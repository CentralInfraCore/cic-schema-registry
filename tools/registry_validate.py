#!/usr/bin/env python3
"""CLI entrypoint for the registry-specific checks (proposals/schema-registry).

Four independent checks, all driven purely by walking general/standards/
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

3. extends coverage (#45) — every YANGBlock whose `spec.extends` names a
   parent block must not silently mutate a field it shares with that
   parent (e.g. narrowing an inherited enum). Unlike `identity.base`
   above, `extends` is implicit full inheritance, not explicit
   restatement, so only the "mutated in place" rule applies, not "every
   field must be restated".

4. release signature verification (#102) — presence of a `release:`/
   `cic_countersign:` block is not trust; every file that carries one
   gets its build_hash, author signature, countersign signature, and
   countersign-authority-to-root-certificate chain actually verified
   (tools/registrylib/verify.py), not just checked for existence. A file
   signed under a different tool's envelope (the cic-primitives kernel
   bundle) is reported SKIPPED, not a violation.

This does NOT replace `tools/compiler.py validate` (the inherited, bundle-
oriented meta-schema check) — it is additive, and is not yet wired into
`make validate`. See CLAUDE.md "Jelenlegi, valódi állapot".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from .registrylib.bundle import find_kernel_type
from .registrylib.bundle import is_bundle as _is_bundle
from .registrylib.coverage import (
    check_coverage,
    extract_fields,
    extract_yang_fields,
    yang_shape_signature,
)
from .registrylib.identity import build_type_index, iter_schema_dirs, parse_pin
from .registrylib.paths import list_versions, resolve_pin
from .registrylib.verify import (
    SignatureVerificationError,
    UnsupportedSignatureEnvelopeError,
    verify_release_signature,
)


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


# #94: (schema_dir relative to registry_root, old filename, new filename,
# field name) tuples for already-merged, already-signed version
# transitions that a real recursive deep-diff would otherwise flag as
# false positives. Each is a deliberate, separately-reviewed additive
# change from a prior fix, not an oversight -- verified against the
# corpus's actual version history (git-checked-out full history, not a
# synthetic fixture) before check_coverage(deep=True) was turned on here.
# Anything NOT on this list is a real violation, both retroactively and
# going forward -- this is not a blanket exemption, it is 10 named,
# individually-justified entries.
_DEEP_DIFF_GRANDFATHER: set[tuple[str, str, str, str]] = {
    # #17: must-contract (delete-confirm / resize-only-grows) added to an
    # existing operation's input -- an additive validation tightening,
    # not a shape/contract-breaking change to the input itself.
    (
        "general/compute/compute-resource",
        "compute-resource.v0.2.4-src2026.yaml",
        "compute-resource.v0.2.5-src2026.yaml",
        "terminate",
    ),
    (
        "general/storage/storage-resource",
        "storage-resource.v0.1.3-src2026.yaml",
        "storage-resource.v0.1.4-src2026.yaml",
        "delete",
    ),
    (
        "general/storage/storage-resource",
        "storage-resource.v0.1.3-src2026.yaml",
        "storage-resource.v0.1.4-src2026.yaml",
        "resize",
    ),
    # #18: capability/support-tier marker added to control-plane
    # component fields -- additive metadata, not a shape change.
    (
        "general/kubernetes/kubernetes-cluster",
        "kubernetes-cluster.v0.1.2-src2026.yaml",
        "kubernetes-cluster.v0.1.4-src2026.yaml",
        "api_server",
    ),
    (
        "general/kubernetes/kubernetes-cluster",
        "kubernetes-cluster.v0.1.2-src2026.yaml",
        "kubernetes-cluster.v0.1.4-src2026.yaml",
        "etcd",
    ),
    (
        "general/kubernetes/kubernetes-cluster",
        "kubernetes-cluster.v0.1.2-src2026.yaml",
        "kubernetes-cluster.v0.1.4-src2026.yaml",
        "controller_manager",
    ),
    (
        "general/kubernetes/kubernetes-cluster",
        "kubernetes-cluster.v0.1.2-src2026.yaml",
        "kubernetes-cluster.v0.1.4-src2026.yaml",
        "scheduler",
    ),
    # #99: the fix itself -- PyYAML boolean-coercion bug corrected by
    # quoting True/False as 'True'/'False' in the enum contract.
    (
        "general/kubernetes/kubernetes-node",
        "kubernetes-node.v0.1.4-src2026.yaml",
        "kubernetes-node.v0.1.5-src2026.yaml",
        "conditions",
    ),
    # Pre-#27-era additive fields (an `access` block, and a second
    # `detach` input parameter) from before this check existed.
    (
        "general/storage/storage-resource",
        "storage-resource.v0.1.2-src2026.yaml",
        "storage-resource.v0.1.3-src2026.yaml",
        "attached_to",
    ),
    (
        "general/storage/storage-resource",
        "storage-resource.v0.1.2-src2026.yaml",
        "storage-resource.v0.1.3-src2026.yaml",
        "detach",
    ),
}


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
            result = check_coverage(
                old_doc,
                new_doc,
                major_bump=major_bump,
                deep=True,
                check_new_required=True,
            )
            dir_key = str(schema_dir.relative_to(registry_root))
            for violation in result.violations:
                grandfather_key = (
                    dir_key,
                    old_path.name,
                    new_path.name,
                    violation.field,
                )
                if grandfather_key in _DEEP_DIFF_GRANDFATHER:
                    continue
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


# extends.version (#81) is a bare "vMAJOR.MINOR.PATCH" content-version pin
# -- no "{namespace}:{Kind}@" prefix, since `extends.name` already carries
# the parent's identity as a separate field. Deliberately not parse_pin()
# (registrylib.identity), which expects that combined format.
_EXTENDS_VERSION_RE = re.compile(
    r"^v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
)


def check_yang_extends(registry_root: Path) -> tuple[list[str], list[str]]:
    """Every YANGBlock whose `spec.extends` names a parent block must not
    silently mutate a field it shares with that parent (#45) -- e.g.
    ietf-interfaces-tunnel narrowing the base's 7-value oper_status enum to
    3 values, with nothing ever flagging it.

    Unlike `identity.base` (check_base_references above, DomainComposition,
    proposals/schema-registry §4), `extends` is implicit full inheritance:
    a child's own config/state lists hold only its NEW or OVERRIDDEN
    fields -- everything else is inherited unchanged, so a base field's
    absence from the child's own list is not a removal. Only the
    "mutated in place" rule applies here (check_coverage(...,
    check_missing=False)); the "every field must be restated" rule is
    deliberately not used.

    `extends.version` (#81) is now a real content-version pin, resolved
    with resolve_pin() exactly like `identity.base` (check_base_references
    above) -- a placeholder or non-existent version is a hard problem, not
    a silent fall-through to the base's latest. This closes the gap the
    previous version of this docstring described: "extends.version is a
    placeholder on every block in the corpus today ... this resolves to
    the base's LATEST content version instead" is no longer true for any
    file this function actually examines (it only ever looks at each
    directory's newest version, and #81 fixed every directory's newest
    version to a real pin) -- but is left here as a note in case a future
    LATEST version regresses to an unparseable placeholder, which this
    function will now catch as a problem rather than silently paper over."""
    problems: list[str] = []
    skipped: list[str] = []
    yang_root = registry_root / "standards" / "yang"
    for schema_dir in iter_schema_dirs(registry_root):
        versions = list_versions(schema_dir)
        newest = max(versions)
        doc = _load(newest.path)
        if not _is_yang_block(doc):
            continue
        extends = (doc.get("spec") or {}).get("extends")
        if not isinstance(extends, dict):
            continue  # e.g. ietf-interfaces-base itself: abstract, extends nothing
        base_name = extends.get("name")
        if not base_name:
            problems.append(f"{newest.path}: extends block has no 'name'")
            continue
        base_dir = yang_root / base_name
        base_versions = list_versions(base_dir)
        if not base_versions:
            problems.append(
                f"{newest.path}: extends {base_name!r} — no such YANGBlock "
                f"directory under {yang_root.relative_to(registry_root)}"
            )
            continue
        extends_version = extends.get("version")
        version_match = _EXTENDS_VERSION_RE.match(str(extends_version))
        if not version_match:
            problems.append(
                f"{newest.path}: extends.version {extends_version!r} is not "
                "a real 'vMAJOR.MINOR.PATCH' pin (#81) -- placeholders like "
                "'v0.0.dev' are no longer accepted"
            )
            continue
        base_version = resolve_pin(
            base_dir,
            int(version_match["major"]),
            int(version_match["minor"]),
            int(version_match["patch"]),
        )
        if base_version is None:
            problems.append(
                f"{newest.path}: extends {base_name!r}@{extends_version} "
                "-- no matching content version found"
            )
            continue
        base_doc = _load(base_version.path)
        if not _is_yang_block(base_doc):
            skipped.append(
                f"{newest.path}: extends {base_name!r}, which is not itself "
                "YANGBlock-kind — unexpected shape, skipped rather than "
                "silently comparing 0 fields"
            )
            continue
        result = check_coverage(
            base_doc,
            doc,
            major_bump=False,
            check_missing=False,
            extract=extract_yang_fields,
            shape=yang_shape_signature,
        )
        for violation in result.violations:
            problems.append(
                f"{newest.path} (extends {base_name}@"
                f"{base_version.content_version_str}): {violation.message}"
            )
    return problems, skipped


def check_release_signatures(registry_root: Path) -> tuple[list[str], list[str]]:
    """#102: presence of a `release:`/`cic_countersign:` block is not
    trust -- resolve_pin() (and everything that pins through it: `base`,
    and eventually `reference_target`/`extends`) only checked that a
    content version was LISTED, never that its signature actually
    verifies. This runs tools.registrylib.verify.verify_release_signature
    over every version file in the corpus that carries a `release:`
    block, catching a wrong build_hash, an invalid author or countersign
    signature, or a countersign authority that doesn't actually chain to
    its embedded root certificate.

    Deliberately does NOT require every file to be signed -- a file with
    no `release:` block at all is silently skipped, not flagged. Whether
    everything SHOULD be signed is a separate, already-settled policy
    (this registry's per-file signing model, proposals/schema-registry
    §5); this check only asks "for the files that claim to be signed, is
    that claim actually true", which is exactly what #102 asked for.

    A file signed under a different envelope (general/primitives/
    cic-primitives's kernel bundle, `release.envelope: 2`, from the
    separate cic-primitives/base-repo release pipeline) is reported
    SKIPPED, not a violation -- this check only understands this
    registry's own per-file signing convention."""
    problems: list[str] = []
    skipped: list[str] = []
    for schema_dir in iter_schema_dirs(registry_root):
        for version in list_versions(schema_dir):
            if "release:" not in version.path.read_text():
                continue  # not signed -- not this check's job (see docstring)
            try:
                verify_release_signature(version.path)
            except UnsupportedSignatureEnvelopeError as e:
                skipped.append(str(e))
            except SignatureVerificationError as e:
                problems.append(str(e))
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
    extends_problems, extends_skipped = check_yang_extends(registry_root)
    signature_problems, signature_skipped = check_release_signatures(registry_root)
    problems = (
        evolution_problems + base_problems + extends_problems + signature_problems
    )
    skipped = evolution_skipped + base_skipped + extends_skipped + signature_skipped

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
