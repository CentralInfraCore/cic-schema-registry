import base64
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tools.registrylib.signing import (
    AlreadySignedError,
    append_signature_blocks,
    compute_build_hash,
    format_signature_blocks,
    sign_with_author_vault,
)


def test_compute_build_hash_is_sha256_of_raw_bytes(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("hello world")
    expected = base64.b64encode(hashlib.sha256(b"hello world").digest()).decode()
    assert compute_build_hash(f) == expected


def test_compute_build_hash_changes_with_content(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("v1")
    h1 = compute_build_hash(f)
    f.write_text("v2")
    h2 = compute_build_hash(f)
    assert h1 != h2


def test_append_signature_blocks_refuses_already_signed_file(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("metadata:\n  name: X\nrelease:\n  sign: already-here\n")
    with pytest.raises(AlreadySignedError):
        append_signature_blocks(f, "cic_countersign:\n  sign: x\n")


def test_append_signature_blocks_refuses_already_countersigned_file(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("metadata:\n  name: X\ncic_countersign:\n  sign: already-here\n")
    with pytest.raises(AlreadySignedError):
        append_signature_blocks(f, "release:\n  sign: x\n")


def test_append_signature_blocks_appends_and_stays_valid_yaml(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("metadata:\n  name: X\nspec:\n  kind: DomainComposition\n")
    blocks = format_signature_blocks(
        author_name="A",
        author_email="a@example.com",
        author_certificate="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n",
        build_hash_b64="aGVsbG8=",
        author_sign="vault:v1:abc",
        countersign={"authority": {"name": "CIC Source CA"}, "sign": "vault:v1:def"},
    )
    append_signature_blocks(f, blocks)

    doc = yaml.safe_load(f.read_text())
    assert doc["metadata"]["name"] == "X"
    assert doc["release"]["build_hash"] == "aGVsbG8="
    assert doc["release"]["sign"] == "vault:v1:abc"
    assert doc["cic_countersign"]["authority"]["name"] == "CIC Source CA"


def test_append_signature_blocks_adds_missing_trailing_newline(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("metadata:\n  name: X")  # no trailing newline
    append_signature_blocks(f, "release:\n  sign: x\n")
    doc = yaml.safe_load(f.read_text())
    assert doc["metadata"]["name"] == "X"
    assert doc["release"]["sign"] == "x"


def test_format_signature_blocks_shape_matches_real_release_files():
    """The shape must match what every real bundle release already carried
    (release.createdBy/build_hash/sign, cic_countersign.authority/...) -
    proposals/schema-registry §5 says this is the same content, just moved
    from a bundle into the one file it covers, not a new format."""
    blocks = format_signature_blocks(
        author_name="Gabor Zoltan Sinko",
        author_email="sinkog@centralinfracore.hu",
        author_certificate="CERT",
        build_hash_b64="HASH",
        author_sign="vault:v1:sig",
        countersign={
            "authority": {"name": "CIC Source CA", "certificate": "CACERT"},
            "signed_payload": "build_hash",
            "sign": "vault:v1:cs",
            "workflow": "test@v1",
            "ts": "2026-01-01T00:00:00Z",
        },
    )
    doc = yaml.safe_load(blocks)
    assert set(doc.keys()) == {"release", "cic_countersign"}
    assert set(doc["release"].keys()) == {"createdBy", "build_hash", "sign"}
    assert set(doc["release"]["createdBy"].keys()) == {"name", "email", "certificate"}
    assert doc["cic_countersign"]["signed_payload"] == "build_hash"


def test_sign_with_author_vault_posts_prehashed_true_and_returns_signature():
    """build_hash_b64 is already a digest (compute_build_hash) — this MUST
    go over the wire as prehashed:true, or Vault hashes it a second time
    and signs sha256(sha256(bytes)) instead of sha256(bytes) (a real bug
    caught only by the live end-to-end test, not by an earlier version of
    this very assertion — it used to assert prehashed:False, which was
    wrong and passing for the wrong reason)."""
    fake_response = MagicMock()
    fake_response.json.return_value = {"data": {"signature": "vault:v1:sig"}}
    fake_response.raise_for_status.return_value = None
    with patch(
        "tools.registrylib.signing.requests.post", return_value=fake_response
    ) as post:
        result = sign_with_author_vault(
            "aGVsbG8=",
            vault_addr="https://vault.example:18200",
            vault_token="tok",
            key_name="cic-my-sign-key",
            vault_ca_file=Path("/dev/null"),
        )
    assert result == "vault:v1:sig"
    args, kwargs = post.call_args
    assert args[0] == "https://vault.example:18200/v1/transit/sign/cic-my-sign-key"
    assert kwargs["json"] == {
        "input": "aGVsbG8=",
        "prehashed": True,
        "hash_algorithm": "sha2-256",
    }
    assert kwargs["headers"]["X-Vault-Token"] == "tok"
    assert kwargs["verify"] == "/dev/null"


def test_sign_with_author_vault_raises_on_vault_error():
    fake_response = MagicMock()
    fake_response.json.return_value = {"errors": ["permission denied"]}
    fake_response.raise_for_status.return_value = None
    with patch("tools.registrylib.signing.requests.post", return_value=fake_response):
        with pytest.raises(RuntimeError, match="permission denied"):
            sign_with_author_vault(
                "aGVsbG8=",
                vault_addr="https://v:1",
                vault_token="t",
                key_name="k",
                vault_ca_file=Path("/dev/null"),
            )
