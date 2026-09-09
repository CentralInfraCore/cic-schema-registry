# Access

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive wrapping every Shape value with access control. Two syntactically equivalent representations:
  key: value
  key: {value: value, access: [...], modify: [...], inherit: true, default_injection: null}
The compiler normalizes the short form to the long form by filling in inherited rules. The runtime always evaluates the expanded form.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből — az eredeti fájl (schemas/atomic/access.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.0`) lett állítva (az eredeti fájl a repóban még
fejlesztői placeholder verziót hordozott). A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `CfuKjoXaFAo1kE/RV02rD3lKN6G1KjCn8qAirv6zlC0=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-primitives` repó saját, valódi aláírt
release-én (`primitives/@v0.2.0` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
