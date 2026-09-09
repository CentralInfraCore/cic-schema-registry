#!/usr/bin/env python3
"""CLI entrypoint for the registry-specific checks (proposals/schema-registry).

Two independent checks, both driven purely by walking general/standards/
providers — no committed index:

1. schema evolution — within each schema's own directory, every step from
   one content version to the next (ignoring -src re-signs, which never
   change content) must respect the major-version-gated field rules
   (tools/registrylib/coverage.py).

2. base-chain coverage — every schema whose `spec.identity.base` is an
   exact-version pin must fully account for every field its resolved base
   declares (implemented, or explicitly `not_implemented`/`deprecated`).

This does NOT replace `tools/compiler.py validate` (the inherited, bundle-
oriented meta-schema check) — it is additive, and is not yet wired into
`make validate`. See CLAUDE.md "Jelenlegi, valódi állapot".
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .registrylib.coverage import check_coverage
from .registrylib.identity import build_type_index, iter_schema_dirs, parse_pin
from .registrylib.paths import list_versions


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def check_schema_evolution(registry_root: Path) -> list[str]:
    problems: list[str] = []
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        # Group by content version, keep only the transition between distinct
        # content versions (a re-sign under a new -src year is not a content
        # change and has nothing to check).
        by_content: dict[tuple[int, int, int], Path] = {}
        for v in versions:
            by_content[v.content_version] = v.path  # last (freshest) wins
        ordered = sorted(by_content.items())
        for (old_cv, old_path), (new_cv, new_path) in zip(ordered, ordered[1:]):
            major_bump = old_cv[0] != new_cv[0]
            result = check_coverage(_load(old_path), _load(new_path), major_bump=major_bump)
            for v in result.violations:
                problems.append(
                    f"{schema_dir}: v{'.'.join(map(str, old_cv))} -> "
                    f"v{'.'.join(map(str, new_cv))}: {v.message}"
                )
    return problems


def check_base_references(registry_root: Path) -> list[str]:
    problems: list[str] = []
    type_index = build_type_index(registry_root)
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        newest = max(versions)
        doc = _load(newest.path)
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
        from .registrylib.paths import resolve_pin

        base_version = resolve_pin(base_schema_dir, parsed.major, parsed.minor, parsed.patch)
        if base_version is None:
            problems.append(
                f"{newest.path}: base {base_pin!r} — no matching content version found"
            )
            continue
        base_doc = _load(base_version.path)
        result = check_coverage(base_doc, doc, major_bump=False)
        for v in result.violations:
            problems.append(f"{newest.path} (base {base_pin}): {v.message}")
    return problems


def main() -> int:
    registry_root = Path.cwd()
    problems = check_schema_evolution(registry_root) + check_base_references(registry_root)
    if not problems:
        print("registry_validate: OK — no coverage/evolution violations found.")
        return 0
    print("registry_validate: FAILED")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
