"""Cryptographic verification of a signed schema file's `release:`/
`cic_countersign:` blocks (#102) -- the trust chain `resolve_pin()` and
every `base`/`extends`/(future) `reference_target` pin ultimately relies
on. A file carrying these blocks is not, by itself, trustworthy: this
module is what actually proves the claim, rather than just checking
presence.

Verifies, for one signed file:

  1. `release.build_hash` matches the file's actual content -- the raw
     bytes BEFORE the top-level `release:` key, i.e. exactly what
     compute_build_hash (signing.py) hashed before the signature blocks
     were appended (tools.registrylib.signing.append_signature_blocks
     always appends at the end, never touching what came before --
     #91's fix made that a hard byte-level guarantee).
  2. `release.sign` is a valid ECDSA signature over that build_hash's
     raw digest, verified with the public key embedded in
     `release.createdBy.certificate`.
  3. `cic_countersign.sign` is a valid ECDSA signature over the same
     digest (`cic_countersign.signed_payload` must say "build_hash"),
     verified with the public key in
     `cic_countersign.authority.certificate`.
  4. That authority certificate actually chains to the CIC Root CA
     embedded in `cic_countersign.authority.root_certificate` -- not
     just string-matched, but verified as a real X.509 signature
     (issuer's public key over the child certificate's TBS bytes).

Deliberately OUT of scope (proposals/schema-registry's own documented
gap, and #102's stated scope): certificate expiry/revocation, and the
AUTHOR certificate's own issuer chain (only the countersign authority's
chain to the root is checked here). Both would be separate follow-ups,
not silently assumed.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

import yaml
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils


class SignatureVerificationError(Exception):
    """Raised when a signed schema file's release/cic_countersign blocks
    fail cryptographic verification -- a wrong build_hash, an invalid
    signature, or a countersign authority that doesn't actually chain to
    the embedded root certificate. Never returned as a bare False: a
    trust failure is always an explicit, named error."""


class UnsupportedSignatureEnvelopeError(SignatureVerificationError):
    """Raised for a release: block that carries an `envelope` field --
    this module only understands the plain per-file convention
    tools.registrylib.signing/registry_sign.py produces (build_hash over
    the raw bytes preceding the top-level 'release:' key, no envelope
    marker). A versioned `envelope` means the file was signed by a
    DIFFERENT tool under a different hash-boundary convention -- e.g.
    general/primitives/cic-primitives's kernel bundle, which carries
    `release.envelope: 2` and comes from the separate cic-primitives/
    base-repo release pipeline (no code under tools/ in this repo ever
    writes an `envelope` key), not from this registry's own signer. That
    is a real, structural difference, not the file lying about its
    authenticity -- this is deliberately NOT a plain
    SignatureVerificationError so callers can bucket it as
    unsupported/skipped rather than a genuine trust failure, matching
    registry_validate.py's existing "SKIPPED, not silently OK, not
    falsely FAILED" convention for other not-yet-implemented shapes."""


# Vault Transit signs with the key's CURRENT version by default (see
# cic-schema-registry#104) -- "vault:v1:", "vault:v2:", etc.
_VAULT_SIG_RE = re.compile(r"^vault:v\d+:")

# release: is always the first of the two top-level keys
# append_signature_blocks (signing.py) appends, and -- because it's a
# top-level YAML key -- can only start a line at column 0. Everything
# before that line is exactly the bytes compute_build_hash hashed.
_RELEASE_KEY_RE = re.compile(rb"(?m)^release:")

_PEM_CERT_RE = re.compile(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL
)


def _signed_content_bytes(raw: bytes, path: Path) -> bytes:
    """The file's bytes before the top-level `release:` key -- what was
    actually hashed into build_hash before signing."""
    m = _RELEASE_KEY_RE.search(raw)
    if m is None:
        raise SignatureVerificationError(
            f"{path}: no top-level 'release:' key found -- file is not signed"
        )
    return raw[: m.start()]


def _decode_vault_signature(vault_sig: object, context: str) -> bytes:
    if not isinstance(vault_sig, str):
        raise SignatureVerificationError(f"{context}: signature is not a string")
    m = _VAULT_SIG_RE.match(vault_sig)
    if not m:
        raise SignatureVerificationError(
            f"{context}: unrecognized signature format {vault_sig!r} "
            "(expected 'vault:vN:...')"
        )
    try:
        return base64.b64decode(vault_sig[m.end() :], validate=True)
    except (ValueError, TypeError) as e:
        raise SignatureVerificationError(
            f"{context}: signature is not valid base64: {e}"
        ) from e


def _load_cert(pem_text: object, context: str) -> x509.Certificate:
    if not isinstance(pem_text, str) or "BEGIN CERTIFICATE" not in pem_text:
        raise SignatureVerificationError(f"{context}: missing/invalid certificate")
    try:
        return x509.load_pem_x509_certificate(pem_text.encode("utf-8"))
    except ValueError as e:
        raise SignatureVerificationError(
            f"{context}: certificate does not parse: {e}"
        ) from e


def _verify_prehashed_ecdsa(
    digest: bytes, vault_sig: object, cert_pem: object, context: str
) -> None:
    sig_der = _decode_vault_signature(vault_sig, context)
    cert = _load_cert(cert_pem, context)
    public_key = cert.public_key()
    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise SignatureVerificationError(
            f"{context}: certificate public key is not an EC key "
            f"({type(public_key).__name__})"
        )
    try:
        public_key.verify(
            sig_der, digest, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256()))
        )
    except InvalidSignature as e:
        raise SignatureVerificationError(f"{context}: signature does not verify") from e


def _extract_embedded_pem(text: object, context: str) -> str:
    if not isinstance(text, str):
        raise SignatureVerificationError(f"{context}: not a string")
    m = _PEM_CERT_RE.search(text)
    if not m:
        raise SignatureVerificationError(
            f"{context}: no embedded '-----BEGIN CERTIFICATE-----' block found"
        )
    return m.group(0)


def _verify_chain_to_root(
    child_cert: x509.Certificate, root_pem: str, context: str
) -> None:
    root_cert = _load_cert(root_pem, context)
    if child_cert.issuer != root_cert.subject:
        raise SignatureVerificationError(
            f"{context}: certificate issuer does not match the embedded "
            "root certificate's subject"
        )
    root_public_key = root_cert.public_key()
    if not isinstance(root_public_key, ec.EllipticCurvePublicKey):
        raise SignatureVerificationError(
            f"{context}: root certificate public key is not an EC key "
            f"({type(root_public_key).__name__})"
        )
    hash_algorithm = child_cert.signature_hash_algorithm
    if hash_algorithm is None:
        raise SignatureVerificationError(
            f"{context}: certificate does not declare a signature hash algorithm"
        )
    try:
        root_public_key.verify(
            child_cert.signature,
            child_cert.tbs_certificate_bytes,
            ec.ECDSA(hash_algorithm),
        )
    except InvalidSignature as e:
        raise SignatureVerificationError(
            f"{context}: certificate is not actually signed by the "
            "embedded root certificate"
        ) from e


def verify_release_signature(path: Path) -> None:
    """Raises SignatureVerificationError if `path`'s release/
    cic_countersign blocks don't cryptographically check out. Returns
    (None) silently on success -- absence of an exception is the only
    "valid" signal, matching the rest of this codebase's fail-loud
    convention (e.g. tools.registrylib.signing.AlreadySignedError)."""
    raw = path.read_bytes()
    try:
        doc = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        raise SignatureVerificationError(f"{path}: does not parse as YAML: {e}") from e

    release = doc.get("release")
    countersign = doc.get("cic_countersign")
    if not isinstance(release, dict):
        raise SignatureVerificationError(f"{path}: missing 'release' block")
    if not isinstance(countersign, dict):
        raise SignatureVerificationError(f"{path}: missing 'cic_countersign' block")
    if release.get("envelope") is not None:
        raise UnsupportedSignatureEnvelopeError(
            f"{path}: release.envelope={release['envelope']!r} -- signed by a "
            "different tool under a different hash-boundary convention "
            "(e.g. the cic-primitives/base-repo release pipeline), not by "
            "this registry's own per-file signer. Not verifiable by this "
            "function; not evidence the file is untrustworthy."
        )

    content = _signed_content_bytes(raw, path)
    actual_hash = base64.b64encode(hashlib.sha256(content).digest()).decode()
    claimed_hash = release.get("build_hash")
    if claimed_hash != actual_hash:
        raise SignatureVerificationError(
            f"{path}: build_hash mismatch -- claimed {claimed_hash!r}, "
            f"actual {actual_hash!r} over the file's content preceding "
            "'release:' (the file's content does not match what was signed)"
        )
    digest = hashlib.sha256(content).digest()

    author_cert_pem = (release.get("createdBy") or {}).get("certificate")
    _verify_prehashed_ecdsa(
        digest, release.get("sign"), author_cert_pem, f"{path}: release.sign"
    )

    authority = countersign.get("authority") or {}
    if countersign.get("signed_payload") != "build_hash":
        raise SignatureVerificationError(
            f"{path}: cic_countersign.signed_payload is "
            f"{countersign.get('signed_payload')!r}, expected 'build_hash' "
            "-- unsupported payload binding"
        )
    authority_cert_pem = authority.get("certificate")
    _verify_prehashed_ecdsa(
        digest,
        countersign.get("sign"),
        authority_cert_pem,
        f"{path}: cic_countersign.sign",
    )

    authority_cert = _load_cert(
        authority_cert_pem, f"{path}: cic_countersign.authority.certificate"
    )
    root_pem = _extract_embedded_pem(
        authority.get("root_certificate") or "",
        f"{path}: cic_countersign.authority.root_certificate",
    )
    _verify_chain_to_root(
        authority_cert, root_pem, f"{path}: cic_countersign.authority chain"
    )
