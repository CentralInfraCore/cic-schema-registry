# ManagedEntity

**Réteg:** `general/primitives/aggregate/` — aggregate primitív (surface/kompozíció)
**Kind:** `AggregatePrimitive`

The base compositional unit of CIC — every domain object specializes from this. Not a standalone object: it is the semantic contract on which switch interfaces, kubernetes pods, databases, services, and anything else are built. The object is always a consequence, never a starting point.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből — az eredeti fájl (schemas/aggregate/managed-entity.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.0`) lett állítva (az eredeti fájl a repóban még
fejlesztői placeholder verziót hordozott). A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `M5ZSUt6GK7DI3ASFrUe5gnMqGJVDg3kuaf3BzULXC94=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-primitives` repó saját, valódi aláírt
release-én (`primitives/@v0.2.0` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
