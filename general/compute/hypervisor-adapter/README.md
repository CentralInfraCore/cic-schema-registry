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

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
