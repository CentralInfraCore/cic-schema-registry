# cic-primitives (kernel)

**Réteg:** `general/primitives/` — a teljes atomic/aggregate primitíva-grammatika,
EGY darab, oszthatatlan alapként.

## Miért egy fájl, nem 13 külön séma

Az első próbálkozás a `cic-primitives` release-t 13 külön fájlra bontotta
(`general/primitives/atomic/shape/`, `.../aggregate/managed-entity/`, stb.) —
ez tévedés volt, visszavonva. A primitíva-réteg (Shape, Role, Behavior,
Contract, Address, Identity, Event, Access + ManagedEntity, ConfigSurface,
StateSurface, OperationSurface, PolicySurface) **nem független, egyenként
verziózható darabokból áll** — ez egy együtt tervezett, együtt kiadott,
egybefüggő grammatika. A `cic-primitives` saját release-folyamata is mindig
EGYETLEN bundle-t ad ki, sosem primitívánként külön-külön release-t.

## Mi ez a fájl

`cic-primitives.v0.2.0-src2026.yaml` — **byte-azonos** másolata a valódi,
CICSourceCA-ellenjegyzett release-nek:
<https://github.com/CentralInfraCore/cic-primitives/blob/primitives/releases/v0.2.0/release/cic-primitives-v0.2.0.yaml>
(tag: `primitives/@v0.2.0`). Semmi nem lett hozzáadva, elvéve vagy módosítva —
ez a fájl már eleve hordozza a saját `release.sign` + `cic_countersign`
blokkját, valódi aláírással.

## Ha változtatni kell rajta

**Ez nem itt szerkesztendő.** A `cic-primitives` a forrás-repó — egy új
primitíva, vagy egy meglévő módosítása ott, a `cic-primitives` saját
issue → branch → PR → release folyamatán megy át. Amikor ott elkészül egy új
release (pl. `v0.2.1` vagy `v0.3.0`), az az új release **egy ÚJ fájlként**
kerül ide (`cic-primitives.v0.2.1-src2026.yaml` stb.) — a `v0.2.0` fájl
változatlanul megmarad, verzió-történetként.

## Ismert, nyitott pont

A `tools/registrylib` jelenlegi feloldó mechanizmusa (`build_type_index`)
egy-séma-egy-fájl modellre épül — egy `PrimitiveRelease`-alakú bundle-fájl
belsejébe (a `specs[]` tömbbe) még nem lát bele, tehát pl. egy
`base: "cic:core:ManagedEntity@v0.2.0"` pin egyelőre NEM oldható fel erre a
fájlra. Ez egy külön, tervezett follow-up (lásd `registry_validate.py`
kommentjeit) — amíg nincs megoldva, `registry_validate` explicit jelzi és
kihagyja ezt a fájlt, nem hamis-zölddel megy át rajta.
