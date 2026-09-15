# ietf-lldp

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (IEEE 802.1ABcu-2021)
**Kind:** `YANGBlock` — önálló, nincs `extends`

LLDP (Link Layer Discovery Protocol) building block. **⚠ 2026-09-15-ig
tévesen `RFC 8516`-ra hivatkozott** — az egy CoAP hibakód ("Too Many
Requests"), sosem volt LLDP forrás. A valódi forrás IEEE 802.1ABcu-2021
(modul: `ieee802-dot1ab-lldp`), javítva `#42`-ben. Önálló darab, mint
`../ietf-ip-v4/`/`../ietf-ip-v6/`.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-lldp.yaml`),
`metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen ellenőrzött, kettős
aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.4` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).
