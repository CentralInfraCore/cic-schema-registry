# Rke2Adapter

**Réteg:** `general/kubernetes/` — adapter kontraktus
**Kind:** `AdapterContract` (RKE2/Rancher, enterprise on-prem)

Az interfész-szerződés, amit egy RKE2/Rancher-alapú cluster kezelésére kell
teljesíteni, hogy `KubernetesCluster`/`KubernetesNode`-t ki tudjon
szolgálni. Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-kubernetes` repó `kubernetes/@v0.1.2` tag-jéből
(`schemas/adapters/rke2-adapter.yaml`), `metadata.version` a release
verziójára (`v0.1.2`) állítva (a gyengébb aláírású `v0.1.3` helyett — lásd
`../kubernetes-cluster/README.md`). Ugyanaz a ténylegesen ellenőrzött,
kettős aláírás.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
