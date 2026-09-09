# KubernetesCluster

**Réteg:** `general/kubernetes/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:kubernetes:KubernetesCluster`)

## Mit ír le

Egy Kubernetes cluster mint **infrastrukturális egység** — lifecycle,
control plane konfiguráció, cluster networking, cert management.
Horgony: Talos `ClusterConfig` v1alpha1 (a `dependency.yaml`-ban rögzítve).

**Explicit hatókör-határ**: kizárólag cluster infrastruktúra. **Workload
management (Pod, Deployment, Service) NEM tartozik ide** — ugyanaz a fajta
tudatos, D-001-szerű scope-döntés, mint amit a `StorageResource`-nál láttunk
(block volume vs. object storage). A workload-szint egy külön, ez a fájl
nem próbálja lefedni.

## Az 5 adapter, amit ez a séma feltételez

| Adapter | Mit kezel |
|---|---|
| `cloud-managed-adapter` | Managed Kubernetes (GKE/EKS/AKS/OKE/DOKS) |
| `k3s-adapter` | K3s, könnyűsúlyú on-prem |
| `kubespray-adapter` | Kubespray/Ansible-alapú on-prem telepítés |
| `rke2-adapter` | RKE2/Rancher, enterprise on-prem |
| `talos-adapter` | Talos on-prem |

**Javítva v0.1.4-ben** — a korábban itt dokumentált inkonzisztencia
(`binding_surface.adapter: kubernetes-adapter`, ami egyik valós
adapternek sem felelt meg) a `cic-kubernetes` repó archiválása óta ott
már nem javítható (nincs hova issue-t nyitni), így itt, a registryben
lett kezelve:

- a flat `adapter:` mező eltávolítva — a kubernetes domain
  architektúrája eleve nem egyetlen generikus adapterrel dolgozik, mint
  a storage/compute (egy AdapterContract + backend enum), hanem minden
  provider saját, önálló fájl. Egyetlen flat mezőnek itt sosem volt
  értelme.
- helyette `binding_surface.adapter_capabilities.known_adapters` —
  valós adapter nevek, provider-önként (talos/kubespray/rke2/k3s),
  mindegyik a control_plane_tuning capability-vel (lásd lent). A
  `state_surface.source` mező is javítva (ugyanaz a placeholder volt
  ott is).
- `cloud-managed-adapter` szándékosan hiányzik ebből a mátrixból — a
  `provider` mező jelenlegi, egyszintű modellje nem tudja azonosítani
  (nincs backend+provider kettős kulcs, mint storage/compute-nál).
  Külön, strukturális kérdésként nyitva: #25
  (https://github.com/CentralInfraCore/cic-schema-registry/issues/25).

Ugyanez a placeholder ugyanígy jelen volt a ../kubernetes-node/ fájlban
is — az is javítva v0.1.4-ben.

## Control-plane mezők capability-jelölése ([#18](https://github.com/CentralInfraCore/cic-schema-registry/issues/18))

`api_server`/`etcd`/`controller_manager`/`scheduler` korábban mind
`required_on_create: false` volt, capability-jelölés nélkül — pedig
managed clusternél ezeket a szolgáltató kezeli, nem az ügyfél. Mind a
négy mező kapott egy `capability: control_plane_tuning` taget, és a
`binding_surface.adapter_capabilities.known_adapters` mondja meg,
melyik adapter hirdeti ezt (talos/rke2/kubespray igen; k3s nem — saját
leírása szerint részleges implementáció, a támogatás nincs
megerősítve; cloud-managed nincs a mátrixban, lásd fent).

## Reláció a `KubernetesNode`-hoz

`relationships.owns_nodes`: `KubernetesNode.cluster_ref` a szülő
`KubernetesCluster` CIC address-ére (`binding_surface.logical_id`) mutat —
ez egy surface-szintű dotted-path hivatkozás, ugyanaz a köztes erősségű
kapcsolat-típus, mint amit a `StorageAdapter`↔`StorageResource` között
találtunk, nem típus-beágyazás.

## Eredet / provenance / aláírás-ellenőrzés — fontos megjegyzés

Ez a fájl a `cic-kubernetes` repó **`kubernetes/@v0.1.2`** tag-jéből
származik, NEM a legfrissebb `v0.1.3`-ból, jó okkal: a `v0.1.3` release
tartalmilag **byte-azonos** a `v0.1.2`-vel (minden `meta_hash` megegyezik),
de a `v0.1.3` release fájlból **hiányzik a `cic_countersign` blokk** —
azaz a legfrissebb tag-nek **gyengébb** az aláírási lánca (csak szerzői
Vault-aláírás, CICSourceCA-ellenjegyzés nélkül), mint az eggyel korábbinak.
Ez valószínűleg egy regresszió volt a `cic-kubernetes` saját
release-folyamatában — dokumentálva a repó (mostanra archivált)
`cic-kubernetes#3` issue-jában, további javításra ott már nincs mód.

**Ténylegesen, `openssl`-lel ellenőrizve** a `v0.1.2` mindkét aláírása:
- szerzői Vault Transit aláírás a `build_hash` felett: **érvényes**
- CICSourceCA ellenjegyzés ugyanarra: **érvényes**
- CA érvényesség: 2026-03-20 → 2026-12-31 (ugyanaz a 2026-os évjárat, mint a
  primitívéknél/storage-nál/compute-nál).

`metadata.version` a release verziójára (`v0.1.2`) lett állítva, plusz
minimális whitespace-tisztítás (vessző utáni hiányzó szóköz, tartalmi
változás nélkül). A `v0.1.2` fájl ezután érintetlen — a fenti javítások
(#18) egy új `v0.1.4` fájlban élnek (`v0.1.3` szándékosan kihagyva, hogy
ne ütközzön a forrás repó azonos számú, de tartalmilag más jelentésű
tag-jével — lásd a fájl saját `metadata.description`-jét).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
