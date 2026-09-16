# CIC Schema Registry — Claude kontextus

## Branch szabály — KÖTELEZŐ

**A `devel` ág és a két-ágas modell 2026-09-15-én tudatosan visszavonva**
(`77a709b`, "chore(ci): drop devel from CI triggers, retire the
two-branch workflow") — sem branch protection nem volt egyik ágon sem,
sem valódi tartalmi divergencia nem alakult ki a `devel`→`main`
promóciók között (minden promóció 1:1 pass-through volt). A `devel` ág
azóta törölve, sem lokálisan, sem a remote-on nem létezik.

**Jelenlegi modell:**

- `main` — csak merge fogad, közvetlen commit tilos
- fájlonkénti/issue-branch-ek (pl. `fix/46-rfc-provenance-origin`,
  `feature/dhcp-service-schema`) — egy változtatásra, PR-ral `main`
  ellen, merge után törlendő (nem perzisztens ág)

Munkafolyamat: branch `main`-ből → módosítás → PR `main` ellen → CI zöld
→ merge → branch törlése. Nincs köztes integrációs ág.

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

## Jelenlegi, valódi állapot (2026-09-16-i frissítés)

30 séma-könyvtár (`general/`: 18, `standards/yang/`: 12), 52 tartalmi
fájl (verziók összesen), `providers/` még mindig üres (`.gitkeep` only —
nincs provider-modul mapping):

| Réteg | Fájlszám (verziók összesen) |
|---|---:|
| `general/primitives/` | 1 (bundle) |
| `general/compute/` | 6 |
| `general/storage/` | 4 |
| `general/kubernetes/` | 9 |
| `general/network/` | 7 (`network-interface`, `switch-netconf-adapter`, `ovs-adapter`, `dhcp-service`) |
| `standards/yang/` | 25 (`ietf-lldp`, `cic-yang-block-schema`, `ietf-interfaces-{base,physical,logical,tunnel,vlan,l2vlan}`, `cic-switchport-vlan`, `ietf-ip-v4`, `ietf-ip-v6`, `ietf-nat`) |
| `providers/` | 0 |

**Aláírás: 52/52 tartalmi fájl valódi Vault Transit + CICSourceCA
ellenjegyzéssel aláírva** (`grep -L '^release:'` a teljes
`general/`+`standards/` fán üres találatot ad) — `tools/registry_sign.py`
(+ `tools/registrylib/signing.py` + `tools/vault-mtls-client/`), minden
egyes verzió saját, önálló aláírt egység (nem bundle).

**`tools/generate_latest.py` + `make registry.latest`** — `LATEST.yaml`
generálás + frozen-file guard: minden `ENROLLED`-be felvett könyvtárban
(jelenleg 9: `standards/yang/{ietf-lldp,cic-yang-block-schema,
ietf-interfaces-tunnel,ietf-interfaces-vlan,ietf-interfaces-physical,
ietf-nat,ietf-interfaces-l2vlan,cic-switchport-vlan}`,
`general/network/dhcp-service`) kikényszeríti, hogy egy már közzétett
`-src<év>.yaml` fájlt senki ne szerkesszen helyben — csak a
release-aláírás felvétele a kivétel. Fokozatos rollout: **4 könyvtár
NINCS ENROLLED-ban** (`ietf-interfaces-base`, `ietf-interfaces-logical`,
`ietf-ip-v4`, `ietf-ip-v6`) — ezekre a guard nem vonatkozik.

**Ennek ellenére a validáció ma nagyon kevés tényleges garanciát ad — ne
higgy a zöld futásnak félrevezető magabiztossággal:**

- `make validate` (`tools/compiler.py validate` → `run_validation()` a
  `tools/infra.py`-ban) **NEM placeholder többé, de NEM is corpus-check**
  — mostantól explicit warningot ad, hogy csak egy örökölt bundle-
  template-et (`schemas/index.yaml`) tölt be és resolve-ol, a valódi
  `general/standards/providers` tartalmat SOSEM éri el. Ezért a CI-ből
  ki lett véve (lásd `.github/workflows/ci.yml` komment) — a
  `registry.validate` a valódi corpus-check.
- `make registry.validate` valódi és MOST már több séma esetén tényleges
  verzióátmenetet ellenőriz (pl. `compute-resource` v0.2.3→v0.2.4→v0.2.5,
  `storage-resource` v0.1.2→...→v0.1.4) — de a `standards/yang/`
  YANGBlock-dialektusú fájlok (spec.config/spec.state, nem
  config_surface/state_surface) evolúció-ellenőrzése továbbra is
  explicit SKIPPED (nem hazudik OK-t, de nem is fut le). A
  `reference_target` mezőt semmi nem oldja fel, csak a docstringben
  szerepel.
- Az 5+ domain-kompozíció `identity.base:` mezője pontos verzióra
  pin-el (`cic:core:ManagedEntity@v0.2.0`), és
  `tools/registrylib/identity.py` `build_type_index()`-e a
  `cic-primitives` bundle `specs[]`-ébe is bemászik, hogy ezt fel tudja
  oldani (`tools/registrylib/bundle.py`). A pin ténylegesen feloldódik
  és látszik a `SKIPPED` jelentésben — de a kernel típusai
  (`ManagedEntity` is) `slots`/`fields`-en át írják le magukat, nem a
  `config_surface`/`state_surface`/... node-listákon, amit
  `coverage.py` ért — ezért a mezőkompatibilitás-ellenőrzés a kernel
  ellen **még mindig nem fut le**, csak EXPLICIT, pontos okkal jelzett
  SKIPPED-ként.
- `tools/registrylib/coverage.py` a mezőket surface-től függetlenül,
  pusztán névre lapítja, és csak a felső szintet hasonlítja — egy
  azonos nevű, azonos típusú mező `config_surface`→`state_surface`
  áthelyezése, vagy egy beágyazott mezőtípus-változás major-váltás
  nélkül átmegy.
- `tools/registrylib/paths.py` `resolve_pin()` a legfrissebb `-src<év>`-et
  numerikusan választja ki, tanúsítvány/aláírás-érvényesség ellenőrzése
  nélkül — jelenlét = bizalom, nem kriptográfiai bizonyíték.
- A CI (`.github/workflows/ci.yml`) `make check` (most `infra.fmt-check`-
  kel, ami nem ír felül csendben) → `make test` → `make infra.coverage`
  (valódi, `tools/` egészére, `--cov=tools`) → `make registry.validate`
  → `make registry.latest` láncot futtatja. `make validate` szándékosan
  KI van véve, lásd fent.

Ne állítsd egyik fentiről se, hogy "kész" vagy "működik" pusztán azért,
mert `make check`/`make registry.validate` zöld — nézd meg pontosan, mit
NEM ellenőriz. A fenti réseknek megfelelő, még nyitott issue-k:
`#79`/`#80`/`#88`/`#94`/`#96` (coverage/meta-séma mélység),
`#100`/`#102` (pin-érvényesség), `#92`/`#93` (frozen-file guard vakfoltjai)
— lásd `#109` az összefoglaló roadmap-javaslatért.

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
make registry.validate   # valódi corpus-check — base-chain coverage + verzió-evolúció, de sekély (lásd fent)
make registry.latest     # LATEST.yaml + frozen-file guard, 9/30 könyvtáron
make check               # fmt-check (nem ír felül) + lint + typecheck + security
make test                # pytest
make infra.coverage      # valódi coverage report, tools/ egészére
```

`make validate` szándékosan NEM része a mércének — lásd fent, örökölt
bundle-template-et tölt be, nem a registry tartalmát. Egyik zöld futás
sem jelenti azt, hogy a tartalom mélyen ellenőrzött — lásd fent
"Jelenlegi, valódi állapot".
