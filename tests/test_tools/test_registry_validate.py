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
