# ietf-interfaces-vlan

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.1.4}`

VLAN interfész — az RFC 8343 `ietf-interfaces-base` közös mezőit
kiterjeszti. Lásd `../ietf-interfaces-base/README.md` a kiterjesztési
mechanizmus és a `registrylib`-rés részleteiért.

**⚠ [#47](https://github.com/CentralInfraCore/cic-schema-registry/issues/47)
szerint két fogalmilag különböző dolgot ír le egy blokkban** — egy VLAN
interfész-entitást (`vlan_id`, `name`, `dhcp_service`, `oper_status`,
`mac_table_entries`) ÉS egy switchport VLAN policy-t (`vlan_mode`,
`allowed_vlans`, `native_vlan`). Ez a fájl (`v0.1.5`) VÁLTOZATLAN marad —
aláírt, lezárt — de a szétválasztott utódja már létezik:
`../ietf-interfaces-l2vlan/` (interfész-entitás) +
`../cic-switchport-vlan/` (port-policy). Az adapterek (`switch-netconf-
adapter`, `ovs-adapter`, `../../../general/network/network-interface/`)
`v0.4.2` óta már a két új blokkot referenciázzák, nem ezt — ez a fájl
mostantól csak történeti/olvasási célból marad a registryben.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-interfaces-
vlan.yaml`), `metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen
ellenőrzött, kettős aláírás, mint `../ietf-interfaces-base/`-nál.

Fájlonkénti release-aláírás: `v0.1.5`, `v0.1.6`, `v0.1.7` a
`tools/registry_sign.py` (proposals/schema-registry §5) szerint valódi
Vault author-aláírással és CICSourceCA ellenjegyzéssel van ellátva
(`release:`/`cic_countersign:` blokk a fájl végén).

## v0.1.7 — extends.version valós pin, csak coverage-javítás miatt ([#81](https://github.com/CentralInfraCore/cic-schema-registry/issues/81))

Ugyanaz az indoklás, mint a `v0.1.6`-nál: DEPRECATED blokk, ez a verzió
kizárólag azért készült, hogy a `#81`-ben szigorított
`check_yang_extends()` (valós `resolve_pin()` ellenőrzés placeholder
`v0.0.dev` helyett) ne bukjon el a teljes corpuson emiatt a LATEST fájl
miatt. `ietf-interfaces-base@v0.1.4`.

## v0.1.6 — config.name átnevezve vlan_name-re, csak coverage-javítás miatt ([#82](https://github.com/CentralInfraCore/cic-schema-registry/issues/82))

**Ez a blokk #47 óta DEPRECATED** — az adapterek (`switch-netconf-
adapter`, `ovs-adapter`, `network-interface`) `../ietf-interfaces-l2vlan/`
+ `../cic-switchport-vlan/`-t referenciázzák, nem ezt. A `v0.1.6`
KIZÁRÓLAG azért készült, mert a `#82` javítása (`_YANG_SHAPE_KEYS`
bővítve `role`/`required_on_create`-tal) ugyanazt a hibát — a `name`
mező csendes felülírása — itt is elkapta (ez a blokk innen lett
byte-szinten kiválasztva `ietf-interfaces-l2vlan`-ba, a hiba öröklődött).
A `registry_validate` a teljes corpust ellenőrzi, tehát a szigorítás
enélkül a teljes buildet elpirosította volna egy már ismert, de a régi
ellenőrzés által nem látott hibától. Nem ennek a blokknak az aktív
továbbfejlesztése.

## v0.1.4 — hybrid mód valóban kifejezhető ([#19](https://github.com/CentralInfraCore/cic-schema-registry/issues/19))

A `v0.1.3` (fent leírt módon byte-verbatim) `hybrid` módja saját maga
szerint "vegyes — egyes VLAN-ok tagged, mások untagged", de a
`native_vlan` mező (az egyetlen, ami untagged VLAN-t tud kifejezni)
`applicable_when: equals: trunk` volt — kizárva pont abból a módból,
amiért létezik. `v0.1.4`-ben `native_vlan` hybrid módban is érvényes;
minden más `allowed_vlans`-beli VLAN tagged. Ez a modell (egy natív +
N tagged) megegyezik a gyakori switch-konvencióval (pl. Cisco
"switchport mode general"), és teljesen additív — a `registrylib`
ezt a dialektust (`spec.config`/`spec.state`, nem
`config_surface`/`state_surface`) egyáltalán nem érti (lásd
[#28](https://github.com/CentralInfraCore/cic-schema-registry/issues/28)),
így ez itt csak tartalmi, nem géppel ellenőrzött garancia.

## v0.1.8 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
