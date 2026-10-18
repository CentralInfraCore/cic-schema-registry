import yaml

from tools.registrylib.certpattern import (
    ambiguous_flow_lists,
    is_valid_pattern,
    pattern_matches,
)

OLD = "        modify: [OU=adapters, O=cic]"
NEW = '        modify: ["OU=adapters,O=cic"]'


def test_old_unquoted_form_is_two_or_patterns():
    # The defect, shown on the parser itself: two elements, not one pattern.
    assert yaml.safe_load("modify: [OU=adapters, O=cic]")["modify"] == [
        "OU=adapters",
        "O=cic",
    ]
    patterns = yaml.safe_load("modify: [OU=adapters, O=cic]")["modify"]
    assert any(pattern_matches(p, "O=cic") for p in patterns)  # too wide


def test_new_quoted_form_is_one_and_pattern():
    patterns = yaml.safe_load(NEW.strip())["modify"]
    assert patterns == ["OU=adapters,O=cic"]
    assert any(pattern_matches(p, "OU=adapters,O=cic") for p in patterns)
    assert not any(pattern_matches(p, "O=cic") for p in patterns)
    assert not any(pattern_matches(p, "OU=adapters") for p in patterns)
    assert any(pattern_matches(p, "CN=bot,OU=adapters,O=cic") for p in patterns)
    assert not any(pattern_matches(p, "OU=adapters,O=other") for p in patterns)


def test_lint_flags_the_old_form_and_not_the_new_one():
    assert ambiguous_flow_lists(OLD) == [(1, OLD.strip())]
    assert ambiguous_flow_lists(NEW) == []


def test_lint_allows_deliberate_or_lists_and_other_unambiguous_forms():
    assert ambiguous_flow_lists('access: ["O=a", "O=b"]') == []  # quoted OR
    assert ambiguous_flow_lists("access: ['O=a', 'O=b']") == []
    assert ambiguous_flow_lists("access: [O=owner]") == []  # one element
    assert ambiguous_flow_lists("access: []") == []
    assert ambiguous_flow_lists("modify:\n  - O=a\n  - O=b\n") == []  # block list
    assert ambiguous_flow_lists('modify: ["OU=adapters,O=cic"]  # one pattern') == []


def test_lint_flags_a_mixed_list_with_an_unquoted_element():
    assert ambiguous_flow_lists('modify: ["OU=adapters", O=cic]')


def test_lint_flags_comma_inside_quotes_only_once_per_element():
    assert ambiguous_flow_lists('modify: ["A=b,C=d", "E=f"]') == []


def test_pattern_validity():
    assert is_valid_pattern("OU=adapters,O=cic")
    assert is_valid_pattern("CN=*,O=partner-a")
    assert not is_valid_pattern("inherit")
    assert not is_valid_pattern("OU=adapters, O=cic")
    assert not is_valid_pattern(1)
