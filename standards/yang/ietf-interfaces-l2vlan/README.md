# ietf-interfaces-l2vlan

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343 + IANA-IF-TYPE)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.0.dev}`

VLAN **interfész-entitás** — csak azt írja le, ami magáról a VLAN-ról mint
önálló interfész-objektumról szól: `vlan_id`, `name`, `dhcp_service`
(config), `oper_status`/`mac_table_entries` (state). Mindig fizikai VAGY
logikai interfészhez kötött, soha nem standalone.

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

**⚠ Adapter-migráció még nincs elvégezve.** A `switch-netconf-adapter`/
`ovs-adapter` egyelőre a régi `ietf-interfaces-vlan`-t referenciázza —
az átállás erre a két blokkra szándékosan külön lépés (nem ennek a
PR-nek a része), mert már aláírt `AdapterContract` fájlokat érintene.

Fájlonkénti release-aláírás: `v0.1.0` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).
