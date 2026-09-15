# SwitchNetconfAdapter

**Réteg:** `general/network/` — adapter kontraktus
**Kind:** `AdapterContract` (fizikai switch, NETCONF)

Az interfész-szerződés, amit egy NETCONF-képes fizikai switch kezelésére
kell teljesíteni, hogy `NetworkInterface`-t ki tudjon szolgálni. Ez az
adapter az, amit a `NetworkInterface.binding_surface.adapter_capabilities`
explicit megnevez, a mögötte lévő `standards/yang/ietf-interfaces-physical`,
`standards/yang/ietf-interfaces-l2vlan` és `standards/yang/
cic-switchport-vlan` YANGBlock-okkal együtt — lásd
`../network-interface/README.md` "Valós, konkrét kapocs a `standards/`
réteghez" szakasza.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-network` repó `network/@v0.4.1` tag-jéből
(`schemas/adapters/switch-netconf-adapter.yaml`), `metadata.version` →
`v0.4.1`. Ugyanaz a ténylegesen ellenőrzött, kettős aláírás, mint
`../network-interface/`-nál.

Fájlonkénti release-aláírás: `v0.4.2` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.4.2 — ietf-interfaces-vlan lecserélve ([#47](https://github.com/CentralInfraCore/cic-schema-registry/issues/47))

A `yang_composition.blocks` régi `ietf-interfaces-vlan` bejegyzése
lecserélve a `#47` szerint szétválasztott `ietf-interfaces-l2vlan`
(VLAN interfész-entitás) + `cic-switchport-vlan` (switchport VLAN
policy) blokk-párra. A `../network-interface/` `v0.4.2` ugyanezzel a
váltással konzisztens (`yang_refs` + a saját `known_adapters.
switch-netconf-adapter.yang_blocks` bejegyzése).
