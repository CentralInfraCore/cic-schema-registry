import subprocess

from tools import generate_latest
from tools.generate_latest import (
    _already_signed_before,
    _commit_content,
    _dir_ever_had_versioned_content,
    _file_history_commits,
    _first_add_commit,
    _only_gained_release_signature,
    check_drift,
    check_no_frozen_edits,
    main,
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


# ── #92(a): signature swap -- the exception fires once, and only once,
# even across an already-COMMITTED intermediate signing ─────────────────────


def test_frozen_edits_clean_when_signing_is_its_own_commit(tmp_path):
    """Sanity check for the fix's own logic: a legitimate first-time
    signing that is ALREADY COMMITTED (not just a working-tree edit) must
    still read as clean -- _already_signed_before must not mistake the
    tip commit (which IS "current") for prior history."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "sign ietf-nat", cwd=tmp_path)

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == []


def test_frozen_edits_flags_a_signature_swap_after_a_committed_legitimate_signing(
    tmp_path,
):
    """#92(a): add (unsigned) -> sign (legitimate, committed) -> swap (a
    forged replacement signature). _only_gained_release_signature() alone
    compares current-vs-first_commit and would wrongly wave this through
    (unsigned original + "only signature keys appended" both still hold)
    -- _already_signed_before must catch that the file was ALREADY signed
    at the middle commit, so this is a real violation, not a first-time
    signing."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n  sign: vault:v1:legit\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "sign ietf-nat", cwd=tmp_path)

    # the forged replacement -- also committed, so this is not just an
    # uncommitted local edit either.
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n  sign: vault:v1:forged\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "swap the signature", cwd=tmp_path)

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat/ietf-nat.v0.1.0-src2026.yaml"
    ]


def test_frozen_edits_flags_an_uncommitted_swap_over_a_committed_signing(tmp_path):
    """Same #92(a) scenario, but the swap is an UNCOMMITTED working-tree
    edit on top of an already-committed legitimate signing -- confirms
    _already_signed_before doesn't rely on the swap itself being
    committed to detect the prior signed state."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n  sign: vault:v1:legit\n",
    )
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "sign ietf-nat", cwd=tmp_path)

    # uncommitted swap
    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        "metadata:\n  name: ietf-nat\nspec:\n  kind: YANGBlock\n"
        "release:\n  build_hash: abc123\n  sign: vault:v1:forged\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat/ietf-nat.v0.1.0-src2026.yaml"
    ]


# ── #92(b): a directory that used to have versioned content, now emptied ────


def test_frozen_edits_flags_a_directory_that_was_emptied(tmp_path):
    """A previously non-empty, enrolled directory with all its versioned
    files deleted (LATEST.yaml included) is a real integrity violation --
    check_no_frozen_edits only walks CURRENTLY-listed files, so without an
    explicit check, deleting everything makes it iterate zero files and
    report clean."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(schema_dir / "ietf-nat.v0.1.0-src2026.yaml", "metadata:\n  name: ietf-nat\n")
    _write(schema_dir / "LATEST.yaml", "schema: ietf-nat\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    (schema_dir / "ietf-nat.v0.1.0-src2026.yaml").unlink()
    (schema_dir / "LATEST.yaml").unlink()

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == [
        "ietf-nat — previously had versioned content, now empty "
        "(directory-emptying is not a sanctioned way to remove a "
        "published schema)"
    ]


def test_check_drift_flags_a_directory_that_was_emptied(tmp_path):
    """Same scenario from check_drift's side: an emptied directory with
    its LATEST.yaml also deleted renders as expected=None, actual=None --
    "no drift" -- unless the directory's git history is consulted."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    _write(schema_dir / "ietf-nat.v0.1.0-src2026.yaml", "metadata:\n  name: ietf-nat\n")
    write_latest(tmp_path, enrolled=["ietf-nat"])
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat", cwd=tmp_path)

    (schema_dir / "ietf-nat.v0.1.0-src2026.yaml").unlink()
    (schema_dir / "LATEST.yaml").unlink()

    assert check_drift(tmp_path, enrolled=["ietf-nat"]) == ["ietf-nat"]


def test_check_drift_clean_for_a_directory_that_was_always_empty(tmp_path):
    """An ENROLLED directory that legitimately never had any content
    (nothing committed under it, ever) must NOT be flagged -- only a
    directory that HAD content and lost it is a violation."""
    _init_repo(tmp_path)
    _write(tmp_path / "README.md", "placeholder so the repo isn't empty\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "init", cwd=tmp_path)

    assert check_drift(tmp_path, enrolled=["never-existed"]) == []


# ---- write_latest() skips a directory render_latest() has nothing for ----


def test_write_latest_skips_an_empty_enrolled_directory(tmp_path):
    assert write_latest(tmp_path, enrolled=["never-existed"]) == []
    assert not (tmp_path / "never-existed" / "LATEST.yaml").exists()


# ---- private git-subprocess helpers -- direct, whitebox: their own
# defensive "git failed" fallbacks are unreachable through the public
# check_no_frozen_edits/check_drift entry points in most cases (the
# callers only reach them once a diff/commit is already known to exist),
# so these exercise them directly instead of contriving an indirect path
# ----


def test_first_add_commit_returns_none_outside_a_git_repo(tmp_path):
    """Not a git repository at all -- git log itself fails."""
    target = tmp_path / "schema.yaml"
    _write(target, "a: 1\n")
    assert _first_add_commit(tmp_path, target) is None


def test_first_add_commit_returns_none_for_an_uncommitted_file(tmp_path):
    """A real repo, but this particular file was never `git add`ed --
    also covers check_no_frozen_edits's own `continue` when a version
    file has no git history at all yet."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    # deliberately never `git add`ed/committed

    version_file = schema_dir / "ietf-lldp.v0.1.3-src2026.yaml"
    assert _first_add_commit(tmp_path, version_file) is None
    # and the public check must not crash on it -- just skip it
    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-lldp"]) == []


def test_file_history_commits_returns_empty_outside_a_git_repo(tmp_path):
    target = tmp_path / "schema.yaml"
    _write(target, "a: 1\n")
    assert _file_history_commits(tmp_path, target) == []


def test_commit_content_returns_none_for_a_bogus_commit(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "a: 1\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)

    assert _commit_content(tmp_path, "0" * 40, target) is None


def test_dir_ever_had_versioned_content_false_outside_a_git_repo(tmp_path):
    assert _dir_ever_had_versioned_content(tmp_path, "ietf-lldp") is False


# ---- _only_gained_release_signature() -- individual defensive branches ----


def test_only_gained_signature_false_for_a_bogus_first_commit(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "a: 1\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)

    assert _only_gained_release_signature(tmp_path, "0" * 40, target) is False


def test_only_gained_signature_normalizes_a_missing_trailing_newline(tmp_path):
    """The first-committed content itself has no trailing newline -- the
    function must still recognize a clean signature-only append on top
    of it, not choke on the byte-level prefix check."""
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-nat"
    no_newline = "metadata:\n  name: ietf-nat"  # deliberately no trailing \n
    _write(schema_dir / "ietf-nat.v0.1.0-src2026.yaml", no_newline)
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add ietf-nat (no trailing newline)", cwd=tmp_path)

    _write(
        schema_dir / "ietf-nat.v0.1.0-src2026.yaml",
        no_newline + "\nrelease:\n  build_hash: abc123\n",
    )

    assert check_no_frozen_edits(tmp_path, enrolled=["ietf-nat"]) == []


def test_only_gained_signature_false_when_nothing_was_appended(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    assert _only_gained_release_signature(tmp_path, first_commit, target) is False


def test_only_gained_signature_false_when_appended_text_is_not_valid_yaml(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    _write(target, "metadata:\n  name: x\nrelease:\n  sign: [unterminated\n")

    assert _only_gained_release_signature(tmp_path, first_commit, target) is False


def test_only_gained_signature_false_when_appended_is_not_a_mapping(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    _write(target, "metadata:\n  name: x\njust a scalar line\n")

    assert _only_gained_release_signature(tmp_path, first_commit, target) is False


def test_only_gained_signature_false_when_a_non_signature_key_is_appended(tmp_path):
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    _write(target, "metadata:\n  name: x\nextra_field: sneaked in\n")

    assert _only_gained_release_signature(tmp_path, first_commit, target) is False


def test_only_gained_signature_false_when_original_was_already_signed(tmp_path):
    """The original (first-committed) content already carries a
    signature key -- even a clean, signature-keys-only append on top of
    it is not a first-time signing."""
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\nrelease:\n  sign: old\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add already-signed", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    _write(
        target,
        "metadata:\n  name: x\nrelease:\n  sign: old\ncic_countersign:\n  sign: new\n",
    )

    assert _only_gained_release_signature(tmp_path, first_commit, target) is False


# ---- _already_signed_before() -- malformed intermediate history entry ----


def test_already_signed_before_skips_unparseable_intermediate_commits(tmp_path):
    """An intermediate commit's content fails to parse as YAML --
    _already_signed_before must skip it (not crash) and keep looking."""
    _init_repo(tmp_path)
    target = tmp_path / "schema.yaml"
    _write(target, "metadata:\n  name: x\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add", cwd=tmp_path)
    first_commit = _first_add_commit(tmp_path, target)

    _write(target, "not: [valid yaml\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "briefly broken", cwd=tmp_path)

    _write(target, "metadata:\n  name: x\nrelease:\n  sign: abc\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "fix and sign", cwd=tmp_path)

    assert _already_signed_before(tmp_path, first_commit, target) is False


# ---- main() -- the CLI entry point itself, end to end with real git repos ----


def test_main_default_mode_nothing_to_update(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generate_latest, "ENROLLED", ["never-existed"])
    _init_repo(tmp_path)
    _write(tmp_path / "README.md", "placeholder\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "init", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)

    rc = main([])

    assert rc == 0
    assert "nothing to update" in capsys.readouterr().out


def test_main_default_mode_writes_latest_and_reports_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generate_latest, "ENROLLED", ["ietf-lldp"])
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)

    rc = main([])

    assert rc == 0
    out = capsys.readouterr().out
    assert "generate_latest: updated:" in out
    assert "ietf-lldp/LATEST.yaml" in out
    assert (schema_dir / "LATEST.yaml").exists()


def test_main_check_mode_ok_when_up_to_date(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generate_latest, "ENROLLED", ["ietf-lldp"])
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    write_latest(tmp_path, enrolled=["ietf-lldp"])
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3 + LATEST.yaml", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)

    rc = main(["--check"])

    assert rc == 0
    assert "generate_latest: OK" in capsys.readouterr().out


def test_main_check_mode_fails_on_drift(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generate_latest, "ENROLLED", ["ietf-lldp"])
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "a: 1\n")
    # deliberately never ran write_latest -- LATEST.yaml is missing
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)

    rc = main(["--check"])

    assert rc == 1
    out = capsys.readouterr().out
    assert "LATEST.yaml is stale" in out
    assert "ietf-lldp/LATEST.yaml" in out


def test_main_fails_on_a_frozen_edit_before_even_checking_drift(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(generate_latest, "ENROLLED", ["ietf-lldp"])
    _init_repo(tmp_path)
    schema_dir = tmp_path / "ietf-lldp"
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "source: RFC 8516\n")
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-q", "-m", "add v0.1.3", cwd=tmp_path)
    _write(schema_dir / "ietf-lldp.v0.1.3-src2026.yaml", "source: IEEE 802.1ABcu\n")
    monkeypatch.chdir(tmp_path)

    rc = main(["--check"])

    assert rc == 1
    out = capsys.readouterr().out
    assert "an already-published schema file was" in out
    assert "ietf-lldp/ietf-lldp.v0.1.3-src2026.yaml" in out
