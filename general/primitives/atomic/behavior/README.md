# Behavior

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive describing an executable operation on an entity. Behavior defines what interactions are possible between the management plane and the entity beyond config/state read-write. OperationSurface.operations is composed of Behaviors.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből — az eredeti fájl (schemas/atomic/behavior.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.0`) lett állítva (az eredeti fájl a repóban még
fejlesztői placeholder verziót hordozott). A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `y2S1NS6Y4AiMiHhKoSQTxP/KzKv2dfaXu2Fx0Bw0dIM=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-primitives` repó saját, valódi aláírt
release-én (`primitives/@v0.2.0` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
