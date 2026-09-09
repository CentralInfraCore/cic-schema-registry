# ConfigSurface

**Réteg:** `general/primitives/aggregate/` — aggregate primitív (surface/kompozíció)
**Kind:** `AggregatePrimitive`

The writable desired-state surface of a ManagedEntity. All configuration changes arrive through this surface — it is the desired state container.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből (`meta_hash: ns/EvKhtlPqGtK3H8nirLYYoiyx1Z3VqW3RPogvSOZs=` a release
bundle-ben — ez a hash igazolja, hogy ez a fájl tartalmilag megegyezik azzal,
amit a release aláírt).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a fenti `meta_hash`-en és a `cic-primitives`
repó saját, valódi aláírt release-én (`primitives/@v0.2.0` tag) keresztül
ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
