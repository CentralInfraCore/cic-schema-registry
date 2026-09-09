"""Resolves `identity.base` / `reference_target` strings to files in the
registry tree, by scanning — no committed index file (proposals/schema-
registry §3/§4).

Pin format: "{namespace}:{Kind}@vMAJOR.MINOR.PATCH", e.g.
"cic:storage:StorageResource@v1.0.0". This extends the plain Identity atom
`base` format ("{namespace}:{Kind}", no version — see
cic-primitives/schemas/atomic/identity.yaml) with an explicit, mandatory
version pin, per proposals/schema-registry §4. A `base`/`reference_target`
written without "@vX.Y.Z" is rejected here — every registry-internal
reference must be exact-version-pinned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from .paths import SchemaVersion, list_versions, resolve_pin

_PIN_RE = re.compile(
    r"^(?P<namespace>[a-z0-9]+(?::[a-z0-9-]+)*):(?P<kind>[A-Za-z0-9]+)"
    r"@v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
)

# The three top-level tiers a schema's directory can live under.
REGISTRY_ROOTS = ("general", "standards", "providers")


@dataclass(frozen=True)
class ParsedPin:
    namespace: str
    kind: str
    major: int
    minor: int
    patch: int

    @property
    def type_key(self) -> str:
        return f"{self.namespace}:{self.kind}"


def parse_pin(pin: str) -> ParsedPin:
    m = _PIN_RE.match(pin)
    if not m:
        raise ValueError(
            f"'{pin}' is not a valid registry pin — expected "
            '"{namespace}:{Kind}@vMAJOR.MINOR.PATCH", e.g. '
            '"cic:storage:StorageResource@v1.0.0" (exact version required, '
            "no bare namespace:Kind and no -src<year> suffix)"
        )
    return ParsedPin(
        namespace=m["namespace"],
        kind=m["kind"],
        major=int(m["major"]),
        minor=int(m["minor"]),
        patch=int(m["patch"]),
    )


def iter_schema_dirs(registry_root: Path) -> Iterable[Path]:
    """Every leaf directory under general/standards/providers that actually
    contains at least one parseable schema-version file."""
    for tier in REGISTRY_ROOTS:
        tier_dir = registry_root / tier
        if not tier_dir.is_dir():
            continue
        for path in tier_dir.rglob("*"):
            if path.is_dir() and list_versions(path):
                yield path


# Namespace convention for AggregatePrimitive/AtomicPrimitive files, which
# (unlike DomainCompositions) carry no `spec.identity` block describing
# themselves — their own "identity" is just their metadata.name. Verified
# against the real corpus: every live `identity.base` pointing at ManagedEntity
# writes "cic:core:ManagedEntity" (e.g. cic-network's network-interface.yaml,
# cic-primitives' own kubernetes-pod.yaml) — "cic:core" is that convention,
# not invented here. Only ManagedEntity is actually referenced this way today
# (ConfigSurface/StateSurface/atoms are used via aggregate_ref/atomic_ref file
# paths, not identity pins) — AtomicPrimitive is indexed too for symmetry and
# because nothing prevents a future reference from needing it, but that path
# is currently untested against real content.
_PRIMITIVE_NAMESPACE = "cic:core"
_PRIMITIVE_KINDS = {"AggregatePrimitive", "AtomicPrimitive"}


def build_type_index(registry_root: Path) -> dict[str, Path]:
    """{ "namespace:Kind": schema_dir } across the whole tree. Built by
    reading one file per schema directory (the newest by content version —
    identity.namespace/kind do not vary across a schema's own versions, so
    any file works, but the newest is checked first as it's most likely
    to reflect the current shape if a schema were ever renamed).

    Two ways a schema declares its own type key:
      - DomainComposition-style files: an explicit `spec.identity.namespace`
        + `spec.identity.kind`.
      - AggregatePrimitive/AtomicPrimitive files (general/primitives/*): no
        `spec.identity` block — keyed as "cic:core:{metadata.name}" instead
        (see _PRIMITIVE_NAMESPACE above).
    """
    index: dict[str, Path] = {}
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        newest = max(versions)
        doc = yaml.safe_load(newest.path.read_text()) or {}
        spec = doc.get("spec") or {}
        ident = spec.get("identity") or {}
        namespace, kind = ident.get("namespace"), ident.get("kind")
        if namespace and kind:
            index[f"{namespace}:{kind}"] = schema_dir
            continue
        if spec.get("kind") in _PRIMITIVE_KINDS:
            name = (doc.get("metadata") or {}).get("name")
            if name:
                index[f"{_PRIMITIVE_NAMESPACE}:{name}"] = schema_dir
    return index


def resolve(
    pin: str, registry_root: Path, type_index: dict[str, Path] | None = None
) -> SchemaVersion:
    """Resolve a full pin string to the concrete, freshest-signed
    SchemaVersion file it currently points at. Raises ValueError/KeyError
    with an actionable message on any failure — this is meant to be called
    from a CLI, not silently swallowed."""
    parsed = parse_pin(pin)
    index = type_index if type_index is not None else build_type_index(registry_root)
    schema_dir = index.get(parsed.type_key)
    if schema_dir is None:
        raise KeyError(
            f"no schema in the registry declares identity {parsed.type_key} "
            f"(pin: {pin!r})"
        )
    resolved = resolve_pin(schema_dir, parsed.major, parsed.minor, parsed.patch)
    if resolved is None:
        raise KeyError(
            f"{parsed.type_key} exists in the registry, but no file matches "
            f"content version v{parsed.major}.{parsed.minor}.{parsed.patch} "
            f"(looked in {schema_dir})"
        )
    return resolved
