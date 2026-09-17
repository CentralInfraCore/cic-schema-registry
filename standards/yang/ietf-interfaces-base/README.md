# ietf-interfaces-base

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `abstract: true`

## Mit ír le

Az RFC 8343 (A YANG Data Model for Interface Management) közös interfész
building block-ja — minden RFC 8343 interfész-típus (physical, logical,
tunnel, vlan) örökli ezeket a mezőket. **A forrás saját maga mondja ki:
`abstract: true`, "nem használható önállóan — mindig egy konkrét interfész
blokk kiterjeszti".**

## Fontos felismerés — ez már MOST is exact-version-pin-elt kiterjesztés

A `ietf-interfaces-logical`/`physical`/`tunnel`/`vlan` mindegyike egy
`extends: {name: ietf-interfaces-base, version: v0.0.dev}` mezővel
hivatkozik erre a fájlra — **ez már a forrásban is pontos verzióra pinnelt
kiterjesztés**, nem csak névhivatkozás. Ez egy más YANGBlock-dialektusban
(nem a `DomainComposition`/`identity.base` mechanizmusunkban) létező,
hasonló mintázat — megerősíti, hogy az exact-version-pin gondolat nem
öncélú találmány, hanem már máshol is bevált gyakorlat ebben az
ökoszisztémában.

**⚠ Ismert, nem megoldott rés:** a `tools/registrylib` jelenlegi
coverage-mechanizmusa (`identity.base`/`reference_target`) **nem ismeri**
a `YANGBlock.extends` mezőt — ez egy külön séma-dialektus (nem
`DomainComposition`), amit a `registrylib` jelenleg egyáltalán nem
vizsgál. Ez azt jelenti, hogy ha a `ietf-interfaces-base` valaha mezőt
veszítene/mutálna, azt a mi mechanizmusunk **nem venné észre** — ez egy
valós, dokumentált, nem-e-migráció-részeként-megoldott hiányosság, nem
csendben elhallgatva.

Ez a réteg (`abstract`+`extends`) máshogy néz ki, mint a `general/storage/`
és `general/compute/` laza, cím-alapú kapcsolatai — itt egy valódi,
struktúrális öröklési lánc van, csak egy másik dialektusban kifejezve.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-yang` repó `yang/@v0.1.3` tag-jéből
(`schemas/ietf/ietf-interfaces-base.yaml`), `metadata.version` a release
verziójára (`v0.1.3`) állítva. **Ténylegesen, `openssl`-lel ellenőrizve**:
szerzői Vault Transit aláírás + CICSourceCA ellenjegyzés a `build_hash`
felett, mindkettő érvényes, ugyanaz a 2026-os CA-lánc, mint minden korábbi
migrációnál. Itt (ellentétben a `cic-kubernetes` esettel) a legfrissebb
tag (`v0.1.3`) MÁR rendben, teljes kettős aláírással rendelkezik.

Fájlonkénti release-aláírás: `v0.1.4` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.4 — mtu origin javítva ([#46](https://github.com/CentralInfraCore/cic-schema-registry/issues/46))

A `config.mtu` mezőnek eddig egyáltalán nem volt `origin` mezője, miközben
a fájl `source`/`tags` szinten RFC 8343-ra hivatkozik. Az RFC 8343 §4
(Design) kifejezetten kimondja, hogy az `ifMtu` objektum NINCS leképezve
az `ietf-interfaces` modulra — az MTU-t interfésztípus-specifikus
modulokra hárítja (ami valójában az RFC 8344 `ietf-ip` cím-család-szintű
`mtu` leafjeiben jelenik meg). A generikus `mtu` itt CIC normalizáció
(egy interfész-szintű kényelmi egyszerűsítés), most `origin: cic-extension`
jelöléssel. Az RFC-szöveg ténylegesen ellenőrizve (`rfc-editor.org/rfc/rfc8343.txt`),
nem feltételezés alapján.

## v0.1.5 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
