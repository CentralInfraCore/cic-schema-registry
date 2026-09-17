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

Fájlonkénti release-aláírás: `v0.1.4`, `v0.1.5` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.5 — lldp_neighbors kompozit kulcs ([#86](https://github.com/CentralInfraCore/cic-schema-registry/issues/86))

`lldp_neighbors` korábban csak `chassis_id`-t jelölte kulcsnak — ütközött,
ha egy switch több portja csatlakozott ugyanahhoz a szomszéd chassishoz
(pl. LAG/MLAG). `port_id` is `role: key` most, kompozit kulcs
(`chassis_id` + `port_id`). A `chassis_id_subtype`/`port_id_subtype`
(IEEE 802.1AB szerinti subtype-tagged azonosítók) szándékosan nincs
ebben a verzióban — nagyobb modellezési kérdés, külön mérlegelendő.

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
