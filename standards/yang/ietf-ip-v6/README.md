# ietf-ip-v6

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8344)
**Kind:** `YANGBlock` — önálló, nincs `extends`

IPv6-cím konfiguráció/állapot building block (RFC 8344 — A YANG Data Model
for IP Management). Önálló darab, mint `../ietf-ip-v4/`.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-ip-v6.yaml`),
`metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen ellenőrzött, kettős
aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.4` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.4 — accept_ra origin javítva ([#46](https://github.com/CentralInfraCore/cic-schema-registry/issues/46))

`config.accept_ra` eddig `origin: rfc8344` volt. Ténylegesen ellenőrizve
(`rfc-editor.org/rfc/rfc8344.txt`): a normatív `ietf-ip` YANG-fában nincs
`accept-ra` (vagy hasonló) leaf, és az RFC 8344 §3 kifejezetten kimondja:
"The IP-MIB defines objects to control IPv6 Router Advertisement
messages. The corresponding YANG data nodes are defined in [RFC8022]."
— azaz a Router Advertisement vezérlés az RFC 8022 (routing management)
hatásköre, nem az `ietf-ip`-é. A legközelebbi valódi RFC 8344 mező az
`ipv6/autoconf/create-global-addresses` (SLAAC cím-generálás
engedélyezése), amit ez a boolean CIC-szinten egyszerűsítve fed le — most
`origin: cic-extension` jelöléssel.
