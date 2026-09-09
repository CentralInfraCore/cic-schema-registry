from tools.registrylib.bundle import find_kernel_type, is_bundle, iter_kernel_types

_BUNDLE = {
    "kind": "PrimitiveRelease",
    "specs": [
        {
            "id": "managed-entity",
            "spec": {
                "metadata": {"name": "ManagedEntity"},
                "spec": {"kind": "AggregatePrimitive", "slots": {}},
            },
        },
        {
            "id": "identity",
            "spec": {
                "metadata": {"name": "Identity"},
                "spec": {"kind": "AtomicPrimitive", "fields": []},
            },
        },
        # not a kernel type — should be skipped, not raise
        {"id": "not-a-kernel-entry", "spec": {"metadata": {"name": "X"}}},
        # malformed entry — should be skipped, not raise
        {"id": "malformed", "spec": "not-a-dict"},
    ],
}


def test_is_bundle_true_for_specs_shape():
    assert is_bundle(_BUNDLE)
    assert not is_bundle({"spec": {"identity": {}}})
    assert not is_bundle({})


def test_iter_kernel_types_yields_only_aggregate_and_atomic_entries():
    found = dict(iter_kernel_types(_BUNDLE))
    assert set(found.keys()) == {"cic:core:ManagedEntity", "cic:core:Identity"}
    assert found["cic:core:ManagedEntity"]["spec"]["kind"] == "AggregatePrimitive"
    assert found["cic:core:Identity"]["spec"]["kind"] == "AtomicPrimitive"


def test_find_kernel_type_returns_unwrapped_doc():
    doc = find_kernel_type(_BUNDLE, "cic:core:ManagedEntity")
    assert doc is not None
    assert doc["metadata"]["name"] == "ManagedEntity"


def test_find_kernel_type_returns_none_for_unknown_key():
    assert find_kernel_type(_BUNDLE, "cic:core:DoesNotExist") is None


def test_iter_kernel_types_on_empty_specs_yields_nothing():
    assert list(iter_kernel_types({"kind": "PrimitiveRelease", "specs": []})) == []
