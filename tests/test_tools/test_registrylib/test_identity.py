import pytest

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


def _write_primitive(path, name, spec_kind):
    """An AggregatePrimitive/AtomicPrimitive-shaped file — no spec.identity
    block, as the real cic-primitives corpus writes them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""---
metadata:
  name: {name}
spec:
  kind: {spec_kind}
""")


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


def test_aggregate_primitive_indexed_under_cic_core(tmp_path):
    """ManagedEntity-shaped files carry no spec.identity block — real
    compositions (cic-network's network-interface.yaml, cic-primitives'
    own kubernetes-pod.yaml) reference them as "cic:core:ManagedEntity"
    regardless, so the index must derive that key itself."""
    schema_dir = tmp_path / "general" / "primitives" / "aggregate" / "managed-entity"
    _write_primitive(
        schema_dir / "managed-entity.v0.2.0-src2026.yaml",
        "ManagedEntity",
        "AggregatePrimitive",
    )

    index = build_type_index(tmp_path)
    assert index["cic:core:ManagedEntity"] == schema_dir

    resolved = resolve("cic:core:ManagedEntity@v0.2.0", tmp_path, index)
    assert resolved.content_version == (0, 2, 0)


def test_atomic_primitive_indexed_under_cic_core(tmp_path):
    schema_dir = tmp_path / "general" / "primitives" / "atomic" / "shape"
    _write_primitive(
        schema_dir / "shape.v0.2.0-src2026.yaml", "Shape", "AtomicPrimitive"
    )

    index = build_type_index(tmp_path)
    assert index["cic:core:Shape"] == schema_dir


def test_domain_composition_identity_takes_precedence_over_primitive_fallback(
    tmp_path,
):
    """A file that DOES declare spec.identity must be keyed by that, never
    by the cic:core fallback — even if its spec.kind happened to collide
    with a primitive kind (defensive; not expected in real content)."""
    schema_dir = tmp_path / "general" / "storage" / "storage-resource"
    _write(
        schema_dir / "storage-resource.v1.0.0-src2026.yaml",
        "cic:storage",
        "StorageResource",
    )
    index = build_type_index(tmp_path)
    assert "cic:core:StorageResource" not in index
    assert index["cic:storage:StorageResource"] == schema_dir
