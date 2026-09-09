import yaml

from tools.registry_validate import (
    _is_bundle,
    check_base_references,
    check_schema_evolution,
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
