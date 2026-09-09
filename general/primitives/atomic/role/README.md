# Role

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive describing the management semantics of a node — what this node means from the management plane perspective. Role does not describe the data (that is Shape's job), but how the system handles it: writable, read-only, key, etc. The seven values are NOT one dimension. They fall on three orthogonal axes, and a node carries one value from each axis it uses — see spec.axes.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből — az eredeti fájl (schemas/atomic/role.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.0`) lett állítva (az eredeti fájl a repóban még
fejlesztői placeholder verziót hordozott). A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `cfwYWgv3i3ulezC96n+r2jcKY7XHPeHMRESu6k9nllk=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-primitives` repó saját, valódi aláírt
release-én (`primitives/@v0.2.0` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
