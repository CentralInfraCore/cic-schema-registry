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

## Kriptográfiai ellenőrzés — valóban elvégezve

A `release.sign` (Vault Transit, a szerző kulcsával) és a `cic_countersign.sign`
(CICSourceCA) aláírást **ténylegesen, `openssl`-lel** ellenőriztük a beágyazott
tanúsítványok ellen, mindkettő a `release.build_hash` felett — mindkettő
**`Signature Verified Successfully`**. Ez tehát valóban érvényes, kettős
aláírású artifact, nem csak struktúra alapján feltételezett.

## ⚠ A kernel maga sem teljes — 3 placeholder slot a ManagedEntity-ben

Mielőtt bárki erre a fájlra mint lezárt, kész alapra hivatkozik: a
`ManagedEntity` aggregate 8 slotja közül **3 explicit placeholder**, nem kész:

| Slot | Státusz | Blokkolva |
|---|---|---|
| `notification_surface` | `placeholder`, `type: Event[]` | NotificationSurface aggregate — nincs modell (notification routing előfeltétel hiányzik) |
| `capability_surface` | `placeholder`, `type: TBD` | CapabilitySurface aggregate — nincs modell (Relay capability declaration rendszer előfeltétel hiányzik) |
| `lifecycle_surface` | `sealed`, `type: TBD` | LifecycleSurface aggregate — nincs modell (Relay execution model előfeltétel hiányzik) |

Ez **nem hiba** — a forrásban is explicit, dokumentált, tudatos hiány (a
háromszintű státusz-elv szerint: `concept`, nem `implemented`). De aki innen
származtat (bármelyik domain composition, pl. `StorageResource`,
`ComputeResource`), **örökli ezt a három hiányt** — ha egy domain-objektumnak
valódi lifecycle- vagy capability-modellje kellene, azt ez a kernel jelenleg
NEM tudja adni. Ezt a kernel bármelyik jövőbeli fogyasztójánál explicit
figyelembe kell venni, nem hallgatólagosan feltételezni, hogy "a ManagedEntity
teljes".

## Ismert, nyitott pont

A `tools/registrylib` jelenlegi feloldó mechanizmusa (`build_type_index`)
egy-séma-egy-fájl modellre épül — egy `PrimitiveRelease`-alakú bundle-fájl
belsejébe (a `specs[]` tömbbe) még nem lát bele, tehát pl. egy
`base: "cic:core:ManagedEntity@v0.2.0"` pin egyelőre NEM oldható fel erre a
fájlra. Ez egy külön, tervezett follow-up (lásd `registry_validate.py`
kommentjeit) — amíg nincs megoldva, `registry_validate` explicit jelzi és
kihagyja ezt a fájlt, nem hamis-zölddel megy át rajta.
