# ietf-interfaces-logical

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.0.dev}`

Logikai interfész (pl. VLAN sub-interface, loopback) — az RFC 8343
`ietf-interfaces-base` közös mezőit kiterjeszti, exact-version-pinnelt
`extends` mezővel. Lásd `../ietf-interfaces-base/README.md` a
kiterjesztési mechanizmus és a `registrylib`-rés részleteiért.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-interfaces-
logical.yaml`), `metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen
ellenőrzött, kettős aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.4` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.4 — lower_layer_if/higher_layer_if origin javítva ([#46](https://github.com/CentralInfraCore/cic-schema-registry/issues/46))

`config.lower_layer_if`/`config.higher_layer_if` eddig `origin: rfc8343`
volt. Az RFC 8343 §3.3 (Interface Layering) ténylegesen ellenőrizve
(`rfc-editor.org/rfc/rfc8343.txt`): "There is no generic mechanism for
how an interface is configured to be layered on top of some other
interface. It is expected that interface-type-specific models define
their own data nodes for interface layering." Az RFC saját generikus
`higher-layer-if`/`lower-layer-if` leaf-listái READ-ONLY (`config false`)
állapot-nézetek, nem konfigurálható mezők. A generikus, írható változat
itt (egy közös `logical` building block minden altípusnak, típusonkénti
saját config helyett) CIC egyszerűsítés — most `origin: cic-extension`
jelöléssel.
