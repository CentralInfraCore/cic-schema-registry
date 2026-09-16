# CloudProviderAdapter

**Réteg:** `general/compute/` — adapter kontraktus
**Kind:** `AdapterContract` (`domain: cic:compute:ComputeResource`, `backend: cloud`)

## Mit ír le

Az interfész-szerződés, amit egy cloud compute instance-t kezelő adapternek
kell teljesítenie (`known_providers: [aws, gcp, azure, hcloud, do, ovh,
oci]`), hogy egy `ComputeResource`-t ki tudjon szolgálni `backend: cloud`
alatt. Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál:
`observe`/`apply`/`watch` műveletek, dotted-path hivatkozással a
`ComputeResource` surface-eire — nem konkrét provider-implementáció, hanem
a szerződés, amit bármelyik felsorolt provider adaptere teljesíthet.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-compute` repó `compute/@v0.2.3` tag-jéből
(`schemas/adapters/cloud-provider-adapter.yaml`), `metadata.version` a
release verziójára (`v0.2.3`) állítva. Ugyanabban a release bundle-ben
van, mint a `compute-resource` — ugyanaz a ténylegesen ellenőrzött kettős
aláírás (lásd `../compute-resource/README.md` "Eredet / provenance" szakasza).

Fájlonkénti release-aláírás: v0.2.3 a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén, minden létező verzión).
