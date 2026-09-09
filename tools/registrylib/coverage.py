"""Field-coverage and version-evolution rules between two versions of the
same schema (proposals/schema-registry §4).

Replaces the git-merge-based inheritance guarantee (cic-primitives D-001,
which only ever applied across repos) with an explicit compiler check,
since a single registry repo has no repo boundary to merge-conflict on.

Rules (same MAJOR version):
  - every field name present in the OLD version must still be present in
    the NEW version — either unchanged, or narrowed to
    `access.conformance: not_implemented` / `deprecated`. A field silently
    disappearing is a hard error.
  - a field present in both versions may not change shape (`shape_type`,
    `scalar_type`, `contract`) in place — that requires a new field name
    (old one deprecated) or a MAJOR bump.

Across a MAJOR version bump, both rules are lifted — removal and in-place
mutation are both allowed.

Known gap (not implemented here): a field name that was removed at a past
MAJOR boundary is supposed to stay reserved forever (never reused with a
different meaning). Checking that needs the *entire* version history of a
schema, not just the adjacent pair this module compares — see
proposals/schema-registry §4's table. Left for a follow-up once the registry
has enough real version history to test against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Every surface's node-list key, and the field-defining sub-key inside a
# schema `spec` that lists individually-named, individually-shaped members.
# Extend this as new surfaces gain node lists (e.g. notification_surface
# already uses `events`, not `nodes` — included below).
_NODE_LIST_KEYS: dict[str, str] = {
    "config_surface": "nodes",
    "state_surface": "nodes",
    "operation_surface": "operations",
    "notification_surface": "events",
}

# Which sub-fields of a node actually define its "shape" for mutation
# purposes. Metadata-only fields (description, default, mandatory/optional
# presence) are deliberately excluded — narrowing presence or adding a
# default is not the kind of change this check guards against; changing the
# underlying data shape or its constraints is.
_SHAPE_KEYS = ("shape_type", "scalar_type", "collection_variant", "contract")

# conformance values that count as "the field is acknowledged, not silently
# dropped" even though it is not fully implemented (D-012).
_ACKNOWLEDGED_CONFORMANCE = {"not_implemented", "deprecated"}


@dataclass
class Violation:
    field: str
    kind: str  # "missing" | "mutated"
    message: str


@dataclass
class CoverageResult:
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.ok


def _spec_of(doc: dict[str, Any]) -> dict[str, Any]:
    return doc.get("spec", {}) or {}


def extract_fields(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Flatten every named node across every known surface into one
    {field_name: node_dict} map. Field names are assumed unique across
    surfaces within one schema — the corpus has never needed the same name
    in two surfaces of the same composition, and allowing it would make
    "field X is missing" ambiguous about which surface it belonged to."""
    spec = _spec_of(doc)
    fields: dict[str, dict[str, Any]] = {}
    for surface_key, list_key in _NODE_LIST_KEYS.items():
        surface = spec.get(surface_key)
        if not isinstance(surface, dict):
            continue
        nodes = surface.get(list_key)
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if isinstance(node, dict) and "name" in node:
                fields[node["name"]] = node
    return fields


def _conformance_of(node: dict[str, Any]) -> str | None:
    access = node.get("access")
    if isinstance(access, dict):
        return access.get("conformance")
    return None


def _shape_signature(node: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(node.get(k) for k in _SHAPE_KEYS)


def check_coverage(
    old_doc: dict[str, Any], new_doc: dict[str, Any], *, major_bump: bool
) -> CoverageResult:
    """Compare an OLD version of a schema against a NEW version (either a
    later version of the same schema, or a derived schema's own declaration
    of its base's fields) and enforce the rules above.

    `major_bump=True` means old_doc.identity.version and new_doc's differ in
    MAJOR — the caller is responsible for determining that from the two
    versions' `spec.identity.version`/filenames; this function only applies
    the resulting policy.
    """
    old_fields = extract_fields(old_doc)
    new_fields = extract_fields(new_doc)
    result = CoverageResult()

    for name, old_node in old_fields.items():
        new_node = new_fields.get(name)
        if new_node is None:
            if not major_bump:
                result.violations.append(
                    Violation(
                        field=name,
                        kind="missing",
                        message=(
                            f"field '{name}' present in the base/prior version is "
                            "absent here — it must appear, at minimum as "
                            "`access.conformance: not_implemented`, unless this is "
                            "a MAJOR version bump"
                        ),
                    )
                )
            continue  # removed at a major bump: allowed, nothing further to check

        if _shape_signature(old_node) != _shape_signature(new_node) and not major_bump:
            result.violations.append(
                Violation(
                    field=name,
                    kind="mutated",
                    message=(
                        f"field '{name}' changed shape/contract in place "
                        f"({_SHAPE_KEYS} differ) without a MAJOR version bump — "
                        "introduce a new field name instead, or deprecate this one"
                    ),
                )
            )

    return result
