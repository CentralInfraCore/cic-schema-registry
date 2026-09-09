# Event

**Réteg:** `general/primitives/atomic/` — irreducibilis szemantikai atom
**Kind:** `AtomicPrimitive`

Atomic primitive describing an asynchronous notification — what a ManagedEntity can emit to the management plane on its own initiative. Event is not request/response: the source entity fires it, subscribed observers receive it. NotificationSurface is composed of Events.

---

## Eredet / provenance

Ez a séma a `cic-primitives` repóból migrált, a **valós, CICSourceCA-ellenjegyzett
`primitives/@v0.2.0` release**-ből (`meta_hash: IzHhprOwIjcGM8cjlWgHWR4nzW58k/LInM+GX8uQDwA=` a release
bundle-ben — ez a hash igazolja, hogy ez a fájl tartalmilag megegyezik azzal,
amit a release aláírt).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben (lásd
`cic-schema-registry` `CLAUDE.md` "Jelenlegi, valódi állapot" szakasza) — ez a
fájl jelenleg NEM hordoz saját `release`/`cic_countersign` blokkot. Amíg ez
elkészül, a tartalmi hitelesség a fenti `meta_hash`-en és a `cic-primitives`
repó saját, valódi aláírt release-én (`primitives/@v0.2.0` tag) keresztül
ellenőrizhető.

Verziók ebben a könyvtárban: lásd a könyvtárlistázást (`ls`) — nincs külön
index fájl.
