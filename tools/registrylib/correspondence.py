"""Loader and applier for a provider correspondence file, for TESTS.

A `kind: ProviderCorrespondence` file (providers/oracle-cloud/network/network-space/
network-space.correspondence.yaml) says how the observed state a provider module reports
(OCI names, with a coverage per path) becomes the observed state in the names of the registry
schema. The decision of #134 stands: the file is a documentation convention, `registry_validate`
and `coverage.py` do not read it, and this module is NOT wired into them. It exists so that the
mapping can be run against the common VCN fixture (tests/fixtures/vcn-v1, stage 4) and so that a
mapping that drifts from the signed schema, or from the fixture, fails a test.

The rule vocabulary is deliberately small:

  direct       the source value as it is
  first        the first element of a list
  rest         the list without its first element
  map_to_list  {k: v} -> [{key_field: k, value_field: v}], sorted by key
  value_map    a string through a table; what the table does not know becomes `default`

Everything is a pure function of its arguments. The coverage of a registry field is the
coverage of its source path, unchanged: a mapping never improves what was observed, and a
source that was not observed gives a field without a value, never a made-up one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

RULES = ("direct", "first", "rest", "map_to_list", "value_map")
SIDES = ("effective_config", "state")
COVERAGE = ("observed", "absent", "unobserved", "unknown")


class CorrespondenceError(ValueError):
    """The correspondence file or the observed input is not in the expected shape."""


def load(path: str | Path) -> dict[str, Any]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("spec", {}).get("kind") != (
        "ProviderCorrespondence"
    ):
        raise CorrespondenceError("%s is not a ProviderCorrespondence" % path)
    return doc


def _target(mapping: dict[str, Any]) -> tuple[str, str]:
    surface, _, name = str(mapping.get("target", "")).partition(".")
    if surface not in ("config_surface", "state_surface") or not name:
        raise CorrespondenceError("bad target %r" % (mapping.get("target"),))
    return surface, name


def check_structure(doc: dict[str, Any]) -> list[str]:
    """Problems with the file itself (not with its fit to a schema); empty if none."""
    problems: list[str] = []
    spec = doc.get("spec", {})
    seen: set[str] = set()
    for m in spec.get("mappings", []):
        try:
            surface, name = _target(m)
        except CorrespondenceError as e:
            problems.append(str(e))
            continue
        if m["target"] in seen:
            problems.append("target %s is mapped twice" % m["target"])
        seen.add(m["target"])
        rule = m.get("rule")
        if rule is None:
            if m.get("kind") not in ("unsupported", "composition", "external-observer"):
                problems.append("%s has no rule and is not unsupported" % name)
            continue
        if rule not in RULES:
            problems.append("%s: unknown rule %r" % (m["target"], rule))
        src = m.get("source", {})
        if src.get("side") not in SIDES or not src.get("field"):
            problems.append("%s: bad source" % m["target"])
        if surface == "config_surface" and not m.get("coverage_from"):
            problems.append("%s: a config field needs coverage_from" % m["target"])
        if rule == "value_map" and not isinstance(m.get("value_map"), dict):
            problems.append("%s: value_map needs a table" % m["target"])
        if rule == "map_to_list" and not (m.get("key_field") and m.get("value_field")):
            problems.append("%s: map_to_list needs key_field and value_field" % name)
    return problems


def _apply_rule(m: dict[str, Any], value: Any) -> Any:
    rule = m["rule"]
    if rule == "direct":
        return value
    if rule in ("first", "rest"):
        if not isinstance(value, list) or not value:
            raise CorrespondenceError(
                "%s: %s of a non-list or empty list" % (m["target"], rule)
            )
        return value[0] if rule == "first" else value[1:]
    if rule == "map_to_list":
        if not isinstance(value, dict):
            raise CorrespondenceError("%s: map_to_list of a non-map" % m["target"])
        return [
            {m["key_field"]: k, m["value_field"]: v} for k, v in sorted(value.items())
        ]
    if rule == "value_map":
        default = m.get("default", "unknown")
        return m["value_map"].get(value, default) if isinstance(value, str) else default
    raise CorrespondenceError("%s: unknown rule %r" % (m["target"], rule))


def apply(
    doc: dict[str, Any],
    observed: dict[str, Any],
    intent: dict[str, Any],
    emit_config: set[str],
) -> dict[str, Any]:
    """The observed state in registry names: {"config", "state", "coverage"}.

    `emit_config` are the registry config fields whose values and coverage are produced (the
    fixture's plan); state fields are produced whenever their source is present. `intent`
    gives the keys of the collections whose elements get a coverage of their own.
    """
    problems = check_structure(doc)
    if problems:
        raise CorrespondenceError("; ".join(problems))
    for k in ("effective_config", "state", "coverage"):
        if not isinstance(observed.get(k), dict):
            raise CorrespondenceError("observed input lacks %r" % k)
    out: dict[str, Any] = {"config": {}, "state": {}, "coverage": {}}
    for m in doc["spec"]["mappings"]:
        if m.get("rule") is None:
            continue
        surface, name = _target(m)
        src = m["source"]
        side = observed[src["side"]]
        if surface == "config_surface":
            if name not in emit_config:
                continue
            cov = observed["coverage"].get(m["coverage_from"])
            if cov not in COVERAGE:
                raise CorrespondenceError(
                    "%s: no coverage for %s" % (m["target"], m["coverage_from"])
                )
            if src["field"] in side:
                out["config"][name] = _apply_rule(m, side[src["field"]])
            els = m.get("coverage_elements")
            if not els:
                out["coverage"]["/" + name] = cov
                continue
            # a collection is observed element by element: the elements the intent
            # names get the coverage of the collection, the collection has none
            for item in intent.get(els["intent_field"], []):
                key = item[els["intent_key"]]
                out["coverage"][els["template"].replace("<key>", str(key))] = cov
        elif src["field"] in side:
            out["state"][name] = _apply_rule(m, side[src["field"]])
    return out


def canonical(doc: Any) -> str:
    """The fixture's file form: sorted keys, two-space indent, one trailing newline."""
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def schema_fields(schema: dict[str, Any]) -> set[str]:
    """`config_surface.X` / `state_surface.X` for every named node of a registry schema."""
    out: set[str] = set()
    spec = schema.get("spec", {})
    for surface in ("config_surface", "state_surface"):
        for node in spec.get(surface, {}).get("nodes", []):
            out.add("%s.%s" % (surface, node["name"]))
    return out
