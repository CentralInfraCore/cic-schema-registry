import subprocess

from tools.generate_latest import (
    check_drift,
    check_no_frozen_edits,
    write_latest,
)
from tools.registrylib.latest import render_latest


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _git(*args, cwd):
    subprocess.run(  # noqa: S603 -- fixed argv, test-only, temp git repo
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "PATH": "/usr/bin:/bin",
        },
    )


def _init_repo(tmp_path):
    _git("init", "-q", "-b", "main", cwd=tmp_path)


# ---- render_latest() -- no git needed ----


def test_render_latest_none_for_empty_dir(tmp_path):
    assert render_latest(tmp_path / "nothing-here") is None


def test_render_latest_picks_highest_content_version(tmp_path):
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    _write(schema_dir / "ietf-lldp.v0.1.4-src2026.yaml", "a: 2\n")

    text = render_latest(schema_dir)

    assert "current:" in text
    assert "version: v0.1.4" in text
    assert "file: ietf-lldp.v0.1.4-src2026.yaml" in text
    # both versions still listed, not just the current one
    assert "ietf-lldp.v0.1.3-src2026.yaml" in text
    assert "ietf-lldp.v0.1.4-src2026.yaml" in text


def test_render_latest_dedupes_by_content_version_freshest_src_year_wins(tmp_path):
    """Two files differing only by -src year (a re-sign, not a content
    change) collapse to ONE entry in all_versions -- mirrors
    registry_validate.check_schema_evolution's own "last (freshest) wins"
    grouping (tools/registrylib/paths.py list_versions ordering)."""
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    _write(schema_dir / "ietf-lldp.v0.1.3-src2027.yaml", "a: 1\n")

    text = render_latest(schema_dir)

    # one list bullet in all_versions, not two -- a re-sign is not a
    # second content version
    assert text.count("  - version:") == 1
    assert "ietf-lldp.v0.1.3-src2027.yaml" in text
    assert "ietf-lldp.v0.1.3-src2026.yaml" not in text


# ---- check_drift() / write_latest() ----


def test_write_latest_creates_file_then_check_drift_is_clean(tmp_path):
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")

    changed = write_latest(tmp_path, enrolled=["ietf-lldp"])
    assert changed == ["ietf-lldp"]
    assert (schema_dir / "LATEST.yaml").exists()

    # idempotent: nothing left to change, and check_drift agrees
    assert write_latest(tmp_path, enrolled=["ietf-lldp"]) == []
    assert check_drift(tmp_path, enrolled=["ietf-lldp"]) == []


def test_check_drift_flags_a_hand_edited_latest_yaml(tmp_path):
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    write_latest(tmp_path, enrolled=["ietf-lldp"])

    _write(schema_dir / "LATEST.yaml", "someone hand-edited this\n")

    assert check_drift(tmp_path, enrolled=["ietf-lldp"]) == ["ietf-lldp"]


def test_check_drift_flags_a_missing_new_version_not_yet_regenerated(tmp_path):
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    write_latest(tmp_path, enrolled=["ietf-lldp"])

    # a new content version lands, but nobody re-ran the generator yet
    _write(schema_dir / "ietf-lldp.v0.1.4-src2026.yaml", "a: 2\n")

    assert check_drift(tmp_path, enrolled=["ietf-lldp"]) == ["ietf-lldp"]


# ---- check_no_frozen_edits() -- the actual #49 guard, needs real git history ----


def test_frozen_edits_clean_when_nothing_touched_after_commit(tmp_path):
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"]) == []


def test_frozen_edits_flags_an_in_place_edit_of_a_published_file(tmp_path):
    """This IS #49: edit an already-committed -src<year>.yaml file instead
    of adding a new version. Reproduced end-to-end with a real git repo,
    not mocked, because the whole point of this check is what real git
    history says."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "source: RFC 8516\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)

    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "source: IEEE 802.1ABcu\n")

    problems = check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"])
    assert problems == ["ietf-lldp/ietf-lldp.v0.1.3-src2026.yaml"]


def test_frozen_edits_clean_after_a_correcting_revert(tmp_path):
    """This is #51: the fix isn't "undo the commit", it's "add a new
    version file and put the original content back in the old one" -- and
    THAT must read as clean again, not as a second violation. Reproduces
    the exact restore-then-recommit shape #51 used."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    original = "source: RFC 8516\n"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", original)
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)

    # #49: bad in-place edit, committed
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "source: WRONG\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "bad in-place edit (#49)", cwd=tmp_path)
    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"]) == [
        "ietf-lldp/ietf-lldp.v0.1.3-src2026.yaml"
    ]

    # #51: restore v0.1.3 exactly, add the fix as a new v0.1.4 instead
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", original)
    _write(schema_dir / "ietf-lldp.v0.1.4-src2026.yaml", "source: IEEE 802.1ABcu\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "correction (#51)", cwd=tmp_path)

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"]) == []


def test_frozen_edits_ignores_files_outside_enrolled_dirs(tmp_path):
    _init_repo(tmp_path)
    other_dir = tmp_path / "ietf-ip-v4"
    _write(other_dir / "ietf-ip-v4.v0.1.3-src2026.yaml", "a: 1\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add unrelated schema", cwd=tmp_path)

    _write(other_dir / "ietf-ip-v4.v0.1.3-src2026.yaml", "a: 2\n")

    # not enrolled -> not checked, even though it was edited in place
    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"]) == []


# ── gaining a release signature (tools/registry_sign.py, proposals/
# schema-registry §5) is the one sanctioned exception to "never edit a
# published file" -- born directly from signing ietf-nat AFTER #52 had
# already enrolled it, which the checker (correctly, before this fix)
# treated as a repeat of #49. ────────────────────────────────────────────


def test_frozen_edits_clean_when_a_file_only_gains_a_release_signature(tmp_path):
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    # registry_sign.py's append_signature_blocks() -- appends release:/
    # cic_countersign: at the top level, touches nothing else.
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n  sign: vault:v1:...\n"
        "cic_countersign:\n  sign: vault:v1:...\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == []


def test_frozen_edits_still_flags_a_real_edit_disguised_next_to_a_signature(tmp_path):
    """The exception is narrow: adding release:/cic_countersign: AND
    changing something else at the same time must still be caught."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\n  source: RFC 8512\nspec:\n  kind: YANGBlock\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\n  source: WRONG CITATION\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat/ietf-nat.v0.1.0-src2026.yaml"
    ]


def test_frozen_edits_flags_re_signing_an_already_signed_file(tmp_path):
    """A file that already carries release:/cic_countersign: and gets
    modified again (whatever the reason) is a real edit, not a first-time
    signing -- the exception may fire once, not repeatedly."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add already-signed ietf-nat", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: def456\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat/ietf-nat.v0.1.0-src2026.yaml"
    ]


def test_frozen_edits_flags_a_comment_change_smuggled_next_to_a_signature(tmp_path):
    """thead02: an earlier version of _only_gained_release_signature()
    compared parsed YAML dicts, which discards comments -- so a comment
    added to the surviving content alongside a legitimate signature would
    have parsed identically to the original and slipped through
    unnoticed. The fix compares bytes (original content must be an exact
    prefix of current), which catches this."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    original = "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
    _write(schema_dir / "ietf-nat.v0.1.0-src2026.yaml", original)
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    # a comment slipped into the surviving content -- invisible to
    # yaml.safe_load(), but a real byte-level change nonetheless.
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat  # sneaky comment\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat/ietf-nat.v0.1.0-src2026.yaml"
    ]
