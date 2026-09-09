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
| **defined** | a mechanizmus/könyvtár létezik, `make validate` zöld rá |
| **draft** | terv megvan írásban (a `proposals/schema-registry`-ben), kód még nincs |
| **not implemented** | sem terv, sem kód — vagy terv van, de kód szándékosan még nincs |

---

## Jelenlegi, valódi állapot (2026-09-09-i bootstrap)

Ez a repó **most jött létre**, a `base-repo` `schema-registry@0.1.0`
flavor-tag-jéből bootstrap-olva. Amit ez ténylegesen jelent:

- A `general/`/`standards/`/`providers/` könyvtárak **üresek** (`.gitkeep`
  csak) — semmilyen séma-tartalom nincs még migrálva
- A `tools/compiler.py`/`tools/infra.py` **még az örökölt, bundle-alapú**
  logikát futtatja — a fájlonkénti aláírás, a base-chain coverage-check, a
  major-verzió-szabályok, a `-src<év>` kezelés **nincs megírva**
- A `renovate.json` még sima package-dependency-kre van konfigurálva, NEM a
  `base:`/`reference_target:` pin-ekre
- A CI (`.github/workflows/ci.yml`) az örökölt base-repo tesztkészletet
  futtatja, nem registry-specifikus szabályokat

Ne állítsd egyik fentiről se, hogy "kész" vagy "működik" — ez egy bootstrap
checkpoint, nem egy funkcionális registry.

---

## Kapcsolódó repók

| Repo | Remote | Mit ad |
|---|---|---|
| `base-repo` | `base` | tooling, signing hook, CI, Makefile — `schema-registry` flavor branch |
| `cic-primitives` | — | a tervezési dokumentum forrása (`proposals/schema-registry`) |
| `cic-network`/`cic-compute`/`cic-kubernetes`/`cic-storage`/`cic-yang`/`CIC-Schemas` | — | migráció forrása, archiválásra várnak |
| `cic-module-oracle-cloud` | — | provider modul, a `providers/oracle-cloud/` sémáinak megvalósítója |

---

## Mérce

```bash
make validate    # séma validáció — ha ez nem zöld, semmi sem kész
```
