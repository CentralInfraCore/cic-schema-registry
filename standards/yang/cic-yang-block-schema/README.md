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

Fájlonkénti release-aláírás: `v0.1.4`, `v0.1.5`, `v0.1.6`, `v0.1.7`,
`v0.1.8` és `v0.1.9` a `tools/registry_sign.py` (proposals/schema-registry
§5) szerint valódi Vault author-aláírással és CICSourceCA ellenjegyzéssel
van ellátva (`release:`/`cic_countersign:` blokk a fájl végén).

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

## v0.1.8 — origin enum bővítve ([#87](https://github.com/CentralInfraCore/cic-schema-registry/issues/87), rövid táv)

`field_schema.origin` (és a testvér `notifications[].origin`) enumja
kibővítve `rfc8512`-vel (`ietf-nat` saját `metadata.source`-a ez, de az
enum eddig nem tudta kifejezni) és `iana-if-type`-tal
(`ietf-interfaces-l2vlan` saját `metadata.source`-a "RFC 8343 +
IANA-IF-TYPE l2vlan", ugyanez a hiányzó kategória).

**Szándékosan NEM ennek a verziónak a része:** a corpus meglévő
mezőinek utólagos átcímkézése az új értékekkel (pl. `ietf-nat` mezői
jelenleg mind `cic-extension`, `ietf-interfaces-l2vlan.vlan_id`
jelenleg `rfc8343`) — ez RFC-szöveg-szintű ellenőrzést igényelne a
`#46` mintájára, nem csak enum-bővítést. A `#87` hosszabb-távú fele (egy
strukturált `provenance` blokk `authority`/`document`/`module`/
`relation: direct|normalized|inspired-by|extension`-nel, a flat `origin`
enum helyett/mellett) szintén nem itt dől el.

## v0.1.9 — meta-séma rekurzívvá téve ([#83](https://github.com/CentralInfraCore/cic-schema-registry/issues/83))

`item_fields`, `properties` és a notification `payload.items` eddig
csak `type: array`/`type: object` szinten voltak megkötve — a belsejük
(egy lista elemeinek mezői, egy object belső mezői) teljesen
validálatlan volt. Mindhárom most visszahivatkozik `#/$defs/field_schema`-ra.

`field_schema.required` `[name, type]`-ról `[type]`-ra szűkült — a
`name` most a HASZNÁLATI HELY (`config`/`state`/`item_fields`/
`notifications[].payload`) felelőssége, `allOf: [$ref field_schema,
required: [name]]`-lel hozzáadva. A `properties` (dict-alakú, kulcs =
mezőnév) NEM kapott extra `name`-követelményt — a valós corpus
`properties`-tartalma (pl. `ietf-ip-v6`/`ietf-interfaces-base`
statisztikák, `dhcp6_overrides`) sosem hordoz `name` kulcsot a dict
értékén belül, mert a dict-kulcs maga a mezőnév. Egy egységes
`field_schema`-ra való `name`-kényszerítés minden ilyen fájlt
elbuktatott volna.

Ellenőrizve KÉTSZER: (1) a teljes `standards/yang` corpus minden
`config`/`state`/`item_fields`/`properties`/`notifications.payload`
tartalma megfelel ennek a szigorúbb struktúrának — semmit nem tör el.
(2) a `jsonschema` könyvtárral ténylegesen lefuttatva a `block_schema`-t
minden LATEST YANGBlock fájl ellen: 12/12 tisztán validál. (A régi,
már lecserélt verziók — pl. `cic-yang-block-schema.v0.1.3`–`v0.1.6`
hiányzó `metadata.source`-szal, `ietf-lldp.v0.1.3` `rfc8516`-tal —
helyesen buknak, ezek pontosan a `#101`/`#42` már javított, korábbi
hibái, nem regresszió.)

**Fontos korlát:** ez a meta-séma jelenleg NINCS bekötve semmilyen
valódi `jsonschema.validate()` hívásba a corpus ellen (az egyetlen
`jsonschema.validate` a `tools/infra.py`-ban a `project.yaml`-t
validálja, más sémával) — ez a fix a séma DEFINÍCIÓJÁT teszi belsőleg
helyessé, de önmagában nem ad tényleges enforcementet, amíg nincs
mögötte futó validátor (lásd `#88`/`#101`).
