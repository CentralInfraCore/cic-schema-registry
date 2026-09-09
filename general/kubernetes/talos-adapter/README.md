# TalosAdapter

**Réteg:** `general/kubernetes/` — adapter kontraktus
**Kind:** `AdapterContract` (Talos on-prem)

Az interfész-szerződés, amit egy Talos-alapú cluster kezelésére kell
teljesíteni, hogy `KubernetesCluster`/`KubernetesNode`-t ki tudjon
szolgálni. Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál.
A `KubernetesCluster` saját maga is Talos `ClusterConfig`-ra horgonyoz
(lásd `../kubernetes-cluster/README.md`), tehát ez az adapter a
legszorosabban illeszkedő a domain-kompozícióhoz.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-kubernetes` repó `kubernetes/@v0.1.2` tag-jéből
(`schemas/adapters/talos-adapter.yaml`), `metadata.version` a release
verziójára (`v0.1.2`) állítva (a gyengébb aláírású `v0.1.3` helyett — lásd
`../kubernetes-cluster/README.md`). Ugyanaz a ténylegesen ellenőrzött,
kettős aláírás.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
