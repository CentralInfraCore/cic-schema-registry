# CIC Schema Registry — Claude kontextus

## Branch szabály — KÖTELEZŐ

**Érdemi fejlesztés kizárólag a `devel` ágon történhet** (ha még nincs
`devel` ág, elsőként azt kell létrehozni `main`-ből).

- `main` — csak merge fogad, közvetlen commit tilos
- `devel` — ez az aktív fejlesztési ág
- fájlonkénti issue-branch-ek (pl. `issue-142-storage-resource-v1.2.0`) — egy
  séma-verzió-változtatásra, PR után törlendő (nem perzisztens ág)

## Mi ez a rendszer

A `cic-schema-registry` a CIC ökoszisztéma **konszolidált séma-tárolója** —
minden séma-leírás (`general/`, `standards/`, `providers/`) itt él, **egy
séma egy fájl** elven, függetlenül verziózva és aláírva.

**Ez a repó leváltja** a per-domain repókat (`cic-network`, `cic-compute`,
`cic-kubernetes`, `cic-storage`, `cic-yang`, `CIC-Schemas`) — azok tartalma
ide migrál, majd azok archiválásra kerülnek. A provider-modulok **kódja**
(pl. `cic-module-oracle-cloud`) NEM ide tartozik.

**A teljes tervezési dokumentáció a `cic-primitives` repóban él**:
`proposals/schema-registry/README.md` — ott van minden döntés indoklása
(miért nincs bundle-release, hogyan működik a `-src<év>` komponens, a
major-verzió-szabályok, a Renovate-alapú elévülés-kezelés). Ezt a fájlt
olvasd el MINDEN érdemi kérdés előtt.

Részletes architektúra ebben a repóban: `ai/SYSTEM_CONTEXT.md`

---

## Boot sequence — minden session elején

1. `mcp__cic-graph__kb_status` — tudásbázis elérhető és friss?
2. Olvasd el: `cic-primitives/proposals/schema-registry/README.md` (ha
   elérhető a workdir-ben) + ennek a repónak az `ai/SYSTEM_CONTEXT.md`-jét
3. Státusz térkép: mi **defined**, mi **not implemented** (lásd README
   "Aktuális állapot" táblázata)

Amíg ez nincs meg, ne tegyél tényállításokat a registry állapotáról.

---

## Háromszintű státusz

| Státusz | Jelentés |
|---|---|
| **defined** | a mechanizmus/könyvtár létezik és le van tesztelve — ez ÖNMAGÁBAN nem jelenti, hogy `make validate`/`make registry.validate` érdemben ellenőrzi is (lásd "Jelenlegi, valódi állapot" a konkrét réseket) |
| **draft** | terv megvan írásban (a `proposals/schema-registry`-ben), kód még nincs |
| **not implemented** | sem terv, sem kód — vagy terv van, de kód szándékosan még nincs |

---

## Jelenlegi, valódi állapot (2026-09-09-i frissítés)

A bootstrap óta a hat elsődleges primitives-group repó tartalma (kernel +
5 domain) migrálva lett — a `general/`/`standards/` könyvtárak **NEM üresek**:

| Réteg | Fájlszám | Forrás |
|---|---:|---|
| `general/primitives/` | 1 (bundle) | `cic-primitives` `primitives/@v0.2.0` |
| `general/compute/` | 4 | `cic-compute` `compute/@v0.2.3` |
| `general/storage/` | 2 | `cic-storage` `storage/@v0.1.2` |
| `general/kubernetes/` | 7 | `cic-kubernetes` `kubernetes/@v0.1.2` |
| `general/network/` | 3 | `cic-network` `network/@v0.4.1` |
| `standards/yang/` | 9 | `cic-yang` `yang/@v0.1.3` |
| `providers/` | 0 | — még nincs provider-modul mapping |

`tools/registrylib/` (`paths.py`, `identity.py`, `coverage.py`) és a hozzá
tartozó `tools/registry_validate.py` CLI **meg vannak írva és tesztelve** —
ez registry-specifikus, additív a `tools/compiler.py`/`tools/infra.py`
örökölt, bundle-alapú logikájához képest (azt NEM helyettesíti).
`tools/registry_sign.py` (+ `tools/registrylib/signing.py` +
`tools/vault-mtls-client/`) is megvan: fájlonkénti, bundle nélküli aláírás
Vault Transit + CICSourceCA ellenjegyzéssel, élő teszttel bizonyítva.

**Ennek ellenére a validáció ma nagyon kevés tényleges garanciát ad — ne
higgy a zöld futásnak félrevezető magabiztossággal:**

- `make validate` (`tools/compiler.py validate` → `run_validation()` a
  `tools/infra.py`-ban) **placeholder** — betölti és logolja a
  `canonical_source_file`-t, de a validációs logika szó szerint
  "to be fully implemented here". Nem érinti a migrált tartalmat.
- `make registry.validate` valódi, de a jelenlegi corpuson **0
  verzióátmenetet ellenőriz** (minden séma pontosan egy tartalmi
  verzióval létezik) és **minden `base:` referenciát csendben átugrik**,
  mert egyik migrált domain-kompozíció sem ír pontos verziót
  (`base: "cic:core:ManagedEntity"`, nem `...@v0.2.0`) — ez az ág még a
  `SKIPPED` jelentésben sem jelenik meg, egyáltalán nincs log róla. A
  `reference_target` mezőt semmi nem oldja fel, csak a docstringben
  szerepel.
- `tools/registrylib/coverage.py` a mezőket surface-től függetlenül,
  pusztán névre lapítja — egy azonos nevű, azonos típusú mező
  `config_surface`→`state_surface` áthelyezése major-váltás nélkül átmegy,
  pedig a fogyasztói szerződés megváltozik.
- `tools/registrylib/paths.py` `resolve_pin()` a legfrissebb `-src<év>`-et
  numerikusan választja ki, tanúsítvány/aláírás-érvényesség ellenőrzése
  nélkül — jelenlét = bizalom.
- A CI (`.github/workflows/ci.yml`) **sem `make validate`-et, sem
  `make registry.validate`-et nem hívja** — csak `make check`/`make test`
  fut, ami a tooling kódot teszteli, nem a valódi séma-corpust.
- A migrált 26 fájl közül **1 van aláírva** (a `cic-primitives` bundle, a
  forrás repóból byte-verbatim átvett, eredeti aláírásával) — a másik 25
  egyike sem lett a `registry_sign.py`-jal aláírva.

Ne állítsd egyik fentiről se, hogy "kész" vagy "működik" pusztán azért,
mert `make check`/`make registry.validate` zöld — nézd meg pontosan, mit
NEM ellenőriz.

---

## Kapcsolódó repók

| Repo | Remote | Mit ad |
|---|---|---|
| `base-repo` | `base` | tooling, signing hook, CI, Makefile — `schema-registry` flavor branch |
| `cic-primitives` | — | a tervezési dokumentum forrása (`proposals/schema-registry`); **NEM archivált**, élő kernel-forrás |
| `cic-network`/`cic-compute`/`cic-kubernetes`/`cic-storage`/`cic-yang` | — | migráció forrása, tartalmuk átköltözött, **mind archivált** |
| `CIC-Schemas` | — | más témájú, tartalma NEM lett migrálva, nincs archiválva |
| `cic-module-oracle-cloud` | — | provider modul, a `providers/oracle-cloud/` sémáinak megvalósítója |

---

## Mérce

```bash
make validate            # örökölt bundle-check — jelenleg PLACEHOLDER, nem validál semmit érdemben
make registry.validate   # valódi, de a jelenlegi corpuson 0 verzióátmenetet és 0 pinnelt base-t lát
```

Egyik zöld futás sem jelenti azt, hogy a migrált tartalom valóban
ellenőrzött — lásd fent "Jelenlegi, valódi állapot".
