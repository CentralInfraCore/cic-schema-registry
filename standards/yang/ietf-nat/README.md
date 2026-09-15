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

Fájlonkénti release-aláírás: `v0.1.0` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).
