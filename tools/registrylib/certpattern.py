"""CertPattern list hygiene (security, cic-primitives D-018 / access-policy/1).

A CertPattern is ONE list element: `attr=value` pairs joined by `,` with no
spaces, AND-ed; list elements are OR-ed. YAML flow syntax makes that easy to
get wrong: the unquoted `modify: [OU=adapters, O=cic]` is TWO elements
(`OU=adapters` OR `O=cic`), so any `O=cic` certificate would match, where the
author meant the single pattern `"OU=adapters,O=cic"`.

This module finds the ambiguous spelling in raw text (the parsed value cannot
tell the two apart) and validates the parsed elements. Explicit, quoted
multi-element lists (`["O=a", "O=b"]`, a deliberate OR) and block lists are not
ambiguous and are never flagged.
"""

from __future__ import annotations

import re

_ATTR = r"[A-Za-z][A-Za-z0-9.-]*"
_VAL = r"[^=,\s][^=,]*"
_PAIR = rf"{_ATTR}={_VAL}"
PATTERN_RE = re.compile(rf"^{_PAIR}(,{_PAIR})*$")

# `modify: [..]` / `access: [..]`, optionally as a list item or with a comment.
_FLOW_LINE = re.compile(r"^\s*(?:-\s*)?(access|modify)\s*:\s*\[(.*)\]\s*(?:#.*)?$")


def is_valid_pattern(value: object) -> bool:
    return isinstance(value, str) and PATTERN_RE.match(value) is not None


def pattern_matches(pattern: str, subject: str) -> bool:
    """AND over the pairs of one pattern; `*` in a value is a wildcard."""
    have = [tuple(p.split("=", 1)) for p in subject.split(",")]
    for attr, want in (tuple(p.split("=", 1)) for p in pattern.split(",")):
        rx = re.compile("^" + ".*".join(re.escape(x) for x in want.split("*")) + "$")
        if not any(a == attr and rx.match(v) for a, v in have):
            return False
    return True


def _split_flow(inner: str) -> list[str]:
    """Split a flow sequence body on commas outside quotes."""
    parts: list[str] = []
    cur: list[str] = []
    quote = ""
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch == ",":
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def ambiguous_flow_lists(text: str) -> list[tuple[int, str]]:
    """(line number, line) of every `access`/`modify` flow list that has two or
    more elements of which at least one is unquoted."""
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        m = _FLOW_LINE.match(line)
        if not m:
            continue
        items = _split_flow(m.group(2))
        if len(items) >= 2 and any(i[0] not in "\"'" for i in items):
            found.append((number, line.strip()))
    return found
