# HypervisorAdapter

**Réteg:** `general/compute/` — adapter kontraktus
**Kind:** `AdapterContract` (`domain: cic:compute:ComputeResource`, `backend: vm`)

## Mit ír le

Az interfész-szerződés, amit egy hypervisor-managed virtuális gépet kezelő
adapternek (pl. Proxmox, libvirt/KVM, VMware) teljesítenie kell, hogy egy
`ComputeResource`-t ki tudjon szolgálni `backend: vm` alatt. Ugyanaz a
minta, mint a `general/storage/storage-adapter/`-nál: `observe`/`apply`/
`watch` műveletek, amik a `ComputeResource` megfelelő surface-eire mutatnak
dotted-path hivatkozással (nem típus-beágyazás).

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-compute` repó `compute/@v0.2.3` tag-jéből
(`schemas/adapters/hypervisor-adapter.yaml`), `metadata.version` a release
verziójára (`v0.2.3`) állítva. Ugyanabban a release bundle-ben van, mint a
`compute-resource` — ugyanaz a ténylegesen ellenőrzött kettős aláírás
(lásd `../compute-resource/README.md` "Eredet / provenance" szakasza).

Fájlonkénti release-aláírás: v0.2.3, v0.2.4 a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén, minden létező verzión).

## v0.2.4 — domain mező ténylegesen javítva ([#97](https://github.com/CentralInfraCore/cic-schema-registry/issues/97))

A `domain:` mező a `spec`-ben tényleges `VirtualMachine`-t hordozott
(nem létező, sosem migrált domain-típus), miközben ez a README fejléce
már régóta a helyes `cic:compute:ComputeResource`-t állította — a
dokumentáció megelőzte a tényleges tartalmat. Most a fájl is ezt mondja.
