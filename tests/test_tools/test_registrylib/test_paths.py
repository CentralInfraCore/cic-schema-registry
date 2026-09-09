from pathlib import Path

from tools.registrylib.paths import (
    list_versions,
    parse_filename,
    resolve_pin,
    latest_content_version,
)


def test_parse_filename_valid():
    v = parse_filename(Path("storage-resource.v1.0.0-src2026.yaml"))
    assert v is not None
    assert (v.major, v.minor, v.patch, v.src_year) == (1, 0, 0, 2026)
    assert v.name == "storage-resource"
    assert v.content_version_str == "v1.0.0"


def test_parse_filename_rejects_non_matching():
    assert parse_filename(Path("README.md")) is None
    assert parse_filename(Path(".gitkeep")) is None
    # no -src suffix — not a valid registry filename
    assert parse_filename(Path("storage-resource.v1.0.0.yaml")) is None


def test_list_versions_sorted(tmp_path):
    d = tmp_path / "storage-resource"
    d.mkdir()
    for fname in [
        "storage-resource.v1.1.0-src2027.yaml",
        "storage-resource.v1.0.0-src2026.yaml",
        "storage-resource.v1.0.0-src2027.yaml",
    ]:
        (d / fname).write_text("---\n")
    (d / "README.md").write_text("# doc\n")

    versions = list_versions(d)
    assert [str(v) for v in versions] == [
        "storage-resource.v1.0.0-src2026",
        "storage-resource.v1.0.0-src2027",
        "storage-resource.v1.1.0-src2027",
    ]


def test_resolve_pin_picks_freshest_signature(tmp_path):
    d = tmp_path / "storage-resource"
    d.mkdir()
    (d / "storage-resource.v1.0.0-src2026.yaml").write_text("---\n")
    (d / "storage-resource.v1.0.0-src2027.yaml").write_text("---\n")
    (d / "storage-resource.v1.1.0-src2027.yaml").write_text("---\n")

    resolved = resolve_pin(d, 1, 0, 0)
    assert resolved is not None
    assert resolved.src_year == 2027  # freshest signature of v1.0.0, not v1.1.0

    assert resolve_pin(d, 9, 9, 9) is None


def test_latest_content_version(tmp_path):
    d = tmp_path / "storage-resource"
    d.mkdir()
    (d / "storage-resource.v1.0.0-src2026.yaml").write_text("---\n")
    (d / "storage-resource.v1.1.0-src2027.yaml").write_text("---\n")

    latest = latest_content_version(d)
    assert latest.content_version == (1, 1, 0)


def test_list_versions_missing_dir(tmp_path):
    assert list_versions(tmp_path / "does-not-exist") == []
