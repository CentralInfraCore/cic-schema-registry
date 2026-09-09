# vault-mtls-client

Small, stdlib-only Go helper: completes a full mTLS handshake with the
`cic-countersign` service and posts a countersign request, where **the
raw Vault Transit private key never touches this process** — both the
TLS `CertificateVerify` signature and the request's own `sign` field are
produced by calling Vault Transit's `/transit/sign` endpoint through a
custom `crypto.Signer`.

Used by `tools/registry_sign.py` (via `tools/registrylib/signing.py`) for
the CICSourceCA-countersignature leg of per-file signing
(proposals/schema-registry §5). Python's `ssl` module has no clean way to
back a TLS client certificate with a signer callback instead of a raw key
file — this is the one operation deliberately delegated to Go rather than
reimplemented.

## Build

```bash
go build -o ../bin/vault-mtls-client .
```

## Environment variables it reads (set by registry_sign.py)

`DEV_VAULT_ADDR`, `DEV_VAULT_TOKEN`, `DEV_VAULT_CA_FILE`,
`DEV_VAULT_KEY_NAME`, `SIGNER_CERT_FILE`, `COUNTERSIGN_ADDR`,
`COUNTERSIGN_CA_FILE`, `BUILD_HASH`, `DOCUMENT_JSON`, `WORKFLOW`.
