# IpmiAdapter

**Réteg:** `general/compute/` — adapter kontraktus
**Kind:** `AdapterContract` (`domain: cic:compute:ComputeResource`, `backend: physical`)

## Mit ír le

Az interfész-szerződés, amit egy bare-metal, IPMI/Redfish-vezérelt fizikai
szerver kezelésére kell teljesíteni, hogy egy `ComputeResource`-t ki tudjon
szolgálni `backend: physical` alatt — pl. `redfish_action`/`ipmi_fallback`
mintájú power-management műveletekkel (lásd a fájl `postcondition`
mezőit — pl. `power_state == off` egy graceful/force shutdown után).

Ugyanaz a minta, mint a `general/storage/storage-adapter/`-nál: `observe`/
`apply`/`watch` műveletek, dotted-path hivatkozással a `ComputeResource`
surface-eire.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-compute` repó `compute/@v0.2.3` tag-jéből
(`schemas/adapters/ipmi-adapter.yaml`), `metadata.version` a release
verziójára (`v0.2.3`) állítva, plusz minimális whitespace-tisztítás (egy
kézzel igazított sor, tartalmi változás nélkül). Ugyanabban a release
bundle-ben van, mint a `compute-resource` — ugyanaz a ténylegesen
ellenőrzött kettős aláírás (lásd `../compute-resource/README.md`
"Eredet / provenance" szakasza).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
