"""Per-file signing (proposals/schema-registry §5): every schema file is its
own signed unit — no bundle, no release/ directory. This module produces the
same two blocks a bundle release used to carry (release.sign +
cic_countersign), except now embedded directly in the one file they cover.

Two independent signatures, both over the same build_hash:
  1. the author's own Vault Transit signature (release.sign)
  2. the CICSourceCA countersignature, obtained via mTLS from the
     cic-countersign service (cic_countersign block)

The mTLS leg is delegated to the existing vault-mtls-client Go binary
(built earlier this session) rather than reimplemented here — Python's
ssl module has no clean way to back a TLS client certificate with a
crypto.Signer-style callback, which is exactly what keeps the raw Vault
Transit key from ever touching this process. Shelling out to a small,
already-audited Go helper for that one operation is a reasonable
boundary, not a shortcut.
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess  # nosec B404 -- used once below, to invoke a fixed, local helper binary with a controlled environment, not arbitrary/user-supplied commands
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml

_TOP_LEVEL_SIGNATURE_KEYS = ("release", "cic_countersign")


class AlreadySignedError(Exception):
    """Raised when asked to sign a file that already carries release/
    cic_countersign blocks. Per proposals/schema-registry §5/§7, a file is
    signed exactly once, at the moment its content is finalized — a change
    afterwards is a new file (new version or new -src year), never an
    in-place re-sign."""


def compute_build_hash(path: Path) -> str:
    """base64(sha256(raw file bytes)) — the digest both signatures cover.
    Computed over the file exactly as it stands before any signature block
    is appended; nothing here can already be signed (see AlreadySignedError)."""
    digest = hashlib.sha256(path.read_bytes()).digest()
    return base64.b64encode(digest).decode()


def _check_not_already_signed(path: Path) -> None:
    doc = yaml.safe_load(path.read_text()) or {}
    present = [k for k in _TOP_LEVEL_SIGNATURE_KEYS if k in doc]
    if present:
        raise AlreadySignedError(
            f"{path} already has {present} — signing is one-shot per file; "
            "a content change belongs in a new -src<year> or version file, "
            "not a re-sign of this one"
        )


def sign_with_author_vault(
    build_hash_b64: str,
    *,
    vault_addr: str,
    vault_token: str,
    key_name: str,
    vault_ca_file: Path,
) -> str:
    """Direct (non-mTLS) call to the author's own Vault Transit key — this
    is release.sign, produced independently of the CICSourceCA leg below.

    `build_hash_b64` is ALREADY a base64-encoded SHA256 digest (see
    compute_build_hash) — prehashed must be true, or Vault base64-decodes
    it and hashes it a SECOND time, signing sha256(sha256(bytes)) instead
    of sha256(bytes). Caught only by the live end-to-end test against the
    real countersign-server, not by mocked unit tests (they'd have passed
    either way, since they only assert what gets sent, not what a real
    Vault does with it) — the author signature failed independent openssl
    verification the first time this ran for real.

    `vault_ca_file` pins the connection to the dev Vault's own self-signed
    certificate — this is the exact TLS-pinning gap that cic-countersign
    itself had and fixed (VAULT_CA_BUNDLE_FILE, PR #2 in that repo) earlier
    this session. Repeating it here as verify=False would be reintroducing
    the same class of vulnerability in new code, not a shortcut worth taking."""
    resp = requests.post(
        f"{vault_addr.rstrip('/')}/v1/transit/sign/{key_name}",
        headers={"X-Vault-Token": vault_token},
        json={"input": build_hash_b64, "prehashed": True, "hash_algorithm": "sha2-256"},
        verify=str(vault_ca_file),
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(f"vault sign failed: {body['errors']}")
    return body["data"]["signature"]


@dataclass
class MTLSClientConfig:
    """Everything vault-mtls-client needs, passed through as environment
    variables (matching how it was invoked manually earlier this session)."""

    binary: Path
    dev_vault_addr: str
    dev_vault_token: str
    dev_vault_ca_file: Path
    dev_vault_key_name: str
    signer_cert_file: Path
    countersign_addr: str
    countersign_ca_file: Path


def get_cic_countersign(
    build_hash_b64: str,
    document: dict[str, Any],
    workflow: str,
    cfg: MTLSClientConfig,
) -> dict[str, Any]:
    """Runs vault-mtls-client as a subprocess to obtain the CICSourceCA
    countersignature over build_hash_b64, via a real mTLS handshake whose
    client-certificate signature is itself Vault-delegated. Returns the
    inner `countersign` object exactly as the service returns it — this is
    embedded as-is under the file's own `cic_countersign:` key."""
    env = {
        "DEV_VAULT_ADDR": cfg.dev_vault_addr,
        "DEV_VAULT_TOKEN": cfg.dev_vault_token,
        "DEV_VAULT_CA_FILE": str(cfg.dev_vault_ca_file),
        "DEV_VAULT_KEY_NAME": cfg.dev_vault_key_name,
        "SIGNER_CERT_FILE": str(cfg.signer_cert_file),
        "COUNTERSIGN_ADDR": cfg.countersign_addr,
        "COUNTERSIGN_CA_FILE": str(cfg.countersign_ca_file),
        "BUILD_HASH": build_hash_b64,
        "DOCUMENT_JSON": json.dumps(document),
        "WORKFLOW": workflow,
    }
    # A fixed, absolute binary path with no shell involved (shell=False, the
    # default) and no user-controlled argument list — the only untrusted-ish
    # input is BUILD_HASH/DOCUMENT_JSON, passed via env, never interpolated
    # into a command line. #nosec B603 - not a shell-injection surface.
    result = subprocess.run(
        [str(cfg.binary)], env=env, capture_output=True, text=True, timeout=30
    )  # nosec B603
    stdout = result.stdout
    if "HTTP_STATUS=200" not in stdout:
        raise RuntimeError(
            f"countersign request failed (exit {result.returncode}):\n"
            f"{stdout}\n{result.stderr}"
        )
    json_start = stdout.index("HTTP_STATUS=200") + len("HTTP_STATUS=200\n")
    body = json.loads(stdout[json_start:])
    return body["countersign"]


def format_signature_blocks(
    *,
    author_name: str,
    author_email: str,
    author_certificate: str,
    build_hash_b64: str,
    author_sign: str,
    countersign: dict[str, Any],
) -> str:
    """The two top-level YAML blocks appended to a freshly-finalized schema
    file — release (author) and cic_countersign (CICSourceCA), matching the
    shape every bundle release already carried (proposals/schema-registry
    §5), just attached to one file instead of a bundle."""
    doc = {
        "release": {
            "createdBy": {
                "name": author_name,
                "email": author_email,
                "certificate": author_certificate,
            },
            "build_hash": build_hash_b64,
            "sign": author_sign,
        },
        "cic_countersign": countersign,
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)


def append_signature_blocks(path: Path, blocks_yaml: str) -> None:
    _check_not_already_signed(path)
    current = path.read_text()
    if not current.endswith("\n"):
        current += "\n"
    path.write_text(current + blocks_yaml)
