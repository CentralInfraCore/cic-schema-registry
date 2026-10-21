"""The vendored common VCN fixture is byte-for-byte what its manifest says."""

import hashlib
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "vcn-v1"


def _manifest():
    rows = [
        line.split("  ", 1)
        for line in (FIXTURE / "MANIFEST.sha256")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    return {name: digest for digest, name in rows}


def test_every_manifest_entry_matches_its_file():
    manifest = _manifest()
    assert len(manifest) > 50
    for name, digest in manifest.items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest, name


def test_no_file_is_outside_the_manifest_except_the_readme_and_the_manifest():
    on_disk = {
        str(p.relative_to(FIXTURE))
        for p in FIXTURE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert on_disk - set(_manifest()) == {"README.md", "MANIFEST.sha256"}


def test_the_fixture_has_the_nine_cases_of_the_agreement():
    cases = json.loads((FIXTURE / "cases.json").read_text(encoding="utf-8"))
    assert sorted(cases) == [
        "conformant",
        "desired-absent",
        "desired-absent-observed-present",
        "drift",
        "field-absent",
        "malformed-cidr",
        "not-found",
        "partial-read",
        "transport-error",
    ]
