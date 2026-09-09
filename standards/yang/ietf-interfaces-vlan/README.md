# ietf-interfaces-vlan

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8343)
**Kind:** `YANGBlock`, `extends: {name: ietf-interfaces-base, version: v0.0.dev}`

VLAN interfész — az RFC 8343 `ietf-interfaces-base` közös mezőit
kiterjeszti. Lásd `../ietf-interfaces-base/README.md` a kiterjesztési
mechanizmus és a `registrylib`-rés részleteiért.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat `yang/@v0.1.3`-ból (`schemas/ietf/ietf-interfaces-
vlan.yaml`), `metadata.version` → `v0.1.3`. Ugyanaz a ténylegesen
ellenőrzött, kettős aláírás, mint `../ietf-interfaces-base/`-nál.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.

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
