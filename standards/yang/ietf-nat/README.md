# ietf-nat

**Réteg:** `standards/yang/` — külső szabvány szerinti séma (RFC 8512)
**Kind:** `YANGBlock` — önálló, nincs `extends`

NAT (Network Address Translation) building block — RFC 8512 CIC-normalizált
adaptációja. Egy szabály-lista (`config.rules`), `translation_type`
mezővel megkülönböztetve `snat`/`dnat`/`masquerade`-et — **nem három külön
YANGBlock**, ahogy az `issue #48` javaslata is kérte.

## Miért egy blokk, nem három

A három művelet ugyanazt a mezőkészletet osztja meg (protokoll, portok,
interfész-referenciák), csak más `applicable_when`/`required_when`
kombinációval. A `masquerade` a Linux/nftables szóhasználat szerint az
`snat` speciális esete (a forrás-cím a kimenő interfész aktuális címe,
runtime binding), nem önálló fogalom — ezért nincs saját
`translated_address` mezője, szemben az `snat`/`dnat`-tal.

## Amit ez a v0.1.0 SZÁNDÉKOSAN nem fed le

Cím-pool és port-range támogatás (több egyidejű fordítási cím/port egy
szabályhoz) — az `issue #48` thead-je ezt is felvetette, de a scope-ot
tudatosan az egyszerű, egy-cím/egy-port esetre szűkítettem első körben.
Bővíthető, ha valós igény van rá.

## Eredet / provenance

Nem migrált tartalom — újonnan írva ebben a repóban, `issue #48` alapján,
a `theads/thead01.txt` NAT-javaslatát követve. RFC 8512 modulnév
(`ietf-nat`) ellenőrizve: [datatracker.ietf.org/doc/rfc8512](https://datatracker.ietf.org/doc/rfc8512/).

## v0.1.1 — destination_port relaxed, port range constraints, origin kitöltve ([#85](https://github.com/CentralInfraCore/cic-schema-registry/issues/85))

`destination_port`'s `required_when: equals: dnat` kizárta az
address-only (1:1 cím-fordítás, port-fordítás nélküli) DNAT-ot —
törölve, csak `applicable_when` maradt. `range: "0..65535"` hozzáadva
minden port-mezőhöz. `origin: cic-extension` kitöltve a `rules.
item_fields`/`state` összes eddig jelöletlen mezőjén — a mezők
ténylegesen RFC 8512-ből erednek, de az `origin` enum jelenleg nem
tudja kifejezni az `rfc8512` értéket (lásd [#87](https://github.com/CentralInfraCore/cic-schema-registry/issues/87)).

Fájlonkénti release-aláírás: `v0.1.0`, `v0.1.1` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).

## v0.1.2 — validatedBy javítva cic-yang-block-schema@v0.1.9-re ([#88](https://github.com/CentralInfraCore/cic-schema-registry/issues/88))

A `metadata.validatedBy` eddig `cic-primitives`-re mutatott, ami nem a
tényleges belső-struktúra validátor. A valódi struktúra-validátor a
`cic-yang-block-schema` (`#83` óta rekurzív, ténylegesen futtatható) —
`validatedBy` mostantól erre mutat, ténylegesen ellenőrizve
`jsonschema.validate()`-tel a `block_schema` ellen commit előtt.

**Szándékosan nem ennek a fájlnak/PR-nek a része**: a `#88` hosszú-távú
javaslata (aláírt `validation:` lista, tartalmi hash-sel, beépítve az
aláírt payloadba) — az a `tools/registry_sign.py` signing pipeline-t
érintő, külön architektúra-döntést igénylő kezdeményezés.
