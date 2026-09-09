# SwitchNetconfAdapter

**Réteg:** `general/network/` — adapter kontraktus
**Kind:** `AdapterContract` (fizikai switch, NETCONF)

Az interfész-szerződés, amit egy NETCONF-képes fizikai switch kezelésére
kell teljesíteni, hogy `NetworkInterface`-t ki tudjon szolgálni. Ez az
adapter az, amit a `NetworkInterface.binding_surface.adapter_capabilities`
explicit megnevez, a mögötte lévő `standards/yang/ietf-interfaces-physical`
és `standards/yang/ietf-interfaces-vlan` YANGBlock-okkal együtt — lásd
`../network-interface/README.md` "Valós, konkrét kapocs a `standards/`
réteghez" szakasza.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-network` repó `network/@v0.4.1` tag-jéből
(`schemas/adapters/switch-netconf-adapter.yaml`), `metadata.version` →
`v0.4.1`. Ugyanaz a ténylegesen ellenőrzött, kettős aláírás, mint
`../network-interface/`-nál.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
