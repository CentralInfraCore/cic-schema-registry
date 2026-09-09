import pytest
import yaml

from tools.registrylib.identity import build_type_index, parse_pin, resolve


def _write(path, namespace, kind):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""---
metadata:
  name: {kind}
spec:
  kind: DomainComposition
  identity:
    namespace: "{namespace}"
    kind: {kind}
""")


def _write_bundle(path, entries):
    """entries: list of (name, kind) for AggregatePrimitive/AtomicPrimitive
    specs[] members, matching the real cic-primitives bundle shape."""
    path.parent.mkdir(parents=True, exist_ok=True)
    specs = [
        {
            "id": name.lower(),
            "spec": {"metadata": {"name": name}, "spec": {"kind": kind}},
        }
        for name, kind in entries
    ]
    doc = {"kind": "PrimitiveRelease", "specs": specs}
    path.write_text(yaml.safe_dump(doc, sort_keys=False))


def test_parse_pin_valid():
    p = parse_pin("cic:storage:StorageResource@v1.0.0")
    assert p.namespace == "cic:storage"
    assert p.kind == "StorageResource"
    assert (p.major, p.minor, p.patch) == (1, 0, 0)
    assert p.type_key == "cic:storage:StorageResource"


@pytest.mark.parametrize(
    "bad_pin",
    [
        "cic:storage:StorageResource",  # no version
        "cic:storage:StorageResource@1.0.0",  # missing leading v
        "cic:storage:StorageResource@v1.0.0-src2026",  # -src not allowed in a pin
    ],
)
def test_parse_pin_rejects_unpinned_or_malformed(bad_pin):
    with pytest.raises(ValueError):
        parse_pin(bad_pin)


def test_build_type_index_and_resolve(tmp_path):
    registry_root = tmp_path
    schema_dir = registry_root / "general" / "storage" / "storage-resource"
    _write(
        schema_dir / "storage-resource.v1.0.0-src2026.yaml",
        "cic:storage",
        "StorageResource",
    )
    _write(
        schema_dir / "storage-resource.v1.1.0-src2027.yaml",
        "cic:storage",
        "StorageResource",
    )

    index = build_type_index(registry_root)
    assert index["cic:storage:StorageResource"] == schema_dir

    resolved = resolve("cic:storage:StorageResource@v1.0.0", registry_root, index)
    assert resolved.content_version == (1, 0, 0)
    assert resolved.src_year == 2026


def test_resolve_unknown_type_raises(tmp_path):
    with pytest.raises(KeyError):
        resolve("cic:storage:DoesNotExist@v1.0.0", tmp_path, {})


def test_resolve_known_type_missing_version_raises(tmp_path):
    schema_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        schema_dir / "storage-resource.v1.0.0-src2026.yaml",
        "cic:storage",
        "StorageResource",
    )
    index = build_type_index(tmp_path)
    with pytest.raises(KeyError):
        resolve("cic:storage:StorageResource@v9.9.9", tmp_path, index)


def test_build_type_index_indexes_kernel_types_inside_a_bundle(tmp_path):
    """A bundle file (the cic-primitives kernel) is never itself indexed
    under its own filename identity — its INTERNAL types (ManagedEntity,
    Identity, ...) are, each under "cic:core:{Name}", all pointing at the
    bundle's own schema_dir (proposals/schema-registry §3.1)."""
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write_bundle(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        [("ManagedEntity", "AggregatePrimitive"), ("Identity", "AtomicPrimitive")],
    )

    index = build_type_index(tmp_path)
    assert index["cic:core:ManagedEntity"] == bundle_dir
    assert index["cic:core:Identity"] == bundle_dir


def test_resolve_kernel_type_pin_resolves_to_the_bundle_file(tmp_path):
    bundle_dir = tmp_path / "general" / "primitives" / "cic-primitives"
    _write_bundle(
        bundle_dir / "cic-primitives.v0.2.0-src2026.yaml",
        [("ManagedEntity", "AggregatePrimitive")],
    )
    index = build_type_index(tmp_path)

    resolved = resolve("cic:core:ManagedEntity@v0.2.0", tmp_path, index)
    assert resolved.content_version == (0, 2, 0)
    assert resolved.path == bundle_dir / "cic-primitives.v0.2.0-src2026.yaml"
