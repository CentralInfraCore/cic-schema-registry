#!/usr/bin/env python3
"""Generates/checks `LATEST.yaml` (tools/registrylib/latest.py) for the
schema directories that have opted in, and guards against the exact
mistake #49 made: editing an already-published `-src<year>.yaml` file in
place instead of adding a new version file.

Two independent checks:

1. LATEST.yaml drift -- does the committed LATEST.yaml match what
   render_latest() produces right now? (Same "generate, then git diff
   --exit-code" pattern `make infra.deps` already uses for
   requirements.txt.)

2. Frozen-file edits -- for every versioned schema file under an enrolled
   directory, does its CURRENT content still match its content at the
   commit that first added it? This is branch-independent on purpose (no
   "--base" to get wrong): it compares each file against its own git
   history, not against a moving branch ref, so a legitimate corrective
   revert (like #51, which restores a file back to its original content)
   passes cleanly, while an in-place edit that changes content and stays
   changed does not. Includes (#92): a file may gain its release
   signature via the sanctioned exception AT MOST ONCE -- a later
   signature SWAP is a real violation, not another "just signing" pass
   -- and an enrolled directory that used to have versioned content and
   now has none is flagged too, whether or not its LATEST.yaml was also
   deleted.

ENROLLED lists which directories this applies to. It started at exactly
one entry (standards/yang/ietf-lldp) on purpose -- see #42/#49/#51 for the
incident this exists to catch, and extend the list one schema at a time
rather than enrolling everything at once.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 -- fixed, local `git` invocations below, no shell, no user-supplied command text.
import sys
from pathlib import Path

import yaml

from .registrylib.latest import render_latest
from .registrylib.paths import list_versions

ENROLLED = [
    "standards/yang/ietf-lldp",
    "standards/yang/cic-yang-block-schema",
    "standards/yang/ietf-interfaces-tunnel",
    "standards/yang/ietf-interfaces-vlan",
    "standards/yang/ietf-interfaces-physical",
    "standards/yang/ietf-nat",
    "standards/yang/ietf-interfaces-l2vlan",
    "standards/yang/cic-switchport-vlan",
    "general/network/dhcp-service",
]


def _latest_path(registry_root: Path, rel: str) -> Path:
    return registry_root / rel / "LATEST.yaml"


def check_drift(registry_root: Path, enrolled: list[str] | None = None) -> list[str]:
    """Dirs whose committed LATEST.yaml doesn't match render_latest()'s
    current output. Returns the list of relative dir paths that drifted.

    #92(b): render_latest() returns None for an empty directory, and a
    missing LATEST.yaml also reads back as None -- so `expected == actual`
    (both None) for a directory that was emptied AND had its LATEST.yaml
    deleted, and no drift is reported. _dir_ever_had_versioned_content
    catches the case check_no_frozen_edits's own (b) fix can't: this
    triggers even in --check mode alone (LATEST.yaml regeneration was
    never reached, because generate_latest.py's main() bails out on
    check_no_frozen_edits first) and even if the caller only ever runs
    check_drift directly."""
    drifted = []
    for rel in ENROLLED if enrolled is None else enrolled:
        expected = render_latest(registry_root / rel)
        latest_path = _latest_path(registry_root, rel)
        actual = latest_path.read_text() if latest_path.exists() else None
        if expected != actual:
            drifted.append(rel)
        elif expected is None and actual is None:
            if _dir_ever_had_versioned_content(registry_root, rel):
                drifted.append(rel)
    return drifted


def write_latest(registry_root: Path, enrolled: list[str] | None = None) -> list[str]:
    """Writes/updates LATEST.yaml for every enrolled dir. Returns the dirs
    actually changed (idempotent -- a second run changes nothing)."""
    changed = []
    for rel in ENROLLED if enrolled is None else enrolled:
        expected = render_latest(registry_root / rel)
        if expected is None:
            continue
        latest_path = _latest_path(registry_root, rel)
        before = latest_path.read_text() if latest_path.exists() else None
        if before != expected:
            latest_path.write_text(expected)
            changed.append(rel)
    return changed


def _first_add_commit(registry_root: Path, path: Path) -> str | None:
    """The oldest commit that added `path` to history (git log is
    newest-first, so the last line is the original add) -- None if git
    can't find one (e.g. the file isn't committed yet).

    Deliberately NOT --follow: this repo's filenames are unique per content
    version by convention (paths.py), so there is no rename to trace, and
    --follow's content-similarity heuristic actively misfires here -- two
    schema files that differ by only a handful of lines (exactly the shape
    of a one-field-corrected v0.1.4 next to its v0.1.3) read as a "rename"
    of one into the other, attributing v0.1.4's add to v0.1.3's original
    commit instead. Measured: with --follow this returned a false positive
    on ietf-lldp.v0.1.4-src2026.yaml the first time this script ran."""
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", str(path)],
        cwd=registry_root,
        capture_output=True,
        text=True,
        timeout=30,
    )  # nosec B603 B607 -- fixed argv, cwd is the registry root, no shell involved.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if result.returncode != 0 or not lines:
        return None
    return lines[-1]


def _file_history_commits(registry_root: Path, path: Path) -> list[str]:
    """Every commit that touched `path`, newest first."""
    result = subprocess.run(
        ["git", "log", "--format=%H", "--", str(path)],
        cwd=registry_root,
        capture_output=True,
        text=True,
        timeout=30,
    )  # nosec B603 B607
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _commit_content(registry_root: Path, commit: str, path: Path) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path.relative_to(registry_root)}"],
        cwd=registry_root,
        capture_output=True,
        text=True,
        timeout=30,
    )  # nosec B603 B607
    if result.returncode != 0:
        return None
    return result.stdout


# Top-level keys a file gains ONLY when it receives its release signature
# (tools/registry_sign.py, proposals/schema-registry §5) -- appended after
# the fact, never touching anything that was already there. This is the
# one sanctioned exception to "never edit a published file": signing a
# file it wasn't wired into `make` when it was first merged (see #60's
# thead) is a real gap, and backfilling it must not read as a repeat of
# #49 -- the whole point is that #49 changed EXISTING content
# (a citation, some origin tags), not that it added trailing keys.
_SIGNATURE_KEYS = ("release", "cic_countersign")


def _only_gained_release_signature(
    registry_root: Path, first_commit: str, path: Path
) -> bool:
    """True if `path`'s current content is its first-committed content,
    BYTE FOR BYTE, with only a release signature appended after it --
    mirroring exactly how tools.registrylib.signing.append_signature_blocks
    writes (original bytes, +1 trailing newline if missing, + signature
    YAML, nothing else touched).

    This is a byte-level prefix check, not a parsed-YAML comparison: an
    earlier version of this function compared parsed dicts (stripping
    _SIGNATURE_KEYS from `current` and comparing to `original`), which
    passes YAML through yaml.safe_load() on both sides -- so a comment or
    pure-formatting change to the surviving content, made alongside a
    legitimate signature addition, would parse identically and slip
    through unnoticed. thead02 flagged this as a real (if unexploited)
    gap. False (the safe default) on any parse error or content mismatch,
    so a malformed file is never silently waved through."""
    result = subprocess.run(
        ["git", "show", f"{first_commit}:{path.relative_to(registry_root)}"],
        cwd=registry_root,
        capture_output=True,
        text=True,
        timeout=30,
    )  # nosec B603 B607
    if result.returncode != 0:
        return False
    original = result.stdout
    if not original.endswith("\n"):
        original += "\n"
    current = path.read_text()
    if not current.startswith(original):
        return False
    appended = current[len(original) :]
    if not appended.strip():
        return False  # nothing actually appended -- not a signing
    try:
        original_data = yaml.safe_load(original) or {}
        appended_data = yaml.safe_load(appended)
    except yaml.YAMLError:
        return False
    if not isinstance(original_data, dict) or not isinstance(appended_data, dict):
        return False
    if not set(appended_data) <= set(_SIGNATURE_KEYS):
        return False
    # The signature keys may only be ADDED, never already present in the
    # original -- a file that already had one and still differs is a real
    # edit, not a first-time signing.
    if any(k in original_data for k in _SIGNATURE_KEYS):
        return False
    return True


def _already_signed_before(registry_root: Path, first_commit: str, path: Path) -> bool:
    """#92(a): True if some commit in `path`'s history -- other than
    `first_commit`, and other than whatever commit's content exactly
    equals `path`'s CURRENT content -- already carried a release/
    cic_countersign block.

    _only_gained_release_signature() on its own only ever compares
    current-vs-first_commit, so it cannot tell a legitimate first-time
    signing apart from a SIGNATURE SWAP: if the file was genuinely signed
    at an intermediate commit and that signature was later replaced (a
    forged countersign, say), both the original unsigned content and the
    replacement signature still satisfy "original bytes + only signature
    keys appended" -- the intermediate, already-signed state is never
    consulted. tools.registrylib.signing.AlreadySignedError's own policy
    is that a file is signed EXACTLY once; this is what actually
    enforces that once frozen-file checking is in the picture.

    Content-equality (not "is this the tip commit") is what distinguishes
    "the commit IS what we're validating" from "prior, distinct history"
    -- this works whether `path`'s current content is itself already
    committed (CI's normal case) or is a not-yet-committed local edit."""
    current = path.read_text()
    for commit in _file_history_commits(registry_root, path):
        if commit == first_commit:
            continue
        content = _commit_content(registry_root, commit, path)
        if content is None or content == current:
            continue  # this commit IS "current" (or unreadable) -- not prior history
        try:
            doc = yaml.safe_load(content) or {}
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and any(k in doc for k in _SIGNATURE_KEYS):
            return True
    return False


_VERSIONED_SCHEMA_FILENAME_RE = re.compile(r"-src\d+\.yaml$")


def _dir_ever_had_versioned_content(registry_root: Path, rel: str) -> bool:
    """#92(b): True if `rel` has EVER contained a tracked, versioned
    schema file (per git history reachable from HEAD) -- used to tell
    "this directory was always/still legitimately empty" apart from
    "this directory used to have content and all of it got deleted",
    which neither check_no_frozen_edits (only iterates files that
    CURRENTLY exist) nor check_drift (an empty dir and a missing
    LATEST.yaml both render as None, so `expected == actual` and no
    drift is reported) can otherwise distinguish."""
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=", "--name-only", "--", rel],
        cwd=registry_root,
        capture_output=True,
        text=True,
        timeout=30,
    )  # nosec B603 B607
    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and _VERSIONED_SCHEMA_FILENAME_RE.search(line):
            return True
    return False


def check_no_frozen_edits(
    registry_root: Path, enrolled: list[str] | None = None
) -> list[str]:
    """Paths (relative to registry_root) of enrolled, versioned schema
    files whose current content no longer matches the content they had
    when first committed -- the actual guard against a repeat of #49.
    Gaining a release signature (_only_gained_release_signature) is the
    one sanctioned exception, but only ONCE (_already_signed_before) --
    everything else is a real violation. Also flags an enrolled
    directory that used to have versioned content and now has none
    (#92(b) -- check_drift alone can't see this: an emptied directory
    and a missing LATEST.yaml both render as None)."""
    problems: list[str] = []
    for rel in ENROLLED if enrolled is None else enrolled:
        schema_dir = registry_root / rel
        versions = list_versions(schema_dir)
        for v in versions:
            first_commit = _first_add_commit(registry_root, v.path)
            if first_commit is None:
                continue
            result = subprocess.run(
                ["git", "diff", "--quiet", first_commit, "--", str(v.path)],
                cwd=registry_root,
                capture_output=True,
                timeout=30,
            )  # nosec B603 B607
            if result.returncode == 1 and (
                not _only_gained_release_signature(registry_root, first_commit, v.path)
                or _already_signed_before(registry_root, first_commit, v.path)
            ):
                problems.append(str(v.path.relative_to(registry_root)))
        if not versions and _dir_ever_had_versioned_content(registry_root, rel):
            problems.append(
                f"{rel} — previously had versioned content, now empty "
                "(directory-emptying is not a sanctioned way to remove a "
                "published schema)"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check_mode = "--check" in argv
    registry_root = Path.cwd()

    frozen = check_no_frozen_edits(registry_root)
    if frozen:
        print(
            "generate_latest: FAILED — an already-published schema file was "
            "modified in place, not left alone:"
        )
        for p in frozen:
            print(f"  - {p}")
        print(
            "  Add a new <name>.vMAJOR.MINOR.PATCH-src<year>.yaml file instead "
            "(proposals/schema-registry §3/§4) — this is exactly what #49 got "
            "wrong and #51 corrected."
        )
        return 1

    if check_mode:
        drifted = check_drift(registry_root)
        if drifted:
            print(
                "generate_latest: FAILED — LATEST.yaml is stale, run "
                "`python -m tools.generate_latest`:"
            )
            for d in drifted:
                print(f"  - {d}/LATEST.yaml")
            return 1
        print(
            f"generate_latest: OK — {len(ENROLLED)} enrolled dir(s), "
            "LATEST.yaml up to date, no frozen-file edits."
        )
        return 0

    changed = write_latest(registry_root)
    if changed:
        print("generate_latest: updated:")
        for c in changed:
            print(f"  - {c}/LATEST.yaml")
    else:
        print(
            f"generate_latest: OK — {len(ENROLLED)} enrolled dir(s), "
            "nothing to update."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
