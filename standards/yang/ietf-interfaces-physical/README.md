# ietf-interfaces-physical

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.1.4}`

Fizikai interfész (pl. switch/router port) — az RFC 8343
`ietf-interfaces-base` közös mezőit kiterjeszti. Lásd
`../ietf-interfaces-base/README.md` a kiterjesztési mechanizmus és a
`registrylib`-rés részleteiért.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-interfaces-
physical.yaml`), `metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen
ellenőrzött, kettős aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.4` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén). A `v0.1.5`, `v0.1.6` és `v0.1.7` (LATEST, lásd lent) szintén
valódi Vault author-aláírással és CICSourceCA ellenjegyzéssel van
ellátva.

## v0.1.5 — speed/duplex origin javítva ([#46](https://github.com/CentralInfraCore/cic-schema-registry/issues/46))

`config.speed`/`config.duplex` eddig `origin: rfc8343` volt. Ténylegesen
ellenőrizve (`rfc-editor.org/rfc/rfc8343.txt`): az RFC 8343 normatív base
modulban a `speed` leaf READ-ONLY (`config false`, "An estimate of the
interface's current bandwidth"), nem konfigurálható; a konfigurálható
`speed`/`duplex` pár kizárólag az RFC A. függelékének nem-normatív,
illusztratív `ethernet` példamoduljában jelenik meg (`namespace
http://example.com/ethernet`), nem magában az `ietf-interfaces` modulban.
Mindkét mező most `origin: cic-extension`. A `state.speed_actual`
megtartja az `rfc8343` origint — az az RFC saját READ-ONLY `speed`
leaf-jének (`ifSpeed`/`ifHighSpeed`) valódi megfelelője.

**Ez a lelet a `#63`-ban javítva lett — lásd lent.**

## v0.1.6 — state.duplex_actual és notifications origin javítva ([#63](https://github.com/CentralInfraCore/cic-schema-registry/issues/63))

`state.duplex_actual` és a `notifications: link-up`/`link-down` eddig
szintén `origin: rfc8343`-mal voltak jelölve. Ugyanaz az RFC 8343-szöveg
(`rfc-editor.org/rfc/rfc8343.txt`), amit a `v0.1.5`/`#46` javításakor már
ellenőriztem: a normatív base modulban nincs `duplex` leaf sehol (csak a
nem-normatív A. függelék illusztratív `ethernet` példamoduljában), és
nincs YANG `notification` definíció sem — csak egy
`link-up-down-trap-enable` SNMP trap-vezérlő config leaf, ami nem YANG
notification statement. Mindhárom mező most `origin: cic-extension`.

## v0.1.7 — extends.version valós pin ([#81](https://github.com/CentralInfraCore/cic-schema-registry/issues/81))

Az `extends.version` eddig `v0.0.dev` placeholder volt. Most valós pin:
`ietf-interfaces-base@v0.1.4`, amit a `check_yang_extends()` már
ténylegesen `resolve_pin()`-nel ellenőriz.
