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

Fájlonkénti release-aláírás: `v0.1.4`, `v0.1.5`, `v0.1.6` és `v0.1.7` a
`tools/registry_sign.py` (proposals/schema-registry §5) szerint valódi
Vault author-aláírással és CICSourceCA ellenjegyzéssel van ellátva
(`release:`/`cic_countersign:` blokk a fájl végén).

## v0.1.7 — két önellentmondás javítva ([#101](https://github.com/CentralInfraCore/cic-schema-registry/issues/101), [#84](https://github.com/CentralInfraCore/cic-schema-registry/issues/84))

A fájl saját `metadata` blokkjából hiányzott a `source` mező, miközben a
meta-séma saját `metadata.required` listája minden YANGBlock fájlon
kötelezővé teszi — a meta-séma nem validálta volna saját magát a saját
szabálya szerint (`#101`). Pótolva: `source: CIC internal`.

`field_schema.required_when` nem deklarálta az `in` property-t, amit a
corpus már 3 helyen ténylegesen használ (`ietf-nat`, `translation_type`
alapján feltételes mezők) — a testvér `applicable_when` mintáját követve
pótolva (`#84`). Mindkét feltétel-objektumhoz (`applicable_when`,
`required_when`) hozzáadva `additionalProperties: false` is, hogy egy
jövőbeli elgépelt/nem-dokumentált operátor tényleges validációs hibaként
bukjon. Ellenőrizve: a teljes `standards/yang` corpus egyik
`applicable_when`/`required_when` blokkja sem használ a `field`/`equals`/
`in` hármason kívüli kulcsot, tehát a szigorítás semmit nem tör el a
meglévő tartalomból.
