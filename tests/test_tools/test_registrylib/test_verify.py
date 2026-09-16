"""#102: tools.registrylib.verify actually verifies the crypto, not just
presence. Positive fixture is a REAL signed file already in the corpus
(ietf-nat.v0.1.0) -- proof this isn't just self-consistent with its own
test fixtures. Negative fixtures are synthetic, self-signed EC
certificates built here so each failure mode (bad hash, bad signature,
wrong signer, broken chain) can be exercised in isolation."""

import base64
import datetime
import hashlib
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
from cryptography.x509.oid import NameOID

from tools.registrylib.verify import (
    SignatureVerificationError,
    UnsupportedSignatureEnvelopeError,
    verify_release_signature,
)

REAL_SIGNED_FILE = Path("standards/yang/ietf-nat/ietf-nat.v0.1.0-src2026.yaml")


def test_real_corpus_file_verifies():
    """The actual, already-signed ietf-nat.v0.1.0 must verify clean --
    proof this checks a real Vault+CICSourceCA signature, not just its
    own synthetic fixtures below."""
    assert REAL_SIGNED_FILE.exists(), "run from the registry root"
    verify_release_signature(REAL_SIGNED_FILE)  # must not raise


def test_real_corpus_file_fails_if_content_tampered(tmp_path):
    raw = REAL_SIGNED_FILE.read_bytes()
    tampered = raw.replace(b"DNAT", b"ZNAT", 1)
    assert tampered != raw
    p = tmp_path / "tampered.yaml"
    p.write_bytes(tampered)
    with pytest.raises(SignatureVerificationError, match="build_hash mismatch"):
        verify_release_signature(p)


# ---- synthetic fixtures for the individual failure modes ----


def _self_signed_ca(name: str):
    key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2026, 1, 1))
        .not_valid_after(datetime.datetime(2027, 1, 1))
        .sign(key, hashes.SHA256())
    )
    return key, cert


def _signed_cert(name: str, issuer_key, issuer_cert):
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
        .issuer_name(issuer_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2026, 1, 1))
        .not_valid_after(datetime.datetime(2027, 1, 1))
        .sign(issuer_key, hashes.SHA256())
    )
    return key, cert


def _pem(cert) -> str:
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def _vault_sign(key, digest: bytes) -> str:
    sig = key.sign(digest, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256())))
    return "vault:v1:" + base64.b64encode(sig).decode()


def _build_signed_file(
    content: bytes,
    author_key,
    author_cert,
    authority_key,
    authority_cert,
    root_cert,
    *,
    author_sig_override: str | None = None,
    countersign_sig_override: str | None = None,
    build_hash_override: str | None = None,
) -> bytes:
    digest = hashlib.sha256(content).digest()
    build_hash = build_hash_override or base64.b64encode(digest).decode()
    author_sign = author_sig_override or _vault_sign(author_key, digest)
    countersign_sign = countersign_sig_override or _vault_sign(authority_key, digest)

    release = (
        "release:\n"
        "  createdBy:\n"
        f"    certificate: '{_pem(author_cert)}'\n"
        f"  build_hash: {build_hash}\n"
        f"  sign: {author_sign}\n"
        "cic_countersign:\n"
        "  authority:\n"
        f"    certificate: '{_pem(authority_cert)}'\n"
        f"    root_certificate: '{_pem(root_cert)}'\n"
        "  signed_payload: build_hash\n"
        f"  sign: {countersign_sign}\n"
    )
    return content + release.encode()


@pytest.fixture
def chain():
    root_key, root_cert = _self_signed_ca("CIC Root CA (test)")
    authority_key, authority_cert = _signed_cert(
        "CIC Source CA (test)", root_key, root_cert
    )
    author_key, author_cert = _self_signed_ca("Test Author")
    return {
        "root_key": root_key,
        "root_cert": root_cert,
        "authority_key": authority_key,
        "authority_cert": authority_cert,
        "author_key": author_key,
        "author_cert": author_cert,
    }


def test_valid_synthetic_chain_verifies(tmp_path, chain):
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    verify_release_signature(p)  # must not raise


def test_rejects_wrong_build_hash(tmp_path, chain):
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
        build_hash_override=base64.b64encode(b"\x00" * 32).decode(),
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    with pytest.raises(SignatureVerificationError, match="build_hash mismatch"):
        verify_release_signature(p)


def test_rejects_author_signature_from_wrong_key(tmp_path, chain):
    """Someone else's valid-looking signature, not the author's own --
    must not verify against the author's certificate."""
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    digest = hashlib.sha256(content).digest()
    impostor_key = ec.generate_private_key(ec.SECP256R1())
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
        author_sig_override=_vault_sign(impostor_key, digest),
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    with pytest.raises(SignatureVerificationError, match="release.sign"):
        verify_release_signature(p)


def test_rejects_countersign_signature_from_wrong_key(tmp_path, chain):
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    digest = hashlib.sha256(content).digest()
    impostor_key = ec.generate_private_key(ec.SECP256R1())
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
        countersign_sig_override=_vault_sign(impostor_key, digest),
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    with pytest.raises(SignatureVerificationError, match="cic_countersign.sign"):
        verify_release_signature(p)


def test_rejects_authority_certificate_not_chained_to_root(tmp_path, chain):
    """The countersign authority certificate is real and its signature
    over build_hash is real -- but it was never actually issued by the
    embedded root certificate (a different, unrelated CA signed it).
    Presence of a root_certificate field is not a chain; this must
    verify the actual X.509 signature, not just accept whatever PEM is
    embedded."""
    other_root_key, other_root_cert = _self_signed_ca("Some Other CA")
    rogue_authority_key, rogue_authority_cert = _signed_cert(
        "Rogue Source CA", other_root_key, other_root_cert
    )
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        rogue_authority_key,
        rogue_authority_cert,
        chain["root_cert"],  # claims to chain to the REAL root, but doesn't
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    with pytest.raises(SignatureVerificationError, match="authority chain"):
        verify_release_signature(p)


def test_rejects_missing_release_block(tmp_path):
    p = tmp_path / "unsigned.yaml"
    p.write_text("metadata:\n  name: X\nspec:\n  kind: YANGBlock\n")
    with pytest.raises(SignatureVerificationError, match="missing 'release' block"):
        verify_release_signature(p)


def test_rejects_missing_countersign_block(tmp_path, chain):
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    digest = hashlib.sha256(content).digest()
    build_hash = base64.b64encode(digest).decode()
    author_sign = _vault_sign(chain["author_key"], digest)
    text = (
        content.decode()
        + "release:\n"
        + "  createdBy:\n"
        + f"    certificate: '{_pem(chain['author_cert'])}'\n"
        + f"  build_hash: {build_hash}\n"
        + f"  sign: {author_sign}\n"
    )
    p = tmp_path / "half-signed.yaml"
    p.write_text(text)
    with pytest.raises(
        SignatureVerificationError, match="missing 'cic_countersign' block"
    ):
        verify_release_signature(p)


def test_unrecognized_signature_prefix_is_rejected(tmp_path, chain):
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
        author_sig_override="not-a-vault-signature",
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    with pytest.raises(SignatureVerificationError, match="unrecognized signature"):
        verify_release_signature(p)


def test_key_rotation_prefix_vault_v2_is_accepted(tmp_path, chain):
    """cic-schema-registry#104: the prefix carries the Vault key version,
    not just v1 -- verification must not hardcode it either."""
    content = b"metadata:\n  name: X\nspec:\n  kind: YANGBlock\n"
    digest = hashlib.sha256(content).digest()
    sig = chain["author_key"].sign(
        digest, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256()))
    )
    v2_sig = "vault:v2:" + base64.b64encode(sig).decode()
    data = _build_signed_file(
        content,
        chain["author_key"],
        chain["author_cert"],
        chain["authority_key"],
        chain["authority_cert"],
        chain["root_cert"],
        author_sig_override=v2_sig,
    )
    p = tmp_path / "schema.yaml"
    p.write_bytes(data)
    verify_release_signature(p)  # must not raise


def test_unsupported_envelope_is_skipped_not_failed(tmp_path, chain):
    """general/primitives/cic-primitives carries release.envelope: 2 from
    a different signing tool -- verify_release_signature must raise the
    distinguishable UnsupportedSignatureEnvelopeError, not a plain
    SignatureVerificationError, so callers can bucket it as skipped."""
    p = tmp_path / "bundle.yaml"
    p.write_text(
        "metadata:\n  name: X\nspec:\n  kind: bundle\n"
        "release:\n  envelope: 2\n  build_hash: whatever\n  sign: vault:v1:whatever\n"
        "cic_countersign:\n  authority: {}\n"
    )
    with pytest.raises(UnsupportedSignatureEnvelopeError):
        verify_release_signature(p)
    # and it IS a SignatureVerificationError too, for callers that only
    # care about "did this verify" without caring about the reason
    with pytest.raises(SignatureVerificationError):
        verify_release_signature(p)
