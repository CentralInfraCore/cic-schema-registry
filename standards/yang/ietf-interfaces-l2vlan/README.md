# ietf-interfaces-l2vlan

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343 + IANA-IF-TYPE)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.1.4}`

VLAN **interfész-entitás** — csak azt írja le, ami magáról a VLAN-ról mint
önálló interfész-objektumról szól: `vlan_id`, `name`, `dhcp_service`
(config), `oper_status`/`mac_table_entries` (state). Mindig fizikai VAGY
logikai interfészhez kötött, soha nem standalone.

`dhcp_service` (`target_kind: DHCPService`) mostantól valódi definícióra
mutat: `../../../general/network/dhcp-service/`.

## #47 — kiválasztva ietf-interfaces-vlan-ból

A korábbi `../ietf-interfaces-vlan/` (v0.1.5, változatlan, aláírt) egy
blokkban írt le két fogalmilag különböző dolgot:

- **VLAN interface entity** (ez a fájl): `vlan_id`, `name`, `dhcp_service`
  — a VLAN mint önálló interfész-objektum.
- **Switchport VLAN policy** (`../cic-switchport-vlan/`): `vlan_mode`,
  `allowed_vlans`, `native_vlan` — egy Ethernet/LAG PORT konfigurációja,
  nem a VLAN interfész saját tulajdonsága.

A [#19](https://github.com/CentralInfraCore/cic-schema-registry/issues/19)
javítás (`native_vlan` hybrid módban is érvényes) helyes volt, de
rávilágított, hogy a két fogalom egy blokkban él — innen a `#47` javaslat.

**Tartalom-eredet:** byte-szintű részhalmaz `../ietf-interfaces-vlan/
ietf-interfaces-vlan.v0.1.5-src2026.yaml`-ból — `vlan_id`/`name`/
`dhcp_service`/`oper_status`/`mac_table_entries` változatlanul átemelve,
`vlan_mode`/`allowed_vlans`/`native_vlan` kihagyva (azok a testvér
`cic-switchport-vlan`-ban élnek).

Adapter-migráció elvégezve — `switch-netconf-adapter`/`ovs-adapter`
`v0.4.2` (és `../../../general/network/network-interface/` `v0.4.2`) már
ezt a blokkot és a `cic-switchport-vlan`-t referenciázza, nem a régi
`ietf-interfaces-vlan`-t.

Fájlonkénti release-aláírás: `v0.1.0`, `v0.1.1`, `v0.1.2` a
`tools/registry_sign.py` (proposals/schema-registry §5) szerint valódi
Vault author-aláírással és CICSourceCA ellenjegyzéssel van ellátva
(`release:`/`cic_countersign:` blokk a fájl végén).

## v0.1.1 — config.name átnevezve vlan_name-re ([#82](https://github.com/CentralInfraCore/cic-schema-registry/issues/82))

Az örökölt `ietf-interfaces-base.name` mező interfész-identitás
(`role: key`, `required_on_create: true`). Ez a blokk egy `name` mezőt
is definiált, csendben felülírva azt egy nem-kulcs, opcionális
display-label mezővel — a `check_yang_extends` (`yang_shape_signature`)
korábban csak `type`/`item_type`-ot hasonlított, a `role`/
`required_on_create` változást nem vette észre. A mező most
`vlan_name`-re át van nevezve; a `yang_shape_signature` is bővült
`role`/`required_on_create` összehasonlítással, hogy ez a hibaosztály
jövőben ne mehessen át észrevétlenül.

## v0.1.2 — extends.version valós pin ([#81](https://github.com/CentralInfraCore/cic-schema-registry/issues/81))

Az `extends.version` eddig `v0.0.dev` placeholder volt — a
`check_yang_extends()` ezt csendben figyelmen kívül hagyta, és mindig a
szülő (`ietf-interfaces-base`) legfrissebb verzióját vette. Most valós
pin: `ietf-interfaces-base@v0.1.4`, amit a `check_yang_extends()` már
ténylegesen `resolve_pin()`-nel ellenőriz — egy nem létező vagy
inkompatibilis verzió mostantól hibaként bukik, nem csendben a
legfrissebbre esik vissza.

## v0.1.3 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
