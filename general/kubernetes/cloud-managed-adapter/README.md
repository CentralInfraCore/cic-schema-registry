# CloudManagedAdapter

**Réteg:** `general/kubernetes/` — adapter kontraktus
**Kind:** `AdapterContract` (managed Kubernetes: GKE, EKS, AKS, OKE, DOKS)

Az interfész-szerződés, amit egy felhő-managed Kubernetes szolgáltatás
(Google GKE, AWS EKS, Azure AKS, Oracle OKE, DigitalOcean DOKS) kezelésére
kell teljesíteni, hogy `KubernetesCluster`/`KubernetesNode`-t ki tudjon
szolgálni. Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-kubernetes` repó `kubernetes/@v0.1.2` tag-jéből
(`schemas/adapters/cloud-managed-adapter.yaml`), `metadata.version` a
release verziójára (`v0.1.2`) állítva. A `v0.1.2`-t választottuk a
frissebb `v0.1.3` helyett, mert az utóbbiból hiányzik a CICSourceCA
countersign (lásd `../kubernetes-cluster/README.md`). Ugyanaz a
ténylegesen ellenőrzött, kettős aláírás.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
