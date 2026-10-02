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


# ── DomainComposition per-value enum conformance (#137, thead07/thead08) ────
# Ports the YANG dialect's not-implemented-value tolerance (below) to the
# DomainComposition dialect's `contract: type: enum` -- exercised through
# check_coverage() with major_bump=False, the exact check_base_references()
# path an identity.base specialization goes through, since this dialect has
# no direct-signature tests the way yang_shape_signature() does.


def test_contract_enum_short_and_long_form_are_the_same_shape():
    """ "none" and {value: none, conformance: implemented} are the same
    value, per the Access atom's own documented short/long-form
    equivalence (mirrors the YANG-side version of this test)."""
    short_form = _doc(
        [
            {
                "name": "encryption_mode",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {"type": "enum", "expression": ["none", "provider_managed"]}
                ],
            }
        ]
    )
    long_form = _doc(
        [
            {
                "name": "encryption_mode",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            {"value": "none", "conformance": "implemented"},
                            "provider_managed",
                        ],
                    }
                ],
            }
        ]
    )
    result = check_coverage(short_form, long_form, major_bump=False)
    assert result.ok


def test_contract_enum_value_order_does_not_matter():
    a = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b", "c"]}],
            }
        ]
    )
    b = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["c", "a", "b"]}],
            }
        ]
    )
    result = check_coverage(a, b, major_bump=False)
    assert result.ok


def test_contract_enum_not_implemented_value_still_counts_in_vocabulary():
    """The actual #137 fix, reproducing StorageResourceOracleCloud.
    encryption_mode: a specialization marking a value conformance:
    not_implemented instead of removing it from the Contract's
    `expression` must NOT read as narrowing the field's shape -- this is
    what lets check_base_references() (always major_bump=False) accept
    the narrowing without demanding a MAJOR bump the base never took."""
    base = _doc(
        [
            {
                "name": "encryption_mode",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "unspecified",
                            "none",
                            "provider_managed",
                            "customer_managed",
                            "guest_managed",
                        ],
                    }
                ],
            }
        ]
    )
    specialization = _doc(
        [
            {
                "name": "encryption_mode",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "unspecified",
                            {"value": "none", "conformance": "not_implemented"},
                            "provider_managed",
                            "customer_managed",
                            {
                                "value": "guest_managed",
                                "conformance": "not_implemented",
                            },
                        ],
                    }
                ],
            }
        ]
    )
    result = check_coverage(base, specialization, major_bump=False)
    assert result.ok


def test_contract_enum_differs_when_a_value_is_genuinely_missing():
    """Actually shrinking the Contract's value set (not just marking one
    not_implemented) must still be caught -- that would be a Liskov
    substitution violation for a base-typed caller, not a conformance
    narrowing."""
    full = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b", "c"]}],
            }
        ]
    )
    silently_narrowed = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b"]}],
            }
        ]
    )
    result = check_coverage(full, silently_narrowed, major_bump=False)
    assert not result.ok
    assert result.violations[0].kind == "mutated"


def test_contract_enum_survives_heterogeneous_value_types():
    """A scalar_type-inconsistent enum (mixed int/str values -- already a
    bug one layer down, but not this function's to catch) must not crash
    check_coverage(): plain sorted() raises TypeError on an int/str mix.
    _sorted_enum_value_names()'s type-qualified fallback keeps the
    comparison deterministic instead."""
    doc = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", 1, "b"]}],
            }
        ]
    )
    result = check_coverage(doc, doc, major_bump=False)
    assert result.ok


def test_non_enum_contract_types_are_unaffected_by_enum_normalization():
    """A range/must/pattern contract must still compare as a real
    mutation when changed -- the enum-specific normalization must not
    accidentally blind the check to other contract types."""
    old = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "integer",
                "contract": [{"type": "range", "expression": "1..10"}],
            }
        ]
    )
    new = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "integer",
                "contract": [{"type": "range", "expression": "1..99"}],
            }
        ]
    )
    result = check_coverage(old, new, major_bump=False)
    assert not result.ok
    assert result.violations[0].kind == "mutated"


# ── Conformance direction (cic-primitives D-017, cic-schema-registry#160) ───
# D-017's one normative derivation direction: implemented/bare ->
# not_implemented is allowed (narrowing); the reverse (un-narrowing) is not.
# `deprecated` is deliberately excluded -- no corpus evidence it's even
# monotonic, so it must never trigger these checks on either side.


def test_contract_enum_value_narrowed_to_not_implemented_is_allowed():
    """The positive case, mirroring StorageResourceOracleCloud.encryption_mode
    exactly: a value moving from bare to not_implemented is the one
    direction D-017 proves. Already covered by
    test_contract_enum_not_implemented_value_still_counts_in_vocabulary for
    the vocabulary side; this asserts it explicitly as the conformance-
    direction positive fixture too."""
    base = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b", "c"]}],
            }
        ]
    )
    specialization = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "not_implemented"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    result = check_coverage(base, specialization, major_bump=False)
    assert result.ok


def test_contract_enum_value_widened_from_not_implemented_is_rejected():
    """The negative case D-017 identified as missing: a descendant
    silently reversing an inherited not_implemented value back to usable
    is caught, even though the plain vocabulary-name comparison
    (_dc_enum_value_names) sees no difference at all between the two
    sides -- both reduce to the same ('a', 'b', 'c') tuple."""
    base = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "not_implemented"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    widened_to_bare = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b", "c"]}],
            }
        ]
    )
    result = check_coverage(base, widened_to_bare, major_bump=False)
    assert not result.ok
    assert result.violations[0].kind == "conformance_widened"

    widened_to_implemented = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "implemented"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    result2 = check_coverage(base, widened_to_implemented, major_bump=False)
    assert not result2.ok
    assert result2.violations[0].kind == "conformance_widened"


def test_contract_enum_deprecated_transitions_are_never_checked():
    """deprecated is explicitly out of scope for D-017 -- neither
    not_implemented -> deprecated nor deprecated -> anything triggers a
    conformance_widened violation. This is the corpus's own real shape:
    StorageResourceOracleCloud.attached_to inherits `conformance:
    deprecated` from the base unchanged; nothing here narrows via
    deprecated."""
    base = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "not_implemented"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    to_deprecated = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "deprecated"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    # Not asserted "ok" -- vocabulary is unchanged either way, but this
    # specific function's job is only to confirm no conformance_widened
    # violation fires for a transition into/out of deprecated.
    result = check_coverage(base, to_deprecated, major_bump=False)
    assert not any(v.kind == "conformance_widened" for v in result.violations)

    already_deprecated = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [
                    {
                        "type": "enum",
                        "expression": [
                            "a",
                            {"value": "b", "conformance": "deprecated"},
                            "c",
                        ],
                    }
                ],
            }
        ]
    )
    widened_from_deprecated = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "contract": [{"type": "enum", "expression": ["a", "b", "c"]}],
            }
        ]
    )
    result2 = check_coverage(
        already_deprecated, widened_from_deprecated, major_bump=False
    )
    assert not any(v.kind == "conformance_widened" for v in result2.violations)


def test_access_conformance_field_narrowed_to_not_implemented_is_allowed():
    """The positive case, mirroring StorageResourceOracleCloud.filesystem
    and NetworkSpaceOracleCloud.dns_support_enabled/dns_hostnames_enabled:
    a whole field gaining access.conformance: not_implemented that it
    didn't carry in the base."""
    base = _doc(
        [{"name": "filesystem", "shape_type": "scalar", "scalar_type": "string"}]
    )
    specialization = _doc(
        [
            {
                "name": "filesystem",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    result = check_coverage(base, specialization, major_bump=False)
    assert result.ok


def test_access_conformance_field_widened_from_not_implemented_is_rejected():
    """The negative case D-017 identified as the real, unenforced gap:
    access isn't in _SHAPE_KEYS at all, so before this check existed,
    check_coverage() was completely blind to a descendant silently
    dropping an inherited access.conformance: not_implemented -- falsely
    claiming a capability the base said didn't exist."""
    base = _doc(
        [
            {
                "name": "filesystem",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    widened_to_absent = _doc(
        [{"name": "filesystem", "shape_type": "scalar", "scalar_type": "string"}]
    )
    result = check_coverage(base, widened_to_absent, major_bump=False)
    assert not result.ok
    assert result.violations[0].kind == "conformance_widened"

    widened_to_implemented = _doc(
        [
            {
                "name": "filesystem",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "implemented"},
            }
        ]
    )
    result2 = check_coverage(base, widened_to_implemented, major_bump=False)
    assert not result2.ok
    assert result2.violations[0].kind == "conformance_widened"


def test_access_conformance_deprecated_transitions_are_never_checked():
    """Same deprecated-is-out-of-scope rule as the contract.enum case,
    applied to whole-field access.conformance."""
    base = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    to_deprecated = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "deprecated"},
            }
        ]
    )
    result = check_coverage(base, to_deprecated, major_bump=False)
    assert not any(v.kind == "conformance_widened" for v in result.violations)


def test_access_conformance_unchanged_not_implemented_is_fine():
    """A field that stays not_implemented on both sides is unchanged, not
    a narrowing or a widening -- must not fire."""
    base = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    same = _doc(
        [
            {
                "name": "x",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    result = check_coverage(base, same, major_bump=False)
    assert result.ok


def test_conformance_direction_lifted_across_major_bump():
    """Consistent with every other coverage rule: a MAJOR bump lifts the
    conformance-direction check too, same as vocabulary/field removal."""
    base = _doc(
        [
            {
                "name": "filesystem",
                "shape_type": "scalar",
                "scalar_type": "string",
                "access": {"conformance": "not_implemented"},
            }
        ]
    )
    widened = _doc(
        [{"name": "filesystem", "shape_type": "scalar", "scalar_type": "string"}]
    )
    result = check_coverage(base, widened, major_bump=True)
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


# ── #80/#94/#95/#96: deep comparison, surface tracking, AdapterContract,
# new-required-field detection ───────────────────────────────────────────


def _state_doc(nodes):
    return {"spec": {"state_surface": {"nodes": nodes}}}


def _adapter_doc(operations):
    return {"spec": {"kind": "AdapterContract", "operations": operations}}


def test_extract_fields_tags_each_node_with_its_surface():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    fields = extract_fields(old)
    assert fields["a"]["_surface"] == "config_surface"


def test_deep_true_flags_a_field_moved_between_surfaces_without_major_bump():
    """#80: config_surface -> state_surface is a real compatibility change
    (a writable field becomes read-only) that the shallow shape_type/
    scalar_type/collection_variant/contract signature alone can't see,
    because none of those keys change — only which surface the field
    lives in does."""
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _state_doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    shallow = check_coverage(old, new, major_bump=False)
    assert shallow.ok  # the blind spot: shallow signature sees no change

    deep = check_coverage(old, new, major_bump=False, deep=True)
    assert not deep.ok
    assert deep.violations[0].field == "a"
    assert deep.violations[0].kind == "mutated"
    assert "_surface" in deep.violations[0].message


def test_deep_true_flags_a_nested_item_fields_change_the_shallow_check_misses():
    """#94: an inner item_fields entry's scalar_type changes while the
    outer field's own top-level shape keys stay identical."""
    old = _doc(
        [
            {
                "name": "reservations",
                "shape_type": "collection",
                "item_fields": [{"name": "mac_address", "scalar_type": "string"}],
            }
        ]
    )
    new = _doc(
        [
            {
                "name": "reservations",
                "shape_type": "collection",
                "item_fields": [{"name": "mac_address", "scalar_type": "integer"}],
            }
        ]
    )
    shallow = check_coverage(old, new, major_bump=False)
    assert shallow.ok  # the blind spot #94 reports

    deep = check_coverage(old, new, major_bump=False, deep=True)
    assert not deep.ok
    assert "item_fields[0].scalar_type" in deep.violations[0].message


def test_deep_true_flags_operation_input_removed():
    """#94: an operation's input list shrinking is a real breaking change
    even though the operation node's own top-level keys don't change."""
    old = _doc(
        [
            {
                "name": "reset_pool",
                "shape_type": "scalar",
                "input": [{"name": "confirm", "scalar_type": "boolean"}],
            }
        ]
    )
    new = _doc([{"name": "reset_pool", "shape_type": "scalar", "input": []}])
    deep = check_coverage(old, new, major_bump=False, deep=True)
    assert not deep.ok
    assert "input" in deep.violations[0].message


def test_deep_true_description_only_change_still_not_a_mutation():
    old = _doc([{"name": "a", "shape_type": "scalar", "description": "old"}])
    new = _doc([{"name": "a", "shape_type": "scalar", "description": "new, better"}])
    assert check_coverage(old, new, major_bump=False, deep=True).ok


def test_deep_true_atomic_ref_format_change_still_not_a_mutation():
    """cic-schema-registry#125: atomic_ref/aggregate_ref name WHICH shared
    kernel primitive backs a field's category (determined by where the
    field sits, e.g. every config/state node uses shape.yaml) -- never
    the individual field's own type, which scalar_type/shape_type/
    contract already fully capture. Rewriting the reference's string
    format (schemas/atomic/<name>.yaml -> the working
    cic:core:<Name>@v0.2.0 pin) must not by itself force a MAJOR bump."""
    old = _doc(
        [
            {
                "name": "a",
                "shape_type": "scalar",
                "atomic_ref": "schemas/atomic/shape.yaml",
            }
        ]
    )
    new = _doc(
        [{"name": "a", "shape_type": "scalar", "atomic_ref": "cic:core:Shape@v0.2.0"}]
    )
    assert check_coverage(old, new, major_bump=False, deep=True).ok


def test_deep_true_allowed_across_major_bump():
    old = _doc([{"name": "a", "shape_type": "collection", "item_fields": [{"x": 1}]}])
    new = _doc([{"name": "a", "shape_type": "collection", "item_fields": [{"x": 2}]}])
    assert check_coverage(old, new, major_bump=True, deep=True).ok


def test_extract_fields_reads_adapter_contract_operations_directly():
    """#95: AdapterContract stores operations at spec.operations, not
    spec.operation_surface.operations -- before this, extract_fields()
    returned {} for every AdapterContract file."""
    doc = _adapter_doc([{"name": "observe", "input": []}, {"name": "apply"}])
    fields = extract_fields(doc)
    assert set(fields) == {"observe", "apply"}
    assert fields["observe"]["_surface"] == "operations"


def test_adapter_contract_operations_change_is_caught_with_deep_true():
    """Before #95: this transition compared 0 fields to 0 fields and
    reported a trivially-true OK no matter what happened to `operations`
    -- reproducing exactly the ovs-adapter/switch-netconf-adapter blind
    spot the issue described, with a real removed operation."""
    old = _adapter_doc([{"name": "observe"}, {"name": "apply"}, {"name": "watch"}])
    new = _adapter_doc([{"name": "observe"}, {"name": "apply"}])
    result = check_coverage(old, new, major_bump=False, deep=True)
    assert not result.ok
    assert result.violations[0].field == "watch"
    assert result.violations[0].kind == "missing"


def test_adapter_contract_operations_unchanged_is_fine():
    old = _adapter_doc([{"name": "observe", "input": [{"name": "id"}]}])
    new = _adapter_doc([{"name": "observe", "input": [{"name": "id"}]}])
    assert check_coverage(old, new, major_bump=False, deep=True).ok


def test_check_new_required_flags_a_new_mandatory_field_without_major_bump():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc(
        [
            {"name": "a", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "b", "shape_type": "scalar", "mandatory": True},
        ]
    )
    result = check_coverage(old, new, major_bump=False, check_new_required=True)
    assert not result.ok
    assert result.violations[0].field == "b"
    assert result.violations[0].kind == "new_required"


def test_check_new_required_ignores_a_required_on_create_field_too():
    old = _doc([])
    new = _doc([{"name": "b", "shape_type": "scalar", "required_on_create": True}])
    result = check_coverage(old, new, major_bump=False, check_new_required=True)
    assert not result.ok
    assert result.violations[0].kind == "new_required"


def test_check_new_required_allows_a_new_optional_field():
    old = _doc([{"name": "a", "shape_type": "scalar", "scalar_type": "string"}])
    new = _doc(
        [
            {"name": "a", "shape_type": "scalar", "scalar_type": "string"},
            {"name": "b", "shape_type": "scalar", "mandatory": False},
        ]
    )
    result = check_coverage(old, new, major_bump=False, check_new_required=True)
    assert result.ok


def test_check_new_required_allowed_across_major_bump():
    old = _doc([])
    new = _doc([{"name": "b", "shape_type": "scalar", "mandatory": True}])
    result = check_coverage(old, new, major_bump=True, check_new_required=True)
    assert result.ok


def test_check_new_required_off_by_default_does_not_flag_it():
    """check_base_references/check_yang_extends compare a base/parent
    against a derived/child that is EXPECTED to declare additional
    fields -- check_new_required must default False so those callers'
    existing behavior is unaffected."""
    old = _doc([])
    new = _doc([{"name": "b", "shape_type": "scalar", "mandatory": True}])
    result = check_coverage(old, new, major_bump=False)
    assert result.ok
