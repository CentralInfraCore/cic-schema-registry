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

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
