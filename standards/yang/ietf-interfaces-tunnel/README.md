# ietf-interfaces-tunnel

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.1.4}`

Tunnel interfész (pl. GRE, IPsec, VXLAN) — az RFC 8343
`ietf-interfaces-base` közös mezőit kiterjeszti. Lásd
`../ietf-interfaces-base/README.md` a kiterjesztési mechanizmus és a
`registrylib`-rés részleteiért.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-interfaces-
tunnel.yaml`), `metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen
ellenőrzött, kettős aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.4`, `v0.1.5` a
`tools/registry_sign.py` (proposals/schema-registry §5) szerint valódi
Vault author-aláírással és CICSourceCA ellenjegyzéssel van ellátva
(`release:`/`cic_countersign:` blokk a fájl végén).

## v0.1.5 — extends.version valós pin ([#81](https://github.com/CentralInfraCore/cic-schema-registry/issues/81))

Az `extends.version` eddig `v0.0.dev` placeholder volt. Most valós pin:
`ietf-interfaces-base@v0.1.4`, amit a `check_yang_extends()` már
ténylegesen `resolve_pin()`-nel ellenőriz.

## v0.1.6 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
