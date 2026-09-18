import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to sys.path to allow importing 'tools'
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools import registry_sign
from tools.registrylib.signing import AlreadySignedError

REQUIRED_ENV = {
    "VAULT_TOKEN": "test-token",
    "COUNTERSIGN_CA_FILE": "/fake/countersign-ca.pem",
    "DEV_VAULT_CA_FILE": "/fake/dev-vault-ca.pem",
}


def _patch_collaborators(mock_module, *, countersign_authority="CIC Source CA"):
    """Patches every collaborator registry_sign.main() calls, wired for a
    clean success path -- individual tests override what they need."""
    mock_module.compute_build_hash.return_value = "aGVsbG8="
    mock_module._fetch_author_certificate.return_value = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
    mock_module.sign_with_author_vault.return_value = "vault:v1:author-sig"
    mock_module.get_cic_countersign.return_value = {
        "authority": {"name": countersign_authority},
        "sign": "vault:v1:counter-sig",
    }
    mock_module.format_signature_blocks.return_value = "release:\n  sign: x\n"


def test_main_wrong_argc_prints_usage_and_returns_2(capsys):
    assert registry_sign.main(["registry_sign.py"]) == 2
    assert "Usage:" in capsys.readouterr().out


def test_main_too_many_args_returns_2():
    assert registry_sign.main(["registry_sign.py", "a.yaml", "b.yaml"]) == 2


def test_main_nonexistent_file_returns_2(tmp_path, capsys):
    missing = tmp_path / "nope.yaml"
    rc = registry_sign.main(["registry_sign.py", str(missing)])
    assert rc == 2
    assert "not a file" in capsys.readouterr().out


def test_main_missing_vault_token_raises(tmp_path, monkeypatch):
    """VAULT_TOKEN/COUNTERSIGN_CA_FILE/DEV_VAULT_CA_FILE are read via
    os.environ[...] (not .get()) BEFORE the try block -- a missing one is
    an uncaught KeyError, not a handled CLI error. Documents the actual
    current behavior, not a claim about what it should be."""
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\n")
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(KeyError):
        registry_sign.main(["registry_sign.py", str(target)])


@patch.object(registry_sign, "append_signature_blocks")
@patch.object(registry_sign, "format_signature_blocks")
@patch.object(registry_sign, "get_cic_countersign")
@patch.object(registry_sign, "sign_with_author_vault")
@patch.object(registry_sign, "_fetch_author_certificate")
@patch.object(registry_sign, "compute_build_hash")
def test_main_success_path_returns_0_and_calls_append(
    mock_build_hash,
    mock_fetch_cert,
    mock_vault_sign,
    mock_countersign,
    mock_format_blocks,
    mock_append,
    tmp_path,
    monkeypatch,
    capsys,
):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\n")

    mock_build_hash.return_value = "aGVsbG8="
    mock_fetch_cert.return_value = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
    mock_vault_sign.return_value = "vault:v1:author-sig"
    mock_countersign.return_value = {
        "authority": {"name": "CIC Source CA"},
        "sign": "vault:v1:counter-sig",
    }
    mock_format_blocks.return_value = "release:\n  sign: x\n"

    rc = registry_sign.main(["registry_sign.py", str(target)])

    assert rc == 0
    out = capsys.readouterr().out
    assert "OK: signed" in out
    mock_append.assert_called_once_with(target, "release:\n  sign: x\n")
    # the author sign call must carry the digest through unchanged
    mock_vault_sign.assert_called_once()
    assert mock_vault_sign.call_args.args[0] == "aGVsbG8="


@patch.object(registry_sign, "get_cic_countersign")
@patch.object(registry_sign, "sign_with_author_vault")
@patch.object(registry_sign, "_fetch_author_certificate")
@patch.object(registry_sign, "compute_build_hash")
def test_main_cleans_up_temp_cert_file_even_on_countersign_failure(
    mock_build_hash,
    mock_fetch_cert,
    mock_vault_sign,
    mock_countersign,
    tmp_path,
    monkeypatch,
):
    """The temp file holding the author cert (for vault-mtls-client's
    SIGNER_CERT_FILE) must not leak on the working directory even when
    get_cic_countersign() raises."""
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\n")

    mock_build_hash.return_value = "aGVsbG8="
    mock_fetch_cert.return_value = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
    mock_vault_sign.return_value = "vault:v1:author-sig"
    mock_countersign.side_effect = RuntimeError("countersign server unreachable")

    rc = registry_sign.main(["registry_sign.py", str(target)])

    assert rc == 1
    cert_tmp = target.parent / ".registry_sign_author_cert.pem.tmp"
    assert not cert_tmp.exists()


@patch.object(registry_sign, "compute_build_hash")
def test_main_already_signed_error_returns_1_and_prints_skip(
    mock_build_hash, tmp_path, monkeypatch, capsys
):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\nrelease:\n  sign: already\n")
    mock_build_hash.side_effect = AlreadySignedError(f"{target} already signed")

    rc = registry_sign.main(["registry_sign.py", str(target)])

    assert rc == 1
    assert "SKIP:" in capsys.readouterr().out


@patch.object(registry_sign, "compute_build_hash")
def test_main_generic_exception_returns_1_and_prints_failed(
    mock_build_hash, tmp_path, monkeypatch, capsys
):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\n")
    mock_build_hash.side_effect = RuntimeError("disk on fire")

    rc = registry_sign.main(["registry_sign.py", str(target)])

    assert rc == 1
    assert "FAILED:" in capsys.readouterr().out


def test_fetch_author_certificate_returns_the_single_kv_field():
    resp = MagicMock()
    resp.json.return_value = {"data": {"data": {"bar": "-----BEGIN CERTIFICATE-----\n..."}}}
    resp.raise_for_status.return_value = None
    with patch("tools.registry_sign.requests.get", return_value=resp) as mock_get:
        cert = registry_sign._fetch_author_certificate(
            "https://127.0.0.1:18200",
            "tok",
            "cic-my-sign-key/data/crt",
            Path("/fake/ca.pem"),
        )
    assert cert == "-----BEGIN CERTIFICATE-----\n..."
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["verify"] == "/fake/ca.pem"


def test_fetch_author_certificate_raises_on_vault_errors_field():
    resp = MagicMock()
    resp.json.return_value = {"errors": ["permission denied"]}
    resp.raise_for_status.return_value = None
    with patch("tools.registry_sign.requests.get", return_value=resp):
        with pytest.raises(RuntimeError, match="vault kv read failed"):
            registry_sign._fetch_author_certificate(
                "https://127.0.0.1:18200",
                "tok",
                "cic-my-sign-key/data/crt",
                Path("/fake/ca.pem"),
            )


@patch.object(registry_sign, "append_signature_blocks")
@patch.object(registry_sign, "format_signature_blocks")
@patch.object(registry_sign, "get_cic_countersign")
@patch.object(registry_sign, "sign_with_author_vault")
@patch.object(registry_sign, "_fetch_author_certificate")
@patch.object(registry_sign, "compute_build_hash")
def test_main_uses_env_var_defaults_when_optional_ones_unset(
    mock_build_hash,
    mock_fetch_cert,
    mock_vault_sign,
    mock_countersign,
    mock_format_blocks,
    mock_append,
    tmp_path,
    monkeypatch,
):
    """VAULT_ADDR/VAULT_KEY_NAME/VAULT_CERT_PATH/COUNTERSIGN_ADDR/
    VAULT_MTLS_CLIENT_BIN all have defaults per the module docstring --
    only VAULT_TOKEN/COUNTERSIGN_CA_FILE/DEV_VAULT_CA_FILE are required."""
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    for optional in (
        "VAULT_ADDR",
        "VAULT_KEY_NAME",
        "VAULT_CERT_PATH",
        "COUNTERSIGN_ADDR",
        "VAULT_MTLS_CLIENT_BIN",
    ):
        monkeypatch.delenv(optional, raising=False)
    target = tmp_path / "schema.yaml"
    target.write_text("metadata:\n  name: X\n")

    mock_build_hash.return_value = "aGVsbG8="
    mock_fetch_cert.return_value = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
    mock_vault_sign.return_value = "vault:v1:author-sig"
    mock_countersign.return_value = {
        "authority": {"name": "CIC Source CA"},
        "sign": "vault:v1:counter-sig",
    }
    mock_format_blocks.return_value = "release:\n  sign: x\n"

    rc = registry_sign.main(["registry_sign.py", str(target)])

    assert rc == 0
    mock_fetch_cert.assert_called_once_with(
        "https://127.0.0.1:18200",
        "test-token",
        "cic-my-sign-key/data/crt",
        Path("/fake/dev-vault-ca.pem"),
    )
    mtls_cfg = mock_countersign.call_args.kwargs["cfg"]
    assert mtls_cfg.binary == Path("tools/bin/vault-mtls-client")
    assert mtls_cfg.countersign_addr == "127.0.0.1:8443"
