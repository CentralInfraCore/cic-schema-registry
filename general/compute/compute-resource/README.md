# ComputeResource

**Réteg:** `general/compute/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition`

Egységes compute erőforrás — hypervisor VM, bare metal fizikai szerver és cloud instance egyaránt leírható. A paradigma (vm/physical/cloud) az adapter és az address rétegben van, nem a config_surface-ben. Az adapter deklarálja a támogatott capability-ket.

**⚠ `identity.base` egyelőre nincs verzió-pinnelve** (`"cic:core:ManagedEntity"`,
nem `"cic:core:ManagedEntity@v0.2.0"`) — ez az eredeti, `cic-primitives`-ból
örökölt, git-merge-alapú konvenció. A registry új, explicit-pin szabálya
(`proposals/schema-registry` §4) még nem lett rávezetve erre a fájlra —
emiatt a `registry.validate` base-chain coverage ellenőrzése egyelőre NEM fut
le rá (a check kihagyja a `@v`-t nem tartalmazó `base` mezőket). Külön
feladat, nem ennek a migrációnak a része.

---

## Eredet / provenance

Ez a séma a `cic-compute` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`compute/@v0.2.3` release**-ből — az eredeti fájl (schemas/domain/compute-resource.yaml)
byte-azonos tartalma, egyetlen ponton módosítva: `metadata.version` a release
tényleges verziójára (`v0.2.3`) lett állítva. A release bundle-ben ehhez a
fájlhoz tartozó `meta_hash`: `gjUwc9OEMBoo2Gi4qYrb8Wuky4/OA8zXziRpsVlLQv8=`.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a `cic-compute` repó saját, valódi aláírt
release-én (`compute/@v0.2.3` tag) keresztül ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
