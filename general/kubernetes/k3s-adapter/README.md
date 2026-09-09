# K3sAdapter

**Réteg:** `general/kubernetes/` — adapter kontraktus
**Kind:** `AdapterContract` (K3s, könnyűsúlyú on-prem Kubernetes)

Az interfész-szerződés, amit egy K3s-alapú cluster kezelésére kell
teljesíteni, hogy `KubernetesCluster`/`KubernetesNode`-t ki tudjon
szolgálni. Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-kubernetes` repó `kubernetes/@v0.1.2` tag-jéből
(`schemas/adapters/k3s-adapter.yaml`), `metadata.version` a release
verziójára (`v0.1.2`) állítva (a gyengébb aláírású `v0.1.3` helyett — lásd
`../kubernetes-cluster/README.md`). Ugyanaz a ténylegesen ellenőrzött,
kettős aláírás.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
