"""Filename convention for the registry: one directory per schema, one file
per (content-version, signing-year) pair.

    <schema-name>.vMAJOR.MINOR.PATCH-src<YEAR>.yaml

MAJOR.MINOR.PATCH is the content version (semver). -src<YEAR> names the
calendar year of the CIC Root CA that signed this exact file — the CA
rotates yearly (proposals/schema-registry §6), so the same content can
legitimately exist as multiple files differing only in -src year, none of
which are "newer content" than the others.

No committed index/catalog file backs this — every function here works by
listing/parsing directories directly, per proposals/schema-registry §3
("nincs külön index/katalógus fájl — a könyvtárlistázás maga a keresés").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_FILENAME_RE = re.compile(
    r"^(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"\.v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"-src(?P<year>\d{4})"
    r"\.yaml$"
)


@dataclass(frozen=True, order=True)
class SchemaVersion:
    """One resolved (content-version, signing-year) file.

    Comparison/ordering is by (major, minor, patch, src_year) — this makes
    `sorted()` and `max()` do the right thing for both "latest content
    version" and "latest signature of a given content version" queries.
    """

    major: int
    minor: int
    patch: int
    src_year: int
    name: str
    path: Path

    @property
    def content_version(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def content_version_str(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.name}.{self.content_version_str}-src{self.src_year}"


def parse_filename(path: Path) -> SchemaVersion | None:
    """Parse one schema file's name. Returns None if it doesn't match the
    convention (e.g. a README.md or .gitkeep sitting in the same directory —
    those are expected and not an error)."""
    m = _FILENAME_RE.match(path.name)
    if not m:
        return None
    return SchemaVersion(
        major=int(m["major"]),
        minor=int(m["minor"]),
        patch=int(m["patch"]),
        src_year=int(m["year"]),
        name=m["name"],
        path=path,
    )


def list_versions(schema_dir: Path) -> list[SchemaVersion]:
    """All parseable schema-version files directly inside one schema
    directory, sorted oldest-content/oldest-signature first."""
    if not schema_dir.is_dir():
        return []
    versions = []
    for child in schema_dir.iterdir():
        if not child.is_file():
            continue
        v = parse_filename(child)
        if v is not None:
            versions.append(v)
    return sorted(versions)


def resolve_pin(schema_dir: Path, major: int, minor: int, patch: int) -> SchemaVersion | None:
    """Resolve a content-version pin (e.g. from `base: "...@v1.0.0"`) to the
    file with the LATEST still-listed -src year for that exact content
    version — this is the "reference resolution always follows the freshest
    valid signature" rule (proposals/schema-registry §8). Note: this does not
    itself check CA validity/expiry — a file that is present is assumed
    valid; expiry handling is a separate, not-yet-implemented concern (the
    scheduled CA-expiry job in the design doc)."""
    candidates = [
        v for v in list_versions(schema_dir) if v.content_version == (major, minor, patch)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v.src_year)


def latest_content_version(schema_dir: Path) -> SchemaVersion | None:
    """The single highest (major, minor, patch) version present, at its
    freshest signature — used for the (not-yet-wired) content-staleness
    report, not for reference resolution."""
    versions = list_versions(schema_dir)
    if not versions:
        return None
    return max(versions)
