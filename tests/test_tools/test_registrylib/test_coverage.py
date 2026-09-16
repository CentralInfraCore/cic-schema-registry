from tools.registrylib.coverage import (
    check_coverage,
    extract_fields,
    extract_yang_fields,
    yang_shape_signature,
)


def _doc(nodes):
    return {
        "spec": {
            "config_surface": {
                "nodes": nodes,
            }
        }
    }


def test_extract_fields_flattens_named_nodes():
    doc = _doc(
        [
            {"name": "bucket_name", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "storage_class", "shape_type": "scalar", "scalar_type": "string"},
        ]
    )
    fields = extract_fields(doc)
    assert set(fields) == {"bucket_name", "storage_class"}


def test_new_field_added_is_fine():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc(
        [
            {"name": "a", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "b", "shape_type": "scalar", "scalar_type": "integer"},
        ]
    )
    result = check_coverage(old, new, major_bump=False)
    assert result.ok


def test_field_silently_dropped_is_a_violation_within_same_major():
    old = _doc(
        [
            {"name": "a", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "b", "shape_type": "scalar", "scalar_type": "integer"},
        ]
    )
    new = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    result = check_coverage(old, new, major_bump=False)
    assert not result.ok
    assert result.violations[0].field == "b"
    assert result.violations[0].kind == "missing"


def test_field_dropped_is_allowed_across_a_major_bump():
    old = _doc(
        [
            {"name": "a", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "b", "shape_type": "scalar", "scalar_type": "integer"},
        ]
    )
    new = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    result = check_coverage(old, new, major_bump=True)
    assert result.ok


def test_field_marked_not_implemented_still_counts_as_present():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc(
        [
            {
                "name": "a",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    result = check_coverage(old, new, major_bump=False)
    assert result.ok


def test_type_mutation_in_place_is_a_violation_within_same_major():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "integer"}])
    result = check_coverage(old, new, major_bump=False)
    assert not result.ok
    assert result.violations[0].kind == "mutated"


def test_type_mutation_allowed_across_major_bump():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "integer"}])
    result = check_coverage(old, new, major_bump=True)
    assert result.ok


def test_description_only_change_is_not_a_mutation():
    old = _doc(
        [
            {
                "name": "a",
                "shape_type": "scalar",
                "scalar_type": "string",
                "description": "old text",
            }
        ]
    )
    new = _doc(
        [
            {
                "name": "a",
                "shape_type": "scalar",
                "scalar_type": "string",
                "description": "much better text",
            }
        ]
    )
    result = check_coverage(old, new, major_bump=False)
    assert result.ok


# ── YANGBlock dialect (#28, #45) ────────────────────────────────────────────


def _yang_doc(config=None, state=None, extends=None):
    spec = {"kind": "YANGBlock"}
    if extends is not None:
        spec["extends"] = extends
    if config is not None:
        spec["config"] = config
    if state is not None:
        spec["state"] = state
    return {"spec": spec}


def test_extract_yang_fields_reads_direct_config_and_state_lists():
    doc = _yang_doc(
        config=[{"name": "mtu", "type": "integer"}],
        state=[{"name": "oper_status", "type": "enum", "values": ["up", "down"]}],
    )
    fields = extract_yang_fields(doc)
    assert set(fields) == {"mtu", "oper_status"}


def test_yang_shape_signature_ignores_value_order():
    a = {"type": "enum", "values": ["up", "down", "unknown"]}
    b = {"type": "enum", "values": ["unknown", "up", "down"]}
    assert yang_shape_signature(a) == yang_shape_signature(b)


def test_yang_shape_signature_same_for_short_and_long_access_form():
    """ "up" and {value: up, conformance: implemented} are the same value,
    per the Access atom's own documented short/long-form equivalence."""
    short_form = {"type": "enum", "values": ["up", "down", "unknown"]}
    long_form = {
        "type": "enum",
        "values": [
            "up",
            "down",
            {"value": "unknown", "conformance": "implemented"},
        ],
    }
    assert yang_shape_signature(short_form) == yang_shape_signature(long_form)


def test_yang_shape_signature_not_implemented_value_still_counts_in_vocabulary():
    """The whole point of #45's fix: marking a value conformance:
    not_implemented instead of deleting it from `values` must NOT look
    like a narrower vocabulary."""
    full = {
        "type": "enum",
        "values": ["up", "down", "testing"],
    }
    narrowed_but_acknowledged = {
        "type": "enum",
        "values": [
            "up",
            "down",
            {"value": "testing", "conformance": "not_implemented"},
        ],
    }
    assert yang_shape_signature(full) == yang_shape_signature(narrowed_but_acknowledged)


def test_yang_shape_signature_differs_when_a_value_is_genuinely_missing():
    full = {"type": "enum", "values": ["up", "down", "testing"]}
    silently_dropped = {"type": "enum", "values": ["up", "down"]}
    assert yang_shape_signature(full) != yang_shape_signature(silently_dropped)


def test_yang_shape_signature_differs_on_type_change():
    a = {"type": "string"}
    b = {"type": "integer"}
    assert yang_shape_signature(a) != yang_shape_signature(b)


def test_yang_shape_signature_differs_on_role_or_required_on_create_change():
    """#82: an inherited key/identity field (role: key, required_on_create:
    true) silently redefined as a non-key optional field, both `type:
    string` with no `values` -- indistinguishable to a type-only
    comparison, but a real semantic change."""
    key_field = {"type": "string", "role": "key", "required_on_create": True}
    display_field = {"type": "string", "required_on_create": False}
    assert yang_shape_signature(key_field) != yang_shape_signature(display_field)


def test_yang_shape_signature_same_for_omitted_and_explicit_false_required_on_create():
    """False-positive found while fixing #82: cic-yang-block-schema
    documents required_on_create's default as false, so a field that
    omits the key and a sibling that explicitly writes `false` are the
    SAME effective shape -- not a mutation. Reproduces the exact
    ietf-interfaces-tunnel.v0.1.4 `statistics` case check_yang_extends
    wrongly flagged before this fix."""
    explicit_false = {"type": "object", "required_on_create": False}
    omitted = {"type": "object"}
    assert yang_shape_signature(explicit_false) == yang_shape_signature(omitted)


def test_check_coverage_yang_dialect_tunnel_narrowing_reproduces_45_then_is_fixed():
    """Reproduces #45 end-to-end: the base's full oper_status enum vs.
    tunnel's silently-truncated one is a violation; the corrected form
    (all 7 values, the missing 4 marked not_implemented) is not."""
    base = _yang_doc(
        state=[
            {
                "name": "oper_status",
                "type": "enum",
                "values": [
                    "up",
                    "down",
                    "testing",
                    "unknown",
                    "dormant",
                    "not_present",
                    "lower_layer_down",
                ],
            }
        ]
    )
    tunnel_before_fix = _yang_doc(
        extends={"name": "ietf-interfaces-base", "version": "v0.0.dev"},
        state=[
            {"name": "oper_status", "type": "enum", "values": ["up", "down", "unknown"]}
        ],
    )
    broken = check_coverage(
        base,
        tunnel_before_fix,
        major_bump=False,
        check_missing=False,
        extract=extract_yang_fields,
        shape=yang_shape_signature,
    )
    assert not broken.ok
    assert broken.violations[0].field == "oper_status"
    assert broken.violations[0].kind == "mutated"

    tunnel_after_fix = _yang_doc(
        extends={"name": "ietf-interfaces-base", "version": "v0.0.dev"},
        state=[
            {
                "name": "oper_status",
                "type": "enum",
                "values": [
                    "up",
                    "down",
                    "unknown",
                    {"value": "testing", "conformance": "not_implemented"},
                    {"value": "dormant", "conformance": "not_implemented"},
                    {"value": "not_present", "conformance": "not_implemented"},
                    {"value": "lower_layer_down", "conformance": "not_implemented"},
                ],
            }
        ],
    )
    fixed = check_coverage(
        base,
        tunnel_after_fix,
        major_bump=False,
        check_missing=False,
        extract=extract_yang_fields,
        shape=yang_shape_signature,
    )
    assert fixed.ok


def test_check_coverage_yang_dialect_does_not_flag_fields_the_child_never_restates():
    """extends is implicit full inheritance (#45): a base field the
    child's own config/state never lists is inherited unchanged, not
    "missing" -- unlike identity.base (check_missing=True default),
    check_missing=False must not flag it."""
    base = _yang_doc(config=[{"name": "name", "type": "string"}])
    child = _yang_doc(extends={"name": "ietf-interfaces-base", "version": "v0.0.dev"})
    result = check_coverage(
        base,
        child,
        major_bump=False,
        check_missing=False,
        extract=extract_yang_fields,
        shape=yang_shape_signature,
    )
    assert result.ok
