# cic-schema-registry

> Ez nem klasszikus repo. Ez AI-operált séma-registry.
> Emberi belépő: ez a README. AI belépő: `CLAUDE.md` + `ai/ONBOARDING.md`.

A `cic-schema-registry` a CIC ökoszisztéma **konszolidált séma-tárolója** —
minden CIC séma-leírás (atomic/aggregate primitívák, domain-kompozíciók,
szabvány-alapú fragmentek, provider-specifikus leképezések) itt él, egyetlen
repóban, **egy séma = egy fájl** elven.

**Ez a repó leváltja** a korábbi per-domain repókat (`cic-network`,
`cic-compute`, `cic-kubernetes`, `cic-storage`, `cic-yang`, `CIC-Schemas`) —
azok a tartalom átköltöztetése után archiválásra kerülnek. A provider-modulok
**kódja** (pl. `cic-module-oracle-cloud`) NEM ide tartozik, marad a saját
repójában — csak a séma-leírásaik.

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
make validate    # séma validáció — ha ez nem zöld, semmi sem kész
```

---

## Kapcsolódó repók

| Repo | Kapcsolat |
|---|---|
| `base-repo` | upstream — `schema-registry` flavor branch, `git remote base` |
| `cic-primitives` | a tervezési döntések forrása (`proposals/schema-registry`) |
| `cic-network`/`cic-compute`/`cic-kubernetes`/`cic-storage`/`cic-yang` | migráció forrása — tartalmuk ide költözik, majd archiválásra kerülnek |
| `CIC-Schemas` | migráció forrása (pl. PostgreSQL séma-fragmentek → `standards/postgresql/`) |
| `cic-module-oracle-cloud` és jövőbeli provider-modulok | a `providers/` rétegben leírt sémák megvalósítói, `cic:provider` WASM ABI-n keresztül |
| `CIC-Relay` | runtime — a provider-modulokat futtatja a registry sémái ellen |

---

## Aktuális állapot

| Elem | Státusz | Megjegyzés |
|---|---|---|
| Repó bootstrap (`base` remote, `schema-registry@0.1.0` merge) | **defined** | |
| `general/`/`standards/`/`providers/` könyvtárstruktúra | **defined** | egyelőre üres (`.gitkeep`) |
| Tényleges séma-tartalom migrálása | **not implemented** | a per-domain repókból még nem történt átköltöztetés |
| `tools/compiler.py` kiterjesztése (base-chain coverage-check, major-verzió-szabályok, fájlonkénti aláírás) | **not implemented** | jelenleg az örökölt, bundle-alapú `compiler.py`/`infra.py` fut |
| `renovate.json` egyedi manager a `base:`/`reference_target:` pin-ekhez | **not implemented** | |
| CI (`.github/workflows/ci.yml`) a registry-specifikus szabályokra | **not implemented** | jelenleg az örökölt base-repo CI fut |
