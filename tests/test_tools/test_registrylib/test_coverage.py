from tools.registrylib.coverage import check_coverage, extract_fields


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
