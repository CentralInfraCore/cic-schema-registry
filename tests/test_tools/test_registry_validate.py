import yaml

from tools.registry_validate import (
    _is_bundle,
    _is_yang_block,
    _parse_min_schemas,
    check_base_references,
    check_schema_evolution,
    check_yang_extends,
    main,
)


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_is_bundle_detects_primitive_release_shape():
    assert _is_bundle({"kind": "PrimitiveRelease", "specs": []})
    assert _is_bundle({"specs": []})  # kind missing but still bundle-shaped
    assert not _is_bundle({"spec": {"identity": {}}})
    assert not _is_bundle({})


def test_schema_evolution_skips_bundle_shaped_files_instead_of_false_passing(
    tmp_path,
):
    schema_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write(
        schema_dir / "cic-primitives.v0.2.0-src2026.yaml",
        "kind: PrimitiveRelease\nspecs: []\n",
    )
    _write(
        schema_dir / "cic-primitives.v0.2.1-src2027.yaml",
        "kind: PrimitiveRelease\nspecs: []\n",
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert problems == []
    assert len(skipped) == 1
    assert "bundle-shaped" in skipped[0]


def test_is_yang_block_detects_yang_dialect_shape():
    assert _is_yang_block({"spec": {"kind": "YANGBlock", "config": []}})
    assert not _is_yang_block({"spec": {"kind": "DomainComposition"}})
    assert not _is_yang_block({"kind": "YANGBlock"})  # wrong nesting level
    assert not _is_yang_block({})


def test_schema_evolution_skips_yang_block_files_instead_of_false_passing(
    tmp_path,
):
    """Before #28: extract_fields() doesn't know spec.config/spec.state
    (direct lists, no config_surface/state_surface nodes: wrapper), so it
    silently returned {} for both versions here and check_coverage()
    reported a trivially-true "OK" — even though the fixture below actually
    DROPS a field (oper_status) between versions, which the
    DomainComposition dialect would flag as a hard "missing" violation."""
    schema_dir = tmp_path / "standards" / "yang" / "ietf-interfaces-vlan"
    _write(
        schema_dir / "ietf-interfaces-vlan.v0.1.3-src2026.yaml",
        "spec:\n"
        "  kind: YANGBlock\n"
        "  config:\n"
        "    - name: vlan_id\n"
        "      type: vlan-id\n"
        "  state:\n"
        "    - name: oper_status\n"
        "      type: enum\n",
    )
    _write(
        schema_dir / "ietf-interfaces-vlan.v0.1.4-src2026.yaml",
        "spec:\n"
        "  kind: YANGBlock\n"
        "  config:\n"
        "    - name: vlan_id\n"
        "      type: vlan-id\n"
        "  state: []\n",
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert problems == []
    assert len(skipped) == 1
    assert "YANGBlock" in skipped[0]


def test_schema_evolution_catches_a_nested_field_change_deep_true_is_now_wired_in(
    tmp_path,
):
    """#94: check_schema_evolution now calls check_coverage(deep=True) --
    a change inside item_fields, invisible to the old shallow signature,
    must surface as a real problem, not silently pass."""
    schema_dir = tmp_path / "general" / "network" / "dhcp-service"
    _write(
        schema_dir / "dhcp-service.v0.1.0-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: reservations\n"
        "        shape_type: collection\n"
        "        item_fields:\n"
        "          - name: mac_address\n"
        "            scalar_type: string\n",
    )
    _write(
        schema_dir / "dhcp-service.v0.1.1-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: reservations\n"
        "        shape_type: collection\n"
        "        item_fields:\n"
        "          - name: mac_address\n"
        "            scalar_type: integer\n",
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert skipped == []
    assert len(problems) == 1
    assert "reservations" in problems[0]
    assert "item_fields" in problems[0]


def test_schema_evolution_grandfather_list_suppresses_only_the_named_case(
    tmp_path,
):
    """#94's grandfather list is keyed to (dir, old filename, new filename,
    field) exactly -- it must suppress the one real, already-reviewed case
    it names, and NOT suppress a same-shaped nested change on a different
    field in the same transition."""
    schema_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        schema_dir / "storage-resource.v0.1.2-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: attached_to\n"
        "        shape_type: scalar\n"
        "      - name: unrelated_field\n"
        "        shape_type: scalar\n",
    )
    _write(
        schema_dir / "storage-resource.v0.1.3-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: attached_to\n"
        "        shape_type: scalar\n"
        "        access: {conformance: not_implemented}\n"  # grandfathered
        "      - name: unrelated_field\n"
        "        shape_type: scalar\n"
        "        access: {conformance: not_implemented}\n",  # NOT grandfathered
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert skipped == []
    assert len(problems) == 1
    assert "unrelated_field" in problems[0]
    assert "attached_to" not in "".join(problems)


def test_schema_evolution_catches_a_new_required_field_without_major_bump(
    tmp_path,
):
    """#96: check_schema_evolution now calls check_coverage(
    check_new_required=True) -- proposals/schema-registry §4 says a new
    field must be optional within the same major version; this had no
    code-level enforcement before."""
    schema_dir = tmp_path / "general" / "compute" / "compute-resource"
    _write(
        schema_dir / "compute-resource.v0.2.0-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: cpu_count\n"
        "        shape_type: scalar\n",
    )
    _write(
        schema_dir / "compute-resource.v0.2.1-src2026.yaml",
        "spec:\n"
        "  kind: DomainComposition\n"
        "  config_surface:\n"
        "    nodes:\n"
        "      - name: cpu_count\n"
        "        shape_type: scalar\n"
        "      - name: memory_gb\n"
        "        shape_type: scalar\n"
        "        mandatory: true\n",
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert skipped == []
    assert len(problems) == 1
    assert "memory_gb" in problems[0]


def test_schema_evolution_catches_adapter_contract_operations_removed(tmp_path):
    """#95: AdapterContract's spec.operations is now read by
    extract_fields() -- before this, this exact transition compared 0
    fields to 0 fields and reported OK regardless of what happened to
    `operations`."""
    schema_dir = tmp_path / "general" / "network" / "ovs-adapter"
    _write(
        schema_dir / "ovs-adapter.v0.4.1-src2026.yaml",
        "spec:\n"
        "  kind: AdapterContract\n"
        "  operations:\n"
        "    - name: observe\n"
        "    - name: apply\n"
        "    - name: watch\n",
    )
    _write(
        schema_dir / "ovs-adapter.v0.4.2-src2026.yaml",
        "spec:\n"
        "  kind: AdapterContract\n"
        "  operations:\n"
        "    - name: observe\n"
        "    - name: apply\n",
    )

    problems, skipped = check_schema_evolution(tmp_path)
    assert skipped == []
    assert len(problems) == 1
    assert "watch" in problems[0]


def test_base_references_skips_bundle_shaped_files(tmp_path):
    schema_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write(
        schema_dir / "cic-primitives.v0.2.0-src2026.yaml",
        "kind: PrimitiveRelease\nspecs: []\n",
    )

    problems, skipped = check_base_references(tmp_path)
    assert problems == []
    assert len(skipped) == 1
    assert "base-chain coverage not yet implemented" in skipped[0]


def _write_kernel_bundle(path, specs_entries):
    _write(
        path,
        yaml.safe_dump(
            {"kind": "PrimitiveRelease", "specs": specs_entries}, sort_keys=False
        ),
    )


def test_base_references_pinned_into_kernel_slot_type_is_skipped_not_passed(
    tmp_path,
):
    """A domain composition correctly pins into the kernel (base resolves,
    the type is found) — but ManagedEntity declares its shape via `slots`,
    not the surface node-lists extract_fields() understands. This must be
    reported SKIPPED, never silently OK — a silent pass here would be
    exactly the false-confidence failure this checker exists to prevent."""
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write_kernel_bundle(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        [
            {
                "id": "managed-entity",
                "spec": {
                    "metadata": {"name": "ManagedEntity"},
                    "spec": {"kind": "AggregatePrimitive", "slots": {"identity": {}}},
                },
            }
        ],
    )
    domain_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        domain_dir / "storage-resource.v1.0.0-src2026.yaml",
        """---
metadata:
  name: StorageResource
spec:
  identity:
    namespace: "cic:storage"
    kind: StorageResource
    base: "cic:core:ManagedEntity@v0.2.0"
""",
    )
    problems, skipped = check_base_references(tmp_path)
    assert problems == []
    kernel_skips = [s for s in skipped if "storage-resource" in s]
    assert len(kernel_skips) == 1
    assert "cic:core:ManagedEntity" in kernel_skips[0]
    assert "slots/fields" in kernel_skips[0]


def test_base_references_pinned_to_kernel_type_missing_from_that_version_is_skipped(
    tmp_path,
):
    """build_type_index() indexes kernel types from the NEWEST bundle file
    only — so a pin to an OLDER content version whose specs[] didn't yet
    have that type resolves (the type_key IS in the index, from the newer
    file) but then can't find the type in the actual resolved file. Must
    be reported skipped with an actionable reason, never silently treated
    as satisfied and never crash."""
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write_kernel_bundle(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        [
            {
                "id": "other",
                "spec": {
                    "metadata": {"name": "Other"},
                    "spec": {"kind": "AtomicPrimitive"},
                },
            }
        ],
    )
    _write_kernel_bundle(
        bundle_dir / "cic-primitives.v0.3.0-src2026.yaml",
        [
            {
                "id": "managed-entity",
                "spec": {
                    "metadata": {"name": "ManagedEntity"},
                    "spec": {"kind": "AggregatePrimitive", "slots": {}},
                },
            }
        ],
    )
    domain_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        domain_dir / "storage-resource.v1.0.0-src2026.yaml",
        """---
metadata:
  name: StorageResource
spec:
  identity:
    namespace: "cic:storage"
    kind: StorageResource
    base: "cic:core:ManagedEntity@v0.2.0"
""",
    )
    problems, skipped = check_base_references(tmp_path)
    assert problems == []
    kernel_skips = [s for s in skipped if "storage-resource" in s]
    assert len(kernel_skips) == 1
    assert "not found among its specs" in kernel_skips[0]


def test_base_references_pinned_into_kernel_type_with_real_fields_is_checked(
    tmp_path,
):
    """If a kernel type DOES declare surface node-lists (hypothetical, but
    the mechanism must not special-case "kernel" itself — only "has no
    checkable fields"), coverage against it must actually run, not be
    skipped just because it came from a bundle."""
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write_kernel_bundle(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        [
            {
                "id": "has-fields",
                "spec": {
                    "metadata": {"name": "HasFields"},
                    "spec": {
                        "kind": "AtomicPrimitive",
                        "config_surface": {
                            "nodes": [
                                {"name": "required_field", "shape_type": "scalar"}
                            ]
                        },
                    },
                },
            }
        ],
    )
    domain_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        domain_dir / "storage-resource.v1.0.0-src2026.yaml",
        """---
metadata:
  name: StorageResource
spec:
  identity:
    namespace: "cic:storage"
    kind: StorageResource
    base: "cic:core:HasFields@v0.2.0"
""",
    )
    problems, skipped = check_base_references(tmp_path)
    assert not any("storage-resource" in s for s in skipped)
    assert len(problems) == 1
    assert "required_field" in problems[0]
    assert "missing" in problems[0] or "absent" in problems[0]


def test_base_references_mixed_registry_only_flags_the_bundle(tmp_path):
    """A registry containing both the bundle-shaped kernel and an unrelated
    domain composition (with no base of its own): only the bundle is
    reported, and only as skipped — never as a problem, never silently
    treated as an empty/compatible schema."""
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        "kind: PrimitiveRelease\nspecs: []\n",
    )
    domain_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        domain_dir / "storage-resource.v1.0.0-src2026.yaml",
        """---
metadata:
  name: StorageResource
spec:
  identity:
    namespace: "cic:storage"
    kind: StorageResource
""",
    )
    problems, skipped = check_base_references(tmp_path)
    assert problems == []
    assert len(skipped) == 1
    assert "bundle-shaped" in skipped[0]


def test_parse_min_schemas_defaults_to_zero():
    assert _parse_min_schemas([]) == 0
    assert _parse_min_schemas(["--some-other-flag"]) == 0


def test_parse_min_schemas_parses_value():
    assert _parse_min_schemas(["--min-schemas=20"]) == 20


def test_main_fails_on_empty_registry_when_floor_set(tmp_path, monkeypatch, capsys):
    """The exact blind spot this flag exists to close: an empty/broken
    checkout must not silently report "OK — no violations found" just
    because there was nothing to check."""
    monkeypatch.chdir(tmp_path)
    rc = main(["--min-schemas=1"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "scanned 0 schema" in out
    assert "FAILED" in out
    assert "expected at least 1" in out


def test_main_passes_on_empty_registry_when_no_floor_set(tmp_path, monkeypatch):
    """Without --min-schemas, an empty registry is not itself a failure —
    the flag is opt-in, not a hidden default floor."""
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0


def test_main_passes_when_floor_is_met(tmp_path, monkeypatch):
    schema_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        schema_dir / "storage-resource.v1.0.0-src2026.yaml",
        """---
metadata:
  name: StorageResource
spec:
  identity:
    namespace: "cic:storage"
    kind: StorageResource
""",
    )
    monkeypatch.chdir(tmp_path)
    assert main(["--min-schemas=1"]) == 0


# ── check_yang_extends (#45) ─────────────────────────────────────────────────


def _write_yang_block(path, *, extends=None, extends_version="v0.0.dev", state_yaml=""):
    extends_yaml = ""
    if extends is not None:
        extends_yaml = (
            f"  extends:\n    name: {extends}\n    version: {extends_version}\n"
        )
    _write(
        path,
        f"""---
metadata:
  name: {path.stem.split(".")[0]}
spec:
  kind: YANGBlock
{extends_yaml}{state_yaml}
""",
    )


def test_check_yang_extends_flags_a_silently_narrowed_inherited_enum(tmp_path):
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-base"
        / "ietf-interfaces-base.v0.1.3-src2026.yaml",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down, testing, unknown, dormant, not_present, "
            "lower_layer_down]\n"
        ),
    )
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-tunnel"
        / "ietf-interfaces-tunnel.v0.1.3-src2026.yaml",
        extends="ietf-interfaces-base",
        extends_version="v0.1.3",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down, unknown]\n"
        ),
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert len(problems) == 1
    assert "oper_status" in problems[0]
    assert "ietf-interfaces-tunnel" in problems[0]


def test_check_yang_extends_passes_once_values_are_acknowledged_not_implemented(
    tmp_path,
):
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-base"
        / "ietf-interfaces-base.v0.1.3-src2026.yaml",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down, testing, unknown, dormant, not_present, "
            "lower_layer_down]\n"
        ),
    )
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-tunnel"
        / "ietf-interfaces-tunnel.v0.1.4-src2026.yaml",
        extends="ietf-interfaces-base",
        extends_version="v0.1.3",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values:\n"
            "        - up\n"
            "        - down\n"
            "        - unknown\n"
            "        - value: testing\n"
            "          conformance: not_implemented\n"
            "        - value: dormant\n"
            "          conformance: not_implemented\n"
            "        - value: not_present\n"
            "          conformance: not_implemented\n"
            "        - value: lower_layer_down\n"
            "          conformance: not_implemented\n"
        ),
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert problems == []


def test_check_yang_extends_ignores_a_block_that_does_not_extend_anything(tmp_path):
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-base"
        / "ietf-interfaces-base.v0.1.3-src2026.yaml",
        state_yaml="  state:\n    - name: oper_status\n      type: enum\n      values: [up, down]\n",
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert problems == []


def test_check_yang_extends_flags_a_dangling_extends_reference(tmp_path):
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-tunnel"
        / "ietf-interfaces-tunnel.v0.1.3-src2026.yaml",
        extends="no-such-block",
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert len(problems) == 1
    assert "no-such-block" in problems[0]


def test_check_yang_extends_flags_a_placeholder_version_as_a_problem(tmp_path):
    """#81: extends.version is now a real pin -- a placeholder like
    v0.0.dev must be a hard problem, not a silent fall-through to the
    base's latest version."""
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-base"
        / "ietf-interfaces-base.v0.1.3-src2026.yaml",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down]\n"
        ),
    )
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-tunnel"
        / "ietf-interfaces-tunnel.v0.1.3-src2026.yaml",
        extends="ietf-interfaces-base",
        extends_version="v0.0.dev",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down]\n"
        ),
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert len(problems) == 1
    assert "v0.0.dev" in problems[0]
    assert "vMAJOR.MINOR.PATCH" in problems[0]


def test_check_yang_extends_flags_a_pin_to_a_nonexistent_base_version(tmp_path):
    """#81: a well-formed but non-existent content-version pin (e.g. a
    typo, or a base version that was never actually released) must fail
    resolve_pin(), not silently fall back to the base's latest."""
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-base"
        / "ietf-interfaces-base.v0.1.3-src2026.yaml",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down]\n"
        ),
    )
    _write_yang_block(
        tmp_path
        / "standards"
        / "yang"
        / "ietf-interfaces-tunnel"
        / "ietf-interfaces-tunnel.v0.1.3-src2026.yaml",
        extends="ietf-interfaces-base",
        extends_version="v9.9.9",
        state_yaml=(
            "  state:\n"
            "    - name: oper_status\n"
            "      type: enum\n"
            "      values: [up, down]\n"
        ),
    )

    problems, skipped = check_yang_extends(tmp_path)

    assert len(problems) == 1
    assert "v9.9.9" in problems[0]
    assert "no matching content version" in problems[0]
