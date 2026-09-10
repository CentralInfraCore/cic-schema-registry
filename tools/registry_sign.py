#!/usr/bin/env python3
"""CLI: sign one schema file, in place, per proposals/schema-registry §5.

Usage:
    python -m tools.registry_sign <path/to/schema.yaml>

Reads Vault/cic-countersign connection details from environment variables
(no config file — this is a one-shot operation run by a human or CI at the
moment a file's content is finalized, not a long-lived service):

    VAULT_ADDR              default: https://127.0.0.1:18200
    VAULT_TOKEN              (required — author's Vault Transit token)
    VAULT_KEY_NAME           default: cic-my-sign-key
    VAULT_CERT_PATH          KV path to the author's own certificate,
                             default: cic-my-sign-key/data/crt (field "bar")
    COUNTERSIGN_ADDR         default: 127.0.0.1:8443
    COUNTERSIGN_CA_FILE      (required — TLS trust for the countersign server)
    DEV_VAULT_CA_FILE        (required — TLS trust for VAULT_ADDR itself)
    VAULT_MTLS_CLIENT_BIN    default: tools/bin/vault-mtls-client

This intentionally does NOT run inside the Docker builder container the
rest of this repo's tooling uses — it needs to reach the host's Vault and
cic-countersign processes directly, which are not container-visible here.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

from .registrylib.signing import (
    AlreadySignedError,
    MTLSClientConfig,
    append_signature_blocks,
    compute_build_hash,
    format_signature_blocks,
    get_cic_countersign,
    sign_with_author_vault,
)

AUTHOR_NAME = "Gabor Zoltan Sinko"
AUTHOR_EMAIL = "sinkog@centralinfracore.hu"


def _fetch_author_certificate(
    vault_addr: str, vault_token: str, cert_path: str, vault_ca_file: Path
) -> str:
    resp = requests.get(
        f"{vault_addr.rstrip('/')}/v1/{cert_path}",
        headers={"X-Vault-Token": vault_token},
        verify=str(vault_ca_file),
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(f"vault kv read failed: {body['errors']}")
    data = body["data"]["data"]
    # This KV entry is a single-field secret ("bar" in every project.yaml's
    # vault_cert_path seen across this ecosystem) — take whatever the one
    # field is rather than hardcoding the name, since it varies by convention
    # only in that one detail.
    return next(iter(data.values()))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    target = Path(argv[1])
    if not target.is_file():
        print(f"not a file: {target}")
        return 2

    vault_addr = os.environ.get("VAULT_ADDR", "https://127.0.0.1:18200")
    vault_token = os.environ["VAULT_TOKEN"]
    vault_key_name = os.environ.get("VAULT_KEY_NAME", "cic-my-sign-key")
    vault_cert_path = os.environ.get("VAULT_CERT_PATH", "cic-my-sign-key/data/crt")
    countersign_addr = os.environ.get("COUNTERSIGN_ADDR", "127.0.0.1:8443")
    countersign_ca_file = Path(os.environ["COUNTERSIGN_CA_FILE"])
    dev_vault_ca_file = Path(os.environ["DEV_VAULT_CA_FILE"])
    mtls_client_bin = Path(
        os.environ.get("VAULT_MTLS_CLIENT_BIN", "tools/bin/vault-mtls-client")
    )

    try:
        build_hash = compute_build_hash(target)
        print(f"build_hash: {build_hash}")

        author_cert = _fetch_author_certificate(
            vault_addr, vault_token, vault_cert_path, dev_vault_ca_file
        )
        author_sign = sign_with_author_vault(
            build_hash,
            vault_addr=vault_addr,
            vault_token=vault_token,
            key_name=vault_key_name,
            vault_ca_file=dev_vault_ca_file,
        )
        print(f"author sign: {author_sign[:50]}...")

        # A temp file holding the author cert, for vault-mtls-client's
        # SIGNER_CERT_FILE — it needs a path, not inline PEM text.
        cert_tmp = target.parent / ".registry_sign_author_cert.pem.tmp"
        cert_tmp.write_text(author_cert)
        try:
            cfg = MTLSClientConfig(
                binary=mtls_client_bin,
                dev_vault_addr=vault_addr,
                dev_vault_token=vault_token,
                dev_vault_ca_file=dev_vault_ca_file,
                dev_vault_key_name=vault_key_name,
                signer_cert_file=cert_tmp,
                countersign_addr=countersign_addr,
                countersign_ca_file=countersign_ca_file,
            )
            countersign = get_cic_countersign(
                build_hash,
                document={"schema_file": str(target), "build_hash": build_hash},
                workflow="cic-schema-registry-sign@v1",
                cfg=cfg,
            )
        finally:
            cert_tmp.unlink(missing_ok=True)
        print(
            f"cic_countersign authority: {countersign.get('authority', {}).get('name')}"
        )

        blocks = format_signature_blocks(
            author_name=AUTHOR_NAME,
            author_email=AUTHOR_EMAIL,
            author_certificate=author_cert,
            build_hash_b64=build_hash,
            author_sign=author_sign,
            countersign=countersign,
        )
        append_signature_blocks(target, blocks)
        print(f"OK: signed {target}")
        return 0
    except AlreadySignedError as e:
        print(f"SKIP: {e}")
        return 1
    except Exception as e:  # noqa: BLE001 - top-level CLI error reporting
        print(f"FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
