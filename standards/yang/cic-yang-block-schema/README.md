# cic-yang-block-schema

**Réteg:** `standards/yang/` — meta-séma
**Kind:** `YANGBlock` (`meta-schema` tag) — validálja a `YANGBlock` kind
belső struktúráját

## Mit ír le

Ez NEM tartalmi séma (nem ír le konkrét YANG-modult) — ez a
**meta-séma**, ami a `standards/yang/` alatt élő `YANGBlock`-fájlok
(`ietf-interfaces-*`, `ietf-ip-*`, `ietf-lldp`) belső struktúráját
validálja: milyen mezőtípusok engedettek (`string`/`mac-address`/
`ipv4-address`/`vlan-id`/`interface-ref`/stb.), mi kötelező egy
`field_schema`-ban. A forrás saját szava szerint: *"Az index.yaml csak
kind/yang_module/yang_source kötelezőségét ellenőrzi. Ez a schema a
config/state/notifications mezők belső konzisztenciáját validálja."*

Ez a `general/primitives/cic-primitives/` kernelhez hasonló szerepű
(alapvető, mindenki más rá épül ebben a rétegben), de attól függetlenül —
**két külön meta-séma-dialektus** él egymás mellett ebben a registry-ben:
`AtomicPrimitive`/`AggregatePrimitive`/`DomainComposition` (a `general/`
primitíva-modell) és `YANGBlock` (a `standards/yang/` szabvány-modell). A
`tools/registrylib` jelenleg egyiket sem érti mélyebben ennél a
fájlnál — csak a saját fájlnév-konvenciót és a `DomainComposition`-ok
`identity.base`/`reference_target` mezőit ellenőrzi.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból
(`schemas/cic-yang-block.schema.yaml`), `metadata.version` → `v0.1.3`.
Ugyanaz a ténylegesen ellenőrzött, kettős aláírás, mint a többi `cic-yang`
fájlnál.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
