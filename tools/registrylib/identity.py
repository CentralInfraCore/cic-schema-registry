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

One type_key can resolve to a schema directory two ways: a normal one
file = one identity schema (read from its `spec.identity`), or one of the
kernel's internal types living inside the cic-primitives bundle's
`specs[]` (see .bundle) — both end up in the same {type_key: schema_dir}
index, and `resolve()` doesn't need to know which kind of directory it got,
since resolve_pin() just lists files in it either way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from .bundle import is_bundle, iter_kernel_types
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


def build_type_index(registry_root: Path) -> dict[str, Path]:
    """{ "namespace:Kind": schema_dir } across the whole tree. Built by
    reading one file per schema directory (the newest by content version —
    identity.namespace/kind do not vary across a schema's own versions, so
    any file works, but the newest is checked first as it's most likely
    to reflect the current shape if a schema were ever renamed).

    A bundle-shaped file (the cic-primitives kernel) indexes differently:
    instead of one `spec.identity`, it declares many types in its
    `specs[]` — every one of those ("cic:core:ManagedEntity",
    "cic:core:Identity", ...) is indexed here too, all pointing at the
    same schema_dir (the bundle file itself is what resolve_pin() will
    find there for any content version pinned against it)."""
    index: dict[str, Path] = {}
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        newest = max(versions)
        doc = yaml.safe_load(newest.path.read_text())
        if is_bundle(doc or {}):
            for type_key, _inner in iter_kernel_types(doc or {}):
                index[type_key] = schema_dir
            continue
        ident = ((doc or {}).get("spec") or {}).get("identity") or {}
        namespace, kind = ident.get("namespace"), ident.get("kind")
        if namespace and kind:
            index[f"{namespace}:{kind}"] = schema_dir
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
