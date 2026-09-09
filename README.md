# cic-schema-registry

> Ez nem klasszikus repo. Ez AI-operált séma-registry.
> Emberi belépő: ez a README. AI belépő: `CLAUDE.md` + `ai/ONBOARDING.md`.

A `cic-schema-registry` a CIC ökoszisztéma **konszolidált séma-tárolója** —
minden CIC séma-leírás (atomic/aggregate primitívák, domain-kompozíciók,
szabvány-alapú fragmentek, provider-specifikus leképezések) itt él, egyetlen
repóban, **egy séma = egy fájl** elven.

**Ez a repó leváltja** a korábbi per-domain repókat (`cic-network`,
`cic-compute`, `cic-kubernetes`, `cic-storage`, `cic-yang`) — tartalmuk
átköltözött, a repók archiválva. (`CIC-Schemas` más témájú, tartalma NEM lett
migrálva.) A provider-modulok **kódja** (pl. `cic-module-oracle-cloud`) NEM
ide tartozik, marad a saját repójában — csak a séma-leírásaik.

A teljes tervezési dokumentáció: `cic-primitives` repó,
`proposals/schema-registry/README.md`.

---

## Három réteg

| Réteg | Mit jelent | Példa |
|---|---|---|
| `general/` | Provider-független, absztrakt fogalom — MIT akarunk | `general/storage/storage-resource/` |
| `standards/` | Külső szabvány/kvázi-szabvány szerinti séma | `standards/yang/ietf-interfaces-base/` |
| `providers/` | Konkrét szolgáltató/implementáció leképezése | `providers/oracle-cloud/object-storage-bucket/` |

Minden séma saját könyvtárat kap:

```
general/storage/storage-resource/
  README.md                                    # egy, folyamatosan frissülő emberi doksi
  storage-resource.v1.0.0-src2026.yaml
```

`<schema-name>.vMAJOR.MINOR.PATCH-src<év>.yaml` — a `-src<év>` az aláíró CIC
Root CA évjárata (a Root CA naptári évenként rotálódik), NEM tartalmi
élettartam. Nincs külön index/katalógus fájl — a könyvtárlistázás a keresés.

---

## Származtatás és aláírás — a lényeg dióhéjban

- `identity.base` / `reference_target` PONTOS tartalmi verzióra pin-el
  (`@v1.0.0`) — a `-src` évet a feloldás automatikusan a legfrissebb érvényes
  aláírásra követi.
- Minden szülő-mezőnek explicit meg kell jelennie a leszármazottban
  (implementálva vagy `conformance: not_implemented`) — nincs csendes
  átsiklás egy új szülő-mezőn.
- Ugyanazon MAJOR verzión belül mező nem törölhető, típusa/kontraktusa nem
  mutálódik helyben — csak MAJOR verzió-váltáskor.
- **Nincs bundle-release.** Minden fájl a saját, önálló, aláírt egysége
  (Vault Transit + CICSourceCA ellenjegyzés, közvetlenül a fájlban).
- Fejlesztés: issue → ideiglenes branch → PR → merge (a merge váltja ki az
  aláírást). Elévülés-kezelés: Renovate (git-tag-alapú datasource).

Részletek, indoklás, nyitott kérdések: `cic-primitives`
`proposals/schema-registry/README.md`.

---

## Gyors start

```bash
make validate            # örökölt bundle-check — jelenleg placeholder, nem validál érdemben
make registry.validate   # base-chain coverage + verzió-evolúció — valódi, de lásd korlátait lent
```

---

## Kapcsolódó repók

| Repo | Kapcsolat |
|---|---|
| `base-repo` | upstream — `schema-registry` flavor branch, `git remote base` |
| `cic-primitives` | a tervezési döntések forrása (`proposals/schema-registry`) |
| `cic-network`/`cic-compute`/`cic-kubernetes`/`cic-storage`/`cic-yang` | migráció forrása — tartalmuk átköltözött, **mind archivált** |
| `CIC-Schemas` | más témájú, tartalma **NEM** lett migrálva, nincs archiválva |
| `cic-module-oracle-cloud` és jövőbeli provider-modulok | a `providers/` rétegben leírt sémák megvalósítói, `cic:provider` WASM ABI-n keresztül |
| `CIC-Relay` | runtime — a provider-modulokat futtatja a registry sémái ellen |

---

## Aktuális állapot

| Elem | Státusz | Megjegyzés |
|---|---|---|
| Repó bootstrap (`base` remote, `schema-registry@0.1.0` merge) | **defined** | |
| `general/`/`standards/`/`providers/` könyvtárstruktúra | **defined** | |
| Séma-tartalom migrálása (kernel + 5 domain, 26 fájl) | **defined** | `cic-primitives`/`cic-compute`/`cic-storage`/`cic-kubernetes`/`cic-network`/`cic-yang`-ból; forrás-repók archiválva; `providers/` még üres |
| `tools/registrylib/` (base-chain coverage, verzió-evolúció, kernel-identitás feloldás) + `registry_validate.py` CLI | **defined** | additív az örökölt `compiler.py`/`infra.py`-hoz, azt NEM helyettesíti; a jelenlegi corpuson 0 verzióátmenet fut le; az 5 domain-kompozíció `base:`-je pontos verzióra pin-el és fel is oldódik a kernel bundle-be, de a kernel `slots`/`fields`-alapú (nem surface node-lista), így a mezőkompatibilitás ellene EXPLICIT SKIPPED, nem lefutó check — lásd alul |
| Örökölt `tools/compiler.py validate` (`run_validation()`) | **not implemented** | placeholder — betölt és logol, nem validál érdemben |
| Fájlonkénti aláírás (`registry_sign.py` + `signing.py` + `vault-mtls-client`) | **defined**, élő teszttel bizonyítva | **de a 26 migrált fájl közül 1 van aláírva** (a `cic-primitives` bundle eredeti, forrásból hozott aláírása) — a `registry_sign.py` a másik 25-re még nem lett lefuttatva |
| `renovate.json` egyedi manager a `base:`/`reference_target:` pin-ekhez | **not implemented** | |
| CI (`.github/workflows/ci.yml`) a registry-specifikus szabályokra | **defined** | `make validate` + `make registry.validate` (`--min-schemas=20` küszöbbel) most már lépés a workflow-ban — de a trigger továbbra is csak `main`/`master`-re irányuló push/PR, `devel`-en nem fut le |

**Ismert, dokumentált rések a `registry_validate.py`-ban** (mind reprodukálva,
lásd `CLAUDE.md` "Jelenlegi, valódi állapot"):

- **Javítva**: az 5 domain-kompozíció `base:`-je pontos verzióra pin-el
  (`cic:core:ManagedEntity@v0.2.0`), és `tools/registrylib/bundle.py` +
  `identity.py` a kernel bundle `specs[]`-ébe mászva fel is oldja — ez most
  már ténylegesen resolve-ol, és látszik a `SKIPPED` jelentésben (nem
  csendben `continue`-ol tovább, mint korábban). A mezőkompatibilitás a
  kernel ellen viszont még mindig nem fut le, mert a kernel típusai
  `slots`/`fields`-en át írják le magukat, nem surface node-listákon —
  ezt a check explicit, pontos okkal jelzi SKIPPED-ként.
- `reference_target` mezőt semmi nem old fel
- a mező-kompatibilitás surface-öket (config/state/operation/notification)
  összemos, pusztán mezőnév alapján hasonlít — egy mező surface-ek közti
  áthelyezése major-váltás nélkül átmegy
- a `-src<év>` feloldás a legfrissebb évet numerikusan választja,
  tanúsítvány/aláírás-érvényesség ellenőrzése nélkül
