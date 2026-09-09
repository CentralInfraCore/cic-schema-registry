# ComputeResource

**Réteg:** `general/compute/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:compute:ComputeResource`)

## Mit ír le ténylegesen ez a séma

A `ComputeResource` azt a "termék" szintet írja le, amit ténylegesen
megrendelsz/igényelsz egy hypervisortól, egy cloud providertől, vagy egy
bare-metal (IPMI-vezérelt) géptől — egy virtuális gépet, egy fizikai
szervert, vagy egy cloud compute instance-t. Pontosan ugyanaz a mintázat,
mint a `general/storage/storage-resource/`-nál: a séma a hypervisor/
physical/cloud paradigmát **nem a `config_surface`-ben**, hanem az
adapter- és cím-rétegben (`binding_surface`) kezeli.

## A multi-paradigma kezelése — ugyanaz a bevált mechanizmus, mint a storage-nál

Nincs séma-szintű derivációs lánc paradigmánként — helyette:

1. **Cím-alapú routing**: `binding_surface` 4-részes összetett címe
   (`backend`/`provider`/`location`/`id`) — `backend: vm|physical|cloud`.
2. **`capability:` tag** az opcionális mezőkön (pl. platform-tag-ek,
   spot/preemptible instance, availability zone).
3. **Capability-mátrix** az egyes backendek/adapterek tényleges
   képességeiről.

## A három adapter, amit ez a séma feltételez

| Adapter | Backend | Mit kezel |
|---|---|---|
| `hypervisor-adapter` | `vm` | Hypervisor-managed virtuális gép |
| `ipmi-adapter` | `physical` | Bare-metal, IPMI/Redfish-vezérelt fizikai szerver |
| `cloud-provider-adapter` | `cloud` | Cloud compute instance (aws/gcp/azure/hcloud/do/ovh/oci) |

Ezek **külön fájlok** ebben a registry-ben (lásd `../hypervisor-adapter/`,
`../ipmi-adapter/`, `../cloud-provider-adapter/`) — a kapcsolat közöttük
laza, cím-alapú routing, nem típus-beágyazás (§3.1 a
`cic-primitives/proposals/schema-registry` dokumentumban).

## Cross-domain referencia és a nyitva hagyott pinnelési kérdés

Ez a séma explicit nem hivatkozik `cic-reference`-fel más domainre a
jelenlegi tartalmában (ellentétben a `StorageResource.attached_to`-val,
ami `ComputeResource`-ra hivatkozik) — a kapcsolat iránya egyoldalú: a
storage hivatkozik a compute-ra, nem fordítva.

`identity.base: cic:core:ManagedEntity` — **unpinned**, ugyanaz a nyitott
pont, mint a `StorageResource`-nál: technikailag most sem oldható fel
pontos verzióra, mert a `registrylib` még nem lát bele a kernel bundle-jébe
(lásd `general/primitives/cic-primitives/README.md` "Ismert, nyitott pont").

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-compute` repó `compute/@v0.2.3` tag-jéből
(`schemas/domain/compute-resource.yaml`), egyetlen ponton módosítva:
`metadata.version` a release verziójára (`v0.2.3`) lett állítva, plusz
minimális whitespace-tisztítás (kézzel igazított oszlopok, amiket ez a
repó szigorúbb `.yamllint`-je hibának jelölt — tartalmi változás nélkül).

**Ténylegesen, `openssl`-lel ellenőrizve** (nem csak struktúra alapján
feltételezve):
- szerzői Vault Transit aláírás a `build_hash` felett: **érvényes**
- CICSourceCA ellenjegyzés ugyanarra: **érvényes**
- az ellenjegyző CA érvényessége: 2026-03-20 → 2026-12-31 (ugyanaz a
  2026-os évjárat, mint a `cic-primitives` kernelnél és a `cic-storage`
  tartalomnál) — ez indokolja a `-src2026` jelölést.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben —
ez a fájl NEM hordoz saját `release`/`cic_countersign` blokkot.

## v0.2.4 — registry-native tartalmi javítás (NEM a `cic-compute`-ból jön)

A `v0.2.3` fent leírt módon byte-azonos a `cic-compute` archivált
repójából. `v0.2.4` ebben a registryben született
([#16](https://github.com/CentralInfraCore/cic-schema-registry/issues/16)):

A `config_surface` kér `cpu_cores`/`memory_mb`/`disk_gb`-t, de a
`state_surface`-ben csak kihasználtsági metrika volt (`cpu_usage_pct`,
`memory_usage_mb`), tényleges allokált kapacitás sehol. Ez azért lényeges,
mert a `resize` explicit megengedi, hogy az adapter a legközelebbi
`instance_type`-ot válassza (AWS/GCP/Azure) — enélkül a mező nélkül a
kért és a tényleges eltérés sehol nem jelenik meg strukturáltan.

Megoldás: `cpu_cores_actual`/`memory_mb_actual`/`disk_gb_actual` új
state mezők, mindegyik egy `Contract: type: must` kontraktussal
(**meglévő, már dokumentált Contract-típus, nem új primitívum** —
`cic-primitives` Contract atom, "Logical constraint... May express
cross-node relationships"), ami kizárja, hogy KEVESEBB legyen allokálva
a kértnél — a felfelé eltérés (instance_type lookup) szándékosan
megengedett marad.

Additív, PATCH bump — semmi nem tűnt el, `check_schema_evolution` zöld
rá.
