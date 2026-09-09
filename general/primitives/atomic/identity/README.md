# Identity

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive describing type identity — not instance identification, but describing WHAT this entity is in the CIC model. Identity defines an entity's type, namespace, version, and inheritance chain. Analogous to YANG identity/identityref, but more general and versioned.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből (`meta_hash: o5V83SYNs9JowwFIFXGaXBqBfawKd/oo1Fs9wK2i5QI=` a release
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
