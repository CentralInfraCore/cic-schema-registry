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

## v0.1.5 — condition enum idézőjelbe téve ([#99](https://github.com/CentralInfraCore/cic-schema-registry/issues/99))

`condition` enum `[True, False, Unknown]` — PyYAML az idézőjel nélküli
`True`/`False`-t boolean-ként töltötte be, `Unknown`-t stringként,
holott a mező `scalar_type: string` és a valós Kubernetes
`NodeCondition.status` is string. Most `["True", "False", "Unknown"]`.

Fájlonkénti release-aláírás: v0.1.2, v0.1.4, v0.1.5 a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén, minden létező verzión).
