import copy
import json
from pathlib import Path

import pytest
import yaml

from tools.registrylib import correspondence as cor

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests" / "fixtures" / "vcn-v1"
NS = ROOT / "providers" / "oracle-cloud" / "network" / "network-space"
CORRESPONDENCE = NS / "network-space.correspondence.yaml"
SCHEMA = NS / "network-space.v0.1.0-src2026.yaml"
CASES = sorted(json.loads((FIXTURE / "cases.json").read_text(encoding="utf-8")))


def _json(*parts):
    return json.loads(Path(FIXTURE, *parts).read_text(encoding="utf-8"))


def _text(*parts):
    return Path(FIXTURE, *parts).read_text(encoding="utf-8")


def _emit_config():
    """The registry config fields the fixture's plan compares."""
    plan = _json("plan.json")
    names = {s["path"].lstrip("/") for s in plan["scalars"]}
    return names | {c["path"].lstrip("/") for c in plan["collections"]}


@pytest.fixture(scope="module")
def doc():
    return cor.load(CORRESPONDENCE)


def _apply(doc, case):
    return cor.apply(
        doc,
        _json("cases", case, "expected", "observed.oci.json"),
        _json("cases", case, "intent.registry.json"),
        _emit_config(),
    )


# --- the fixture, stage 4 ---------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_the_correspondence_gives_the_expected_registry_observation(doc, case):
    got = cor.canonical(_apply(doc, case))
    assert got == _text("cases", case, "expected", "observed.registry.json")


def test_there_are_nine_cases_and_each_was_compared():
    assert len(CASES) == 9


def test_a_partial_read_leaves_ipv6_enabled_without_a_value(doc):
    got = _apply(doc, "partial-read")
    assert "ipv6_enabled" not in got["config"]
    assert got["coverage"]["/ipv6_enabled"] == "unobserved"


def test_a_404_and_a_timeout_give_no_value_and_distinct_coverage(doc):
    nf, te = _apply(doc, "not-found"), _apply(doc, "transport-error")
    assert nf["config"] == te["config"] == {}
    assert set(nf["coverage"].values()) == {"unknown"}
    assert set(te["coverage"].values()) == {"unobserved"}


def test_a_mapping_never_improves_the_coverage(doc):
    for case in CASES:
        oci = _json("cases", case, "expected", "observed.oci.json")
        got = _apply(doc, case)
        assert got["coverage"]["/cidr_block"] == oci["coverage"]["/cidrBlocks"]
        assert got["coverage"]["/dns_label"] == oci["coverage"]["/dnsLabel"]
        assert got["coverage"]["/ipv6_enabled"] == oci["coverage"]["/isIpv6Enabled"]


def test_tag_elements_follow_the_keys_of_the_intent(doc):
    got = _apply(doc, "conformant")
    assert sorted(p for p in got["coverage"] if p.startswith("/tags/")) == [
        "/tags/{key=env}/value",
        "/tags/{key=owner}/value",
    ]
    assert got["config"]["tags"] == [
        {"key": "env", "value": "prod"},
        {"key": "owner", "value": "net"},
    ]


def test_tags_are_sorted_by_key_whatever_order_oci_answers_in(doc):
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    oci["effective_config"]["freeformTags"] = {"zeta": "1", "alpha": "2", "mid": "3"}
    got = cor.apply(doc, oci, {}, _emit_config())
    assert [t["key"] for t in got["config"]["tags"]] == ["alpha", "mid", "zeta"]


def test_a_value_map_without_a_default_still_gives_unknown(doc):
    bad = copy.deepcopy(doc)
    for m in bad["spec"]["mappings"]:
        m.pop("default", None)
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    oci["state"]["lifecycleState"] = "NEW_STATE"
    got = cor.apply(bad, oci, {}, _emit_config())
    assert got["state"]["lifecycle_state"] == "unknown"


def test_secondary_cidr_blocks_are_mapped_but_not_emitted_by_fixture_v1(doc):
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    oci["effective_config"]["cidrBlocks"] = ["10.0.0.0/16", "10.1.0.0/16"]
    intent = _json("cases", "conformant", "intent.registry.json")
    plain = cor.apply(doc, oci, intent, _emit_config())
    assert "secondary_cidr_blocks" not in plain["config"]
    more = cor.apply(doc, oci, intent, _emit_config() | {"secondary_cidr_blocks"})
    assert more["config"]["secondary_cidr_blocks"] == ["10.1.0.0/16"]
    assert more["config"]["cidr_block"] == "10.0.0.0/16"


# --- the lifecycle table ----------------------------------------------------------------


def test_the_lifecycle_table_equals_the_fixture_table(doc):
    table = next(
        m for m in doc["spec"]["mappings"] if m["target"] == "state_surface.lifecycle_state"
    )
    fixture = _json("lifecycle-map.json")
    assert table["value_map"] == fixture["map"]
    assert table["default"] == fixture["other"]


def test_an_oci_state_the_table_does_not_know_is_unknown_not_a_guess(doc):
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    oci["state"]["lifecycleState"] = "MIGRATING"
    got = cor.apply(doc, oci, {}, _emit_config())
    assert got["state"]["lifecycle_state"] == "unknown"
    oci["state"]["lifecycleState"] = 7
    assert cor.apply(doc, oci, {}, _emit_config())["state"]["lifecycle_state"] == "unknown"


def test_every_value_of_the_table_is_in_the_schema_enum():
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    node = next(
        n
        for n in schema["spec"]["state_surface"]["nodes"]
        if n["name"] == "lifecycle_state"
    )
    allowed = {
        v
        for c in node["contract"]
        if c["type"] == "enum"
        for v in c["expression"]
    }
    assert allowed == {"pending", "available", "deleting", "deleted", "unknown"}
    table = _json("lifecycle-map.json")
    assert set(table["map"].values()) | {table["other"]} <= allowed


# --- the correspondence against the signed schema ---------------------------------------


def test_the_file_is_well_formed(doc):
    assert cor.check_structure(doc) == []


def test_every_mapped_field_is_in_the_signed_schema(doc):
    schema = cor.schema_fields(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))
    mapped = {m["target"] for m in doc["spec"]["mappings"]}
    assert mapped <= schema, sorted(mapped - schema)


def test_every_schema_config_and_state_field_is_mapped_or_declared_unmapped(doc):
    schema = cor.schema_fields(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))
    mapped = {m["target"] for m in doc["spec"]["mappings"]}
    unmapped = set(doc["spec"]["unmapped_schema_fields"])
    assert schema <= mapped | unmapped, sorted(schema - mapped - unmapped)
    assert unmapped <= schema


def test_a_field_declared_unmapped_has_no_rule(doc):
    unmapped = set(doc["spec"]["unmapped_schema_fields"])
    for m in doc["spec"]["mappings"]:
        if m["target"] in unmapped:
            assert "rule" not in m, m["target"]
        else:
            assert "rule" in m, m["target"]


def test_the_correspondence_names_the_schema_it_belongs_to(doc):
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    ident = schema["spec"]["identity"]
    assert doc["spec"]["canonical"] == "%s:%s@%s" % (
        ident["namespace"],
        ident["kind"],
        ident["version"],
    )
    assert doc["spec"]["provider_resources"] == schema["spec"]["provider_resources"]


def test_the_known_gaps_are_recorded(doc):
    ids = {g["id"] for g in doc["spec"]["gaps"]}
    assert ids == {"lifecycle-updating", "compartment-and-display-name"}
    provider_fields = {f["field"] for f in doc["spec"]["unmapped_provider_fields"]}
    assert {"compartmentId", "displayName", "id", "definedTags"} <= provider_fields


def test_every_oci_field_the_fixture_reports_is_mapped_or_declared(doc):
    """Nothing the OCI answers with is silently dropped."""
    mapped = {
        m["source"]["field"] for m in doc["spec"]["mappings"] if "source" in m
    }
    declared = {f["field"] for f in doc["spec"]["unmapped_provider_fields"]}
    seen = set()
    for case in CASES:
        path = FIXTURE / "cases" / case / "oci" / "response.json"
        if path.exists():
            seen |= set(json.loads(path.read_text(encoding="utf-8")))
    assert seen <= mapped | declared | {"freeformTags"}, sorted(
        seen - mapped - declared
    )


# --- the applier refuses what it cannot do ----------------------------------------------


def test_a_broken_file_is_reported(doc):
    bad = copy.deepcopy(doc)
    bad["spec"]["mappings"][0]["rule"] = "teleport"
    bad["spec"]["mappings"].append(copy.deepcopy(bad["spec"]["mappings"][1]))
    problems = cor.check_structure(bad)
    assert any("unknown rule" in p for p in problems)
    assert any("mapped twice" in p for p in problems)
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(bad, {"effective_config": {}, "state": {}, "coverage": {}}, {}, set())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m.pop("rule"),
        lambda m: m.pop("coverage_from"),
        lambda m: m["source"].update(side="nowhere"),
        lambda m: m.update(target="config_surface"),
    ],
)
def test_each_structural_defect_is_reported(doc, mutate):
    bad = copy.deepcopy(doc)
    mutate(next(m for m in bad["spec"]["mappings"] if m["target"] == "config_surface.dns_label"))
    assert cor.check_structure(bad)


def test_a_value_map_and_a_map_to_list_need_their_arguments(doc):
    bad = copy.deepcopy(doc)
    for m in bad["spec"]["mappings"]:
        m.pop("value_map", None)
        m.pop("key_field", None)
    problems = cor.check_structure(bad)
    assert any("value_map needs a table" in p for p in problems)
    assert any("map_to_list needs" in p for p in problems)


def test_the_observed_input_must_have_its_three_parts(doc):
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(doc, {"effective_config": {}, "state": {}}, {}, set())


def test_a_source_without_coverage_is_refused(doc):
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    del oci["coverage"]["/dnsLabel"]
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(doc, oci, {}, _emit_config())


def test_first_of_nothing_is_refused_not_invented(doc):
    oci = _json("cases", "conformant", "expected", "observed.oci.json")
    oci["effective_config"]["cidrBlocks"] = []
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(doc, oci, {}, _emit_config())
    oci["effective_config"]["cidrBlocks"] = "10.0.0.0/16"
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(doc, oci, {}, _emit_config())
    oci["effective_config"]["cidrBlocks"] = ["10.0.0.0/16"]
    oci["effective_config"]["freeformTags"] = ["not", "a", "map"]
    with pytest.raises(cor.CorrespondenceError):
        cor.apply(doc, oci, {}, _emit_config())


def test_load_refuses_a_file_that_is_not_a_correspondence(tmp_path):
    other = tmp_path / "x.yaml"
    other.write_text("spec:\n  kind: Something\n", encoding="utf-8")
    with pytest.raises(cor.CorrespondenceError):
        cor.load(other)
    other.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(cor.CorrespondenceError):
        cor.load(other)
