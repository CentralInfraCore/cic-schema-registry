# cic-switchport-vlan

**Réteg:** `standards/yang/` — CIC-natív séma (nincs közvetlen RFC alap)
**Kind:** `YANGBlock`, `standalone: false`, nincs `extends` — mixin-mintázat,
ugyanaz mint `../ietf-ip-v4/`/`../ietf-ip-v6/`-nél.

Switchport **VLAN policy** — `vlan_mode` (access/trunk/hybrid),
`allowed_vlans`, `native_vlan`. Ez egy Ethernet/LAG **port**
konfigurációja (mit enged be/ki taggelve/untaggelve), nem egy VLAN
interfész-entitás saját tulajdonsága — ezért nincs saját interfész-
identitása (`extends: ietf-interfaces-base` hiányzik szándékosan), mindig
egy fizikai/LAG porthoz kompozit, ugyanúgy, ahogy `ietf-ip-v4`/`ietf-ip-v6`
mindig egy interfészhez van kötve `extends` nélkül.

## #47 — kiválasztva ietf-interfaces-vlan-ból

Lásd `../ietf-interfaces-l2vlan/README.md` a testvér-blokk és a teljes
indoklás részleteiért.

**Tartalom-eredet:** byte-szintű részhalmaz `../ietf-interfaces-vlan/
ietf-interfaces-vlan.v0.1.5-src2026.yaml`-ból — `vlan_mode`/
`allowed_vlans`/`native_vlan` átemelve.

## native_vlan — szándékosan eltávolított default

A régi blokkban `native_vlan: default: 1` volt. A `#47` javaslata szerint
ez túl erős, vendor-specifikus állítás egy standard building blockban
(pl. Cisco "VLAN 1" konvenció — nem minden vendor/adapter ugyanezt
feltételezi). Itt a `default` mező hiányzik — a defaultot az
adapternek/vendor-profilnak kell megadnia, nem a sémának.

Adapter-migráció elvégezve — lásd `../ietf-interfaces-l2vlan/README.md`.

**Fontos: a `default: 1` hiánya adapter-oldalon SZÁNDÉKOSAN NEM lett
pótolva** a migráció során — sem a `switch-netconf-adapter.v0.4.2`, sem
az `ovs-adapter.v0.4.2` nem ír elő vendor-specifikus native_vlan
defaultot. Ha egy konkrét adapter/vendor-profil ilyet igényel, azt ott
kell explicit hozzáadni, nem itt.

Fájlonkénti release-aláírás: `v0.1.0` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.1 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
