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

## Az 5 adapter, amit ez a séma feltételez — és egy inkonzisztencia

| Adapter | Mit kezel |
|---|---|
| `cloud-managed-adapter` | Managed Kubernetes (GKE/EKS/AKS/OKE/DOKS) |
| `k3s-adapter` | K3s, könnyűsúlyú on-prem |
| `kubespray-adapter` | Kubespray/Ansible-alapú on-prem telepítés |
| `rke2-adapter` | RKE2/Rancher, enterprise on-prem |
| `talos-adapter` | Talos on-prem |

**⚠ Talált inkonzisztencia, nem javítva itt (byte-verbatim migráció):** a
`binding_surface.adapter` mező értéke `kubernetes-adapter` — ez **nem
egyezik egyik fenti, valós adapter nevével sem**. Vagy egy régi,
elavott placeholder maradt bent, vagy egy hatodik, sosem migrált
adapter-koncepcióra utal. Ezt a forrás-repóban (`cic-kubernetes`) kellene
tisztázni/javítani, egy issue-n keresztül — itt csak jelezzük, nem
találgatjuk ki a helyes értéket.

Ugyanez a mező ugyanígy jelen van a `../kubernetes-node/` fájlban is.

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
Ez valószínűleg egy regresszió a `cic-kubernetes` saját release-folyamatában
— érdemes ott issue-t nyitni rá.

**Ténylegesen, `openssl`-lel ellenőrizve** a `v0.1.2` mindkét aláírása:
- szerzői Vault Transit aláírás a `build_hash` felett: **érvényes**
- CICSourceCA ellenjegyzés ugyanarra: **érvényes**
- CA érvényesség: 2026-03-20 → 2026-12-31 (ugyanaz a 2026-os évjárat, mint a
  primitívéknél/storage-nál/compute-nál).

`metadata.version` a release verziójára (`v0.1.2`) lett állítva, plusz
minimális whitespace-tisztítás (vessző utáni hiányzó szóköz, tartalmi
változás nélkül).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
