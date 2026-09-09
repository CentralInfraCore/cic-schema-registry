# OvsAdapter

**Réteg:** `general/network/` — adapter kontraktus
**Kind:** `AdapterContract` (Open vSwitch / Linux bridge)

Az interfész-szerződés, amit egy OVS/Linux-bridge-alapú hálózati
interfész kezelésére kell teljesíteni, hogy `NetworkInterface`-t ki
tudjon szolgálni. Ugyanaz a minta, mint a
`general/storage/storage-adapter/`-nál.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-network` repó `network/@v0.4.1` tag-jéből
(`schemas/adapters/ovs-adapter.yaml`), `metadata.version` → `v0.4.1`.
Ugyanaz a ténylegesen ellenőrzött, kettős aláírás, mint
`../network-interface/`-nál.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
