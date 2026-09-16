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

from collections.abc import Callable
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
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    *,
    major_bump: bool,
    check_missing: bool = True,
    extract: Callable[[dict[str, Any]], dict[str, dict[str, Any]]] = extract_fields,
    shape: Callable[[dict[str, Any]], tuple[Any, ...]] = _shape_signature,
) -> CoverageResult:
    """Compare an OLD version of a schema against a NEW version (either a
    later version of the same schema, or a derived schema's own declaration
    of its base's fields) and enforce the rules above.

    `major_bump=True` means old_doc.identity.version and new_doc's differ in
    MAJOR — the caller is responsible for determining that from the two
    versions' `spec.identity.version`/filenames; this function only applies
    the resulting policy.

    `check_missing=False` turns off the "every old field must still appear"
    rule — needed for `extends` (YANGBlock, #45), whose inheritance model is
    implicit full inheritance (a child's own field list holds only NEW or
    OVERRIDDEN fields; everything else is inherited unchanged, so its
    absence from the child's list is not a removal). `identity.base`
    (DomainComposition, proposals/schema-registry §4) is the opposite —
    explicit full restatement is required there — so its callers keep the
    default `True`.

    `extract`/`shape` are pluggable so the same missing/mutated logic
    serves both field vocabularies (DomainComposition's `shape_type`/
    `scalar_type`/`nodes:`-wrapped surfaces vs. YANGBlock's `type`/
    `item_type`/direct `config`/`state` lists) without duplicating the
    comparison itself — see extract_yang_fields()/yang_shape_signature()
    below.
    """
    old_fields = extract(old_doc)
    new_fields = extract(new_doc)
    result = CoverageResult()

    for name, old_node in old_fields.items():
        new_node = new_fields.get(name)
        if new_node is None:
            if check_missing and not major_bump:
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

        if shape(old_node) != shape(new_node) and not major_bump:
            result.violations.append(
                Violation(
                    field=name,
                    kind="mutated",
                    message=(
                        f"field '{name}' changed shape in place without a MAJOR "
                        "version bump — introduce a new field name instead, or "
                        "explicitly deprecate this one"
                    ),
                )
            )

    return result


# ── YANGBlock dialect (#28, #45) ────────────────────────────────────────────
# spec.config/spec.state as direct lists (no config_surface/state_surface
# nodes: wrapper), fields shaped with `type`/`item_type`/`values`, not
# `shape_type`/`scalar_type`/`collection_variant`/`contract`.

_YANG_LIST_KEYS = ("config", "state")

# The sub-fields that define a YANGBlock field's "shape" for mutation
# purposes, per cic-yang-block-schema's field_schema (standards/yang/
# cic-yang-block-schema): `type` for the base type, `item_type` for list
# element type, `role`/`required_on_create` for key/identity semantics.
# Enum `values` is handled separately, below (_yang_enum_value_names) --
# its vocabulary (the SET of legal values) is what counts as the shape,
# not which of them a given block currently implements; see that
# function's docstring for why a not_implemented value must not read as
# a narrower vocabulary.
#
# role/required_on_create were added after #82: two fields with the same
# `type: string` and no `values` looked identical to a plain type-only
# comparison, even though one was `role: key, required_on_create: true`
# (an interface identity field) and the other `required_on_create: false`
# with no role at all (a display label) -- a real semantic change that
# check_yang_extends should have caught and didn't.
_YANG_SHAPE_KEYS = ("type", "item_type", "role", "required_on_create")


def extract_yang_fields(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """extract_fields()'s counterpart for the YANGBlock dialect — flattens
    spec.config + spec.state's direct lists into {field_name: field_dict}."""
    spec = _spec_of(doc)
    fields: dict[str, dict[str, Any]] = {}
    for key in _YANG_LIST_KEYS:
        nodes = spec.get(key)
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if isinstance(node, dict) and "name" in node:
                fields[node["name"]] = node
    return fields


def _yang_enum_value_names(values: Any) -> tuple[str, ...] | None:
    """Normalizes an enum `values` list to a sorted tuple of bare value
    names, whichever of the Access atom's two equivalent forms each entry
    uses (primitives-group/primitives/schemas/atomic/access.yaml):

        - up                                   # short form
        - value: testing                       # long form
          conformance: not_implemented

    Sorted (order-independent) and conformance-blind on purpose: the SHAPE
    of an enum is the set of values it can legitimately take, not the order
    they're declared in or which ones a given block currently implements.
    A `not_implemented` value is still part of the vocabulary per the
    Access atom's own definition ("field exists... but not on the device")
    — narrowing which values a block IMPLEMENTS is not narrowing the
    vocabulary itself, and must not read as a shape mutation (that's the
    whole reason the not_implemented form exists instead of just deleting
    the value)."""
    if not isinstance(values, list):
        return None
    names = []
    for entry in values:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and "value" in entry:
            names.append(entry["value"])
        else:
            return None  # malformed -- let the raw comparison below catch it
    return tuple(sorted(names))


# Defaults documented in cic-yang-block-schema's field_schema for the
# _YANG_SHAPE_KEYS above -- a field that omits the key means this value,
# per the meta-schema, not "unset"/None. Without this, comparing a field
# that explicitly writes `required_on_create: false` against a sibling
# that just omits the key (same effective meaning, per the meta-schema's
# own documented default) reads as a shape change when it isn't one --
# caught as a false positive on ietf-interfaces-tunnel's `statistics`
# field while fixing #82's real defect (ietf-interfaces-l2vlan's `name`).
# `role` has no documented default (its absence is a real, meaningful
# "no role assigned", not equivalent to any specific role value) so it
# is deliberately not in this map.
_YANG_SHAPE_KEY_DEFAULTS: dict[str, Any] = {"required_on_create": False}


def yang_shape_signature(node: dict[str, Any]) -> tuple[Any, ...]:
    sig = tuple(node.get(k, _YANG_SHAPE_KEY_DEFAULTS.get(k)) for k in _YANG_SHAPE_KEYS)
    values = node.get("values")
    normalized = _yang_enum_value_names(values)
    # normalized is None either for a non-enum field (no `values` at all)
    # or a malformed one the normalizer couldn't parse -- fall back to
    # comparing the raw structure in both cases, so a genuine format error
    # still shows up as a mismatch instead of silently passing.
    value_sig = normalized if normalized is not None else values
    return sig + (value_sig,)
