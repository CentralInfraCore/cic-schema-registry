# StorageResource

**Réteg:** `general/storage/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:storage:StorageResource`)

## Mit ír le ténylegesen ez a séma

A `StorageResource` a **"block storage" fogalmát írja le abban az értelemben,
ahogy egy ügyfél ténylegesen megrendeli/igényli egy felhőtől vagy
hypervisortól** — pl. amikor valaki létrehoz egy Block Volume-ot az OCI-n,
egy EBS volume-ot AWS-en, vagy egy virtuális lemezt egy Proxmox
hypervisoron. Ez a **"termék" szint**, nem a mögötte lévő nyers eszköz
szintje:

```
general/storage/storage/           ← nyers HDD/SSD/NVMe/PMEM egy fizikai
                                      hoszton belül (MÉG NEM létezik ebben
                                      a registry-ben — külön feladat)
general/storage/storage-resource/  ← EZ A FÁJL — a hálózaton keresztül
                                      elérhető, csatolható blokkeszköz-termék
```

Amikor pl. Oracle Cloud-tól rendelsz egy Block Volume-ot: azt kapod, amit ez
a séma ír le (méret, hozzáférési mód, titkosítás, tag-ek — `config_surface`).
Azt, hogy ez hány fizikai NVMe-lemezre van szétosztva, milyen redundancia-
sémával — **sosem látod, és ennek a sémának sem kell látnia**. Ez a
provider belső ügye, a séma szándékosan nem modellezi (lásd
`derivation_chain`/`binding_surface` — a paradigma az adapter/cím rétegben
van, nem a `config_surface`-ben).

## Explicit hatókör-határ — mi NEM tartozik ide

A forrás saját szava szerint (eredetileg D-001 döntés a `cic-storage`
repóban): **kizárólag block volume lifecycle**. Object storage, NFS/NAS,
és snapshot mint önálló resource **tudatosan kizárva**.

Ez nem önkényes határ — strukturális okai vannak, amiket ebben a registry-
munkában újra levezettünk, függetlenül a forrás döntésétől:

| Tulajdonság | Block storage (ez a séma) | Object storage (KIZÁRVA) |
|---|---|---|
| Hozzáférési egység | nyers blokk (offset+szám) | egész objektum (kulcs) |
| Protokoll | csatolás (attach), blokkeszköz-szintű | HTTP API, nincs csatolás |
| Mutálhatóság | részleges, in-place írás | egész-objektum csere (PUT felülír) |
| Struktúra forrása | ráépülő fájlrendszer adja | a tárolás saját névtere (bucket+kulcs) |
| Kapacitás | fix, előre lefoglalt (`size_gb`) | elasztikus, nincs előzetes foglalás |
| Viszony a compute-hoz | `attached_to` — a state RÉSZE | nincs "csatolás" fogalom |

Emiatt az object storage-hoz szükséges mezők/műveletek (méret nélküli
kapacitás, kulcs-alapú címzés, verziózás mint "snapshot") **nem** tehetők
be ide capability-tag-gel — ez nem néhány opcionális mező kérdése, hanem a
teljes `operation_surface`/`binding_surface` más igényel. Az object storage
egy külön, még meg nem írt koncepció lesz, nem ennek a fájlnak a bővítése.

## A capability-tag mechanizmus — hogyan kezeli a backend-varianciát

A `StorageResource` EGYETLEN lapos sémában kezeli a hypervisor-managed
disk / SAN-LUN / cloud block storage hármas variánsát — NEM séma-szintű
derivációs lánccal (Storage→RAID→... — ezt az ötletet korábban megvizsgáltuk
és elvetettük, mert sehol nincs bizonyítva a valós tartalomban), hanem:

1. **Cím-alapú routing**: a `binding_surface` egy 4-részes összetett cím
   (`backend`/`provider`/`location`/`id`) alapján dönti el, melyik adapter
   kezeli a kérést — `backend: hypervisor|san|cloud`.
2. **`capability:` tag az opcionális mezőkön/műveleteken**: `filesystem`,
   `encryption`, `tagging`, `resize`, `snapshot`, `usage_metrics`,
   `health_monitoring` — minden ilyen mező/művelet egy capability-hez kötött.
3. **Capability-mátrix**: `binding_surface.adapter_capabilities.known_adapters`
   mondja meg, melyik backend melyik capability-t támogatja ténylegesen.

Ugyanez a minta alkalmazható lenne pl. HDD/SSD/NVMe/PMEM médiatípus-
varianciára is (a jövőbeli `general/storage/storage/` sémánál) — a
`Contract: type: when` kontraktus-típussal kiegészítve tudja kikényszeríteni,
hogy pl. egy SSD rekordon ne jelenhessen meg egy HDD-specifikus mező.

## Cross-domain referencia

`state_surface.attached_to` → `semantic_type: cic-reference`,
`reference_target: cic:compute:ComputeResource` — ez a mechanizmus már a
forrásban is megvolt, mielőtt mi külön kérdésként foglalkoztunk volna vele
(D-014, `cic-primitives`).

**⚠ Jelenleg NEM verzió-pinnelt** (`cic:compute:ComputeResource`, nem
`@v0.2.3`-mal) — ez a régi, git-merge-alapú konvenció maradványa. Nem
javítottuk itt, mert a `ComputeResource` maga még nincs migrálva ebbe a
registry-be — amint migrálva lesz, ezt is pinnelni kell, szimmetrikusan az
`identity.base`-szel.

Hasonlóan, `identity.base: cic:core:ManagedEntity` is **unpinned** —
most már LENNE mire pinnelni (`general/primitives/cic-primitives/` a
kernelt tartalmazza), de a bundle-alakú kernel-fájlba a `registrylib` még
nem tud belelátni (lásd a kernel README "Ismert, nyitott pont" szakaszát) —
tehát a pinnelés egyelőre technikailag sem oldható fel, még ha meg is
tennénk.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-storage` repó `storage/@v0.1.2` tag-jéből
(`schemas/domain/storage-resource.yaml`), egyetlen ponton módosítva:
`metadata.version` a release verziójára (`v0.1.2`) lett állítva. **Ténylegesen,
`openssl`-lel ellenőrizve** (nem csak struktúra alapján feltételezve) a
release bundle mindkét aláírása:
- szerzői Vault Transit aláírás a `build_hash` felett: **érvényes**
- CICSourceCA ellenjegyzés ugyanarra: **érvényes**
- az ellenjegyző CA (`CIC Source CA`) érvényessége: 2026-03-20 → 2026-12-31
  (ugyanaz a 2026-os évjárat, mint a `cic-primitives` kernelnél) — ez
  indokolja a `-src2026` fájlnév-jelölést.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben —
ez a fájl NEM hordoz saját `release`/`cic_countersign` blokkot. A tartalmi
hitelesség a `cic-storage` repó saját, GHCR-en is publikált release-én
keresztül ellenőrizhető (`ghcr.io/centralinfracore/schema/cic-storage:v0.1.2-src2026`).

## v0.1.3 — registry-native tartalmi javítás (NEM a `cic-storage`-ból jön)

A `v0.1.2` fájl fent leírt módon byte-azonos a `cic-storage` archivált
repójából — az EGYETLEN kivétel a `metadata.version` beállítása. `v0.1.3`
ezzel szemben **ebben a registryben született**, mert `cic-storage` már
archivált (nincs hova visszamenő issue-t nyitni, mint a korábbi
placeholder-mismatch hibáknál) — ez az első eset, hogy a registry saját
maga hordoz tartalmi evolúciót, nem csak migrációt.

Mi változott ([#15](https://github.com/CentralInfraCore/cic-schema-registry/issues/15)):
`state_surface.attached_to` egyetlen string, miközben `config_surface.access_mode`
explicit hirdeti a `multi_attach` capabilityt (`read_only_many`/`read_write_many`)
— egy több compute-erőforráshoz csatolt volume teljes csatolási állapota nem
volt leírható. Megoldás:

- új `state_surface.attachments` lista (`target`+`state` páronként) — ez adja
  vissza a teljes, multi-attach-kompatibilis állapotot
- `attached_to` megmaradt, de `access.conformance: deprecated` — visszafelé
  kompatibilis, single-attach esetén továbbra is használható, de már nem ez
  a hivatkozási forrás
- `operation_surface.detach` kapott egy opcionális `target` inputot, mert egy
  konkrét csatolás megszüntetéséhez multi-attach esetén tudni kell, MELYIK
  csatolást szünteti meg — ez a séma szinten csak leírásban kötelező
  multi-attach esetén, strukturálisan nem kikényszerített (lásd
  [#17](https://github.com/CentralInfraCore/cic-schema-registry/issues/17) —
  hasonló, prózában élő garanciák általános problémája)

Ez additív, MAJOR-váltás nélküli (PATCH) módosítás — a `registrylib`
`check_schema_evolution` ellenőrzi és zöld rá, mert `attached_to` nem tűnt
el, csak deprecated lett.

## v0.1.4 — must-kontraktus a delete/resize szövegben élő szabályokra

([#17](https://github.com/CentralInfraCore/cic-schema-registry/issues/17))
Két, korábban csak `description`-ben kimondott szabály kapott valódi,
géppel értelmezhető kontraktust — mindkettő a `Contract` atom MEGLÉVŐ
`must` típusát használja (XPath-szerű logikai kifejezés, cross-node
relációkra — ez nem új primitívum, a `cic-primitives` kernel már
dokumentálja):

- `operation_surface.delete.confirm`: `must: confirm = true()` — a
  `mandatory: true` eddig nem tiltotta a `false` értéket.
- `operation_surface.resize.size_gb`: `must: size_gb >=
  ../../state_surface/size_actual_gb` — a "csak növelhet" szabály eddig
  csak prózában élt.

Az issue #17 harmadik pontja (adapter `apply` idempotencia strukturált
jelölése) NEM ebben a fájlban lett kezelve — az `AdapterContract` dialektus
(`storage-adapter.yaml` és a többi adapter-kontraktus) egyáltalán nem
ismer `idempotent:` mezőt sehol, ez egy dialektus-szintű döntés, nem egy
fájl foltja. Lásd [#23](https://github.com/CentralInfraCore/cic-schema-registry/issues/23).

## Kapcsolódó fájl

`storage-adapter/` — a `StorageAdapter` kontraktus, amit ez a séma
`binding_surface.adapter: storage-adapter` néven, illetve az adapter maga
`StorageResource.config_surface`/`state_surface`-re dotted-path
hivatkozással köt össze. Ez egy köztes erősségű kapcsolat — nem típus-
beágyazás, de nem is puszta névhivatkozás; a `registrylib` jelenleg nem
ellenőrzi ezt a fajta hivatkozást (csak `identity.base`/`reference_target`-et).
