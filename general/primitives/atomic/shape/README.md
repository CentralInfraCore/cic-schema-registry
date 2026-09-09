# Shape

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive describing data structure — what fields exist and what types they have. Shape defines how a config or state node looks from a data-structure perspective. All ConfigSurface.nodes and StateSurface.nodes are composed of Shape atoms.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből (`meta_hash: P6+S9d1XqvOEBS6G/ioGrHysVFwm29E1nYx0/bCXvqc=` a release
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
