# cloud-provider-adapter

**Réteg:** `general/compute/` — adapter kontraktus
**Kind:** `AdapterContract`

Cloud provider adapter interface contract — ComputeResource (backend: cloud) runtime kötése. Bármely cloud provider implementálhatja. Ez NEM implementáció — ez az interface amit minden cloud provider adapternek teljesítenie kell.

---

## Eredet / provenance

Ez a séma a `cic-compute` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`compute/@v0.2.3` release**-ből — az eredeti fájl (schemas/adapters/cloud-provider-adapter.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.3`) lett állítva. A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `mbkzSjiMUGXXCtNO7TM0JlX5rZMlgofcVfgPNz0OAAE=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-compute` repó saját, valódi aláírt
release-én (`compute/@v0.2.3` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
