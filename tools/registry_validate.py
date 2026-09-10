#!/usr/bin/env python3
"""CLI entrypoint for the registry-specific checks (proposals/schema-registry).

Two independent checks, both driven purely by walking general/standards/
providers — no committed index:

1. schema evolution — within each schema's own directory, every step from
   one content version to the next (ignoring -src re-signs, which never
   change content) must respect the major-version-gated field rules
   (tools/registrylib/coverage.py). A YANGBlock-kind file (standards/yang/)
   uses `spec.config`/`spec.state` as direct lists, not the
   DomainComposition dialect's `config_surface`/`state_surface` `nodes:`
   wrapper that extract_fields() understands — running the check anyway
   would silently compare 0 fields against 0 fields and report a
   meaningless "OK", so these transitions are reported SKIPPED instead
   (#28).

2. base-chain coverage — every schema whose `spec.identity.base` is an
   exact-version pin must fully account for every field its resolved base
   declares (implemented, or explicitly `not_implemented`/`deprecated`). A
   base pinned into the cic-primitives kernel bundle resolves through
   registrylib.bundle — but most kernel types (ManagedEntity included)
   declare their shape via `slots`/`fields`, not surface node-lists, so
   coverage against them is reported SKIPPED, not silently passed.

This does NOT replace `tools/compiler.py validate` (the inherited, bundle-
oriented meta-schema check) — it is additive, and is not yet wired into
`make validate`. See CLAUDE.md "Jelenlegi, valódi állapot".
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .registrylib.bundle import find_kernel_type
from .registrylib.bundle import is_bundle as _is_bundle
from .registrylib.coverage import check_coverage, extract_fields
from .registrylib.identity import build_type_index, iter_schema_dirs, parse_pin
from .registrylib.paths import list_versions, resolve_pin


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _is_yang_block(doc: dict) -> bool:
    """A YANGBlock-kind schema (standards/yang/) — `spec.config`/
    `spec.state` are direct lists, not the DomainComposition dialect's
    `config_surface`/`state_surface` `nodes:`-wrapped lists extract_fields()
    knows how to read. extract_fields() silently returns {} for these, so
    without this detector check_coverage() would compare 0 fields to 0
    fields and report a trivially-true "OK" on every version transition —
    the same false-confidence shape as the kernel-bundle case below, just
    not yet flagged (#28)."""
    return ((doc.get("spec") or {}).get("kind")) == "YANGBlock"


def check_schema_evolution(registry_root: Path) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    skipped: list[str] = []
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        # Group by content version, keep only the transition between distinct
        # content versions (a re-sign under a new -src year is not a content
        # change and has nothing to check).
        by_content: dict[tuple[int, int, int], Path] = {}
        for schema_version in versions:
            by_content[schema_version.content_version] = (
                schema_version.path
            )  # last (freshest) wins
        ordered = sorted(by_content.items())
        for (old_cv, old_path), (new_cv, new_path) in zip(ordered, ordered[1:]):
            old_doc, new_doc = _load(old_path), _load(new_path)
            if _is_bundle(old_doc) or _is_bundle(new_doc):
                skipped.append(
                    f"{schema_dir}: v{'.'.join(map(str, old_cv))} -> "
                    f"v{'.'.join(map(str, new_cv))} — bundle-shaped file(s), "
                    "coverage/evolution check not yet implemented for this shape"
                )
                continue
            if _is_yang_block(old_doc) or _is_yang_block(new_doc):
                skipped.append(
                    f"{schema_dir}: v{'.'.join(map(str, old_cv))} -> "
                    f"v{'.'.join(map(str, new_cv))} — YANGBlock-shaped "
                    "file(s) (spec.config/spec.state, not "
                    "config_surface/state_surface), field-coverage/"
                    "evolution check not yet implemented for this dialect (#28)"
                )
                continue
            major_bump = old_cv[0] != new_cv[0]
            result = check_coverage(old_doc, new_doc, major_bump=major_bump)
            for violation in result.violations:
                problems.append(
                    f"{schema_dir}: v{'.'.join(map(str, old_cv))} -> "
                    f"v{'.'.join(map(str, new_cv))}: {violation.message}"
                )
    return problems, skipped


def check_base_references(registry_root: Path) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    skipped: list[str] = []
    type_index = build_type_index(registry_root)
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        newest = max(versions)
        doc = _load(newest.path)
        if _is_bundle(doc):
            skipped.append(
                f"{newest.path}: bundle-shaped file, base-chain coverage not "
                "yet implemented for this shape"
            )
            continue
        identity = ((doc.get("spec") or {}).get("identity")) or {}
        base_pin = identity.get("base")
        if not base_pin or "@v" not in str(base_pin):
            continue  # no base, or an unpinned base — not this check's job
        try:
            parsed = parse_pin(base_pin)
        except ValueError as e:
            problems.append(f"{newest.path}: invalid base pin: {e}")
            continue
        base_schema_dir = type_index.get(parsed.type_key)
        if base_schema_dir is None:
            problems.append(
                f"{newest.path}: base {parsed.type_key!r} not found in registry"
            )
            continue
        base_version = resolve_pin(
            base_schema_dir, parsed.major, parsed.minor, parsed.patch
        )
        if base_version is None:
            problems.append(
                f"{newest.path}: base {base_pin!r} — no matching content version found"
            )
            continue
        base_doc = _load(base_version.path)
        if _is_bundle(base_doc):
            kernel_doc = find_kernel_type(base_doc, parsed.type_key)
            if kernel_doc is None:
                skipped.append(
                    f"{newest.path}: base {base_pin!r} resolves into the "
                    f"kernel bundle, but {parsed.type_key!r} was not found "
                    "among its specs[] entries — check the pin"
                )
                continue
            if not extract_fields(kernel_doc):
                # A real, correctly-resolved kernel type (e.g. ManagedEntity)
                # — but kernel types declare their shape via `slots`/`fields`
                # (schemas/aggregate|atomic/*.yaml), not the
                # config_surface/state_surface/... node-lists extract_fields()
                # looks for. Running check_coverage anyway would silently
                # find 0 fields and report a trivial, meaningless "pass" —
                # exactly the false-confidence failure mode this whole
                # module exists to avoid. Reported as skipped, not OK.
                skipped.append(
                    f"{newest.path}: base {base_pin!r} resolves to kernel "
                    f"type {parsed.type_key!r}, which declares its shape "
                    "via slots/fields, not surface node-lists — base-chain "
                    "coverage against the kernel is not yet implemented"
                )
                continue
            base_doc = kernel_doc
        result = check_coverage(base_doc, doc, major_bump=False)
        for violation in result.violations:
            problems.append(f"{newest.path} (base {base_pin}): {violation.message}")
    return problems, skipped


def _parse_min_schemas(argv: list[str]) -> int:
    """--min-schemas=N — a floor on how many schema directories this run
    must have scanned, so an accidentally-empty or broken checkout (wrong
    cwd, a botched migration, iter_schema_dirs regressing to find nothing)
    fails CI instead of trivially reporting "OK — no violations found"
    over zero schemas. 0 (the default) performs no such check — this is
    opt-in, since library callers (tests, other tooling) have no reason to
    hit it unexpectedly."""
    for arg in argv:
        if arg.startswith("--min-schemas="):
            return int(arg.split("=", 1)[1])
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    min_schemas = _parse_min_schemas(argv)

    registry_root = Path.cwd()
    schema_dirs = list(iter_schema_dirs(registry_root))
    print(
        f"registry_validate: scanned {len(schema_dirs)} schema "
        f"director{'y' if len(schema_dirs) == 1 else 'ies'} under "
        f"general/standards/providers"
    )
    if len(schema_dirs) < min_schemas:
        print(
            f"registry_validate: FAILED — expected at least {min_schemas} "
            f"schema directories, found only {len(schema_dirs)}. This is a "
            "floor, not the real corpus size — either the checkout/cwd is "
            "wrong, or content was genuinely removed (lower --min-schemas "
            "deliberately if so)."
        )
        return 1

    evolution_problems, evolution_skipped = check_schema_evolution(registry_root)
    base_problems, base_skipped = check_base_references(registry_root)
    problems = evolution_problems + base_problems
    skipped = evolution_skipped + base_skipped

    if skipped:
        print("registry_validate: SKIPPED (unsupported shape, not a failure)")
        for s in skipped:
            print(f"  - {s}")

    if not problems:
        print("registry_validate: OK — no coverage/evolution violations found.")
        return 0
    print("registry_validate: FAILED")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
