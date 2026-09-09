# KubernetesNode

**Réteg:** `general/kubernetes/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:kubernetes:KubernetesNode`)

## Mit ír le

Egy Kubernetes cluster egyetlen node-ja — a `../kubernetes-cluster/`
gyermeke a `relationships.owns_nodes` kapcsolaton keresztül
(`cluster_ref` → a szülő `KubernetesCluster` CIC address-ére mutat,
surface-szintű dotted-path hivatkozással, nem típus-beágyazással).

Ugyanazt az 5 adapter-mintát (`cloud-managed`/`k3s`/`kubespray`/`rke2`/
`talos`) hordozza, mint a `kubernetes-cluster` — lásd
`../kubernetes-cluster/README.md` a részletekért, nem ismételve itt.

**`v0.1.4`-ben javítva** ([#18](https://github.com/CentralInfraCore/cic-schema-registry/issues/18)
kapcsán): a `v0.1.2`-ben itt is jelen volt a `binding_surface.adapter:
kubernetes-adapter` placeholder és a `state_surface.source` ugyanezen
hibája — mindkettő javítva, ugyanúgy, mint a `kubernetes-cluster`-nél
(lásd ott a részletes indoklást).

## Eredet / provenance / aláírás-ellenőrzés

Ugyanabból a release bundle-ből (`kubernetes/@v0.1.2`, NEM a gyengébb
aláírású `v0.1.3`-ból — lásd `../kubernetes-cluster/README.md` indoklását),
`metadata.version` a release verziójára (`v0.1.2`) állítva. Ugyanaz a
ténylegesen ellenőrzött, kettős aláírás. A `v0.1.2` fájl ezután
érintetlen — a fenti javítás egy új `v0.1.4` fájlban él (`v0.1.3`
szándékosan kihagyva, ugyanazon okból, mint a `kubernetes-cluster`-nél).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
