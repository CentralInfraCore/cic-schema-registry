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

Fájlonkénti release-aláírás: `v0.4.2` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.4.2 — ietf-interfaces-vlan lecserélve ([#47](https://github.com/CentralInfraCore/cic-schema-registry/issues/47))

A `yang_composition.blocks` régi `ietf-interfaces-vlan` bejegyzése
lecserélve a `#47` szerint szétválasztott `ietf-interfaces-l2vlan`
(VLAN interfész-entitás) + `cic-switchport-vlan` (switchport VLAN
policy) blokk-párra.

**Talált, de itt szándékosan nem javított inkonzisztencia:** a
`../network-interface/` fájl saját `binding_surface.adapter_capabilities.
known_adapters` listájában az `ovs-adapter` bejegyzés `yang_blocks`
mezője már A MIGRÁCIÓ ELŐTT sem tartalmazta az `ietf-interfaces-vlan`-t
(csak `logical`/`tunnel`/`ip-v4`/`ip-v6`), miközben a `capabilities`
lista `vlan`-t is felsorol — ez egy a `#47`-től független, korábbi
hiányosság, nem javítva ebben a PR-ben.
