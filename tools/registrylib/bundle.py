"""Helpers for reading the one bundle-shaped file left in the registry: the
`cic-primitives` kernel (general/primitives/cic-primitives/). Every other
schema here is one file = one identity; the kernel is versioned and signed
as a single indivisible grammar instead (proposals/schema-registry §3.1 —
its internal types are tightly, structurally coupled via `aggregate_ref`/
`atomic_ref`, so splitting it into per-atom files was tried and reverted).

That does not mean the kernel's internal identities (`ManagedEntity`,
`Identity`, `ConfigSurface`, ...) should be unaddressable. Every migrated
domain composition already writes `identity.base: "cic:core:ManagedEntity"`
(cic-network's network-interface.yaml, cic-primitives' own
kubernetes-pod.yaml, and every domain composition migrated into this
registry) — this module makes that resolvable by pin, by reading straight
into the bundle's `specs[]` list, without ever splitting the file.
"""

from __future__ import annotations

from typing import Any, Iterable

# The two `spec.kind` values a bundle entry can carry — the same values a
# standalone AggregatePrimitive/AtomicPrimitive file would have had, before
# the kernel was consolidated into one bundle.
_KERNEL_KINDS = {"AggregatePrimitive", "AtomicPrimitive"}

# The fixed namespace every kernel-internal type resolves under — matches
# the `base: "cic:core:<Name>"` convention already written (unpinned) by
# every migrated domain composition.
KERNEL_NAMESPACE = "cic:core"


def is_bundle(doc: dict[str, Any]) -> bool:
    """A PrimitiveRelease-shaped file — many identities folded into one
    `specs[]` list, versioned/signed as a single indivisible unit rather
    than per-atom (proposals/schema-registry §3.1)."""
    return doc.get("kind") == "PrimitiveRelease" or "specs" in doc


def iter_kernel_types(
    bundle_doc: dict[str, Any],
) -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield (type_key, unwrapped_doc) for every AggregatePrimitive/
    AtomicPrimitive entry in a bundle's `specs[]`.

    `type_key` is "cic:core:{Name}" — the exact string every domain
    composition's `identity.base` already uses. `unwrapped_doc` is that
    entry's own {metadata, spec} document (specs[i].spec in the bundle),
    in the same shape a standalone schema file would have, so it can be
    fed straight into extract_fields()/check_coverage() — though note most
    kernel types declare their shape via `slots`/`fields`, not the
    config_surface/state_surface/... node-lists those functions look for
    (see registry_validate.check_base_references, which checks for this
    before treating a resolved kernel type as coverage-checkable)."""
    for entry in bundle_doc.get("specs") or []:
        inner = entry.get("spec") if isinstance(entry, dict) else None
        if not isinstance(inner, dict):
            continue
        kind = (inner.get("spec") or {}).get("kind")
        name = (inner.get("metadata") or {}).get("name")
        if kind in _KERNEL_KINDS and name:
            yield f"{KERNEL_NAMESPACE}:{name}", inner


def find_kernel_type(
    bundle_doc: dict[str, Any], type_key: str
) -> dict[str, Any] | None:
    """The unwrapped doc for one specific kernel type_key, or None if the
    bundle has no such entry (e.g. a stale/typo'd pin)."""
    for key, doc in iter_kernel_types(bundle_doc):
        if key == type_key:
            return doc
    return None
