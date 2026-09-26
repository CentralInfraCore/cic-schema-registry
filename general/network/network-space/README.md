# NetworkSpace

**Réteg:** `general/network/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:network:NetworkSpace`)

## Mit ír le

Provider-managed, isolált IP-hálózati tér — OCI VCN, AWS VPC, Azure VNet
közös absztrakciója. Ugyanaz a "service resource" mintázat, mint a
`../network-interface/` és `../dhcp-service/` esetében: cím-alapú routing
(`backend`/`provider`/`location`/`id`) + capability-tag mechanizmus.

## Miért kellett

A `theads/thead04.txt` OCI correspondence review (a `cic-module-oracle-cloud`
extractor valós OCI SDK-kontraktusa ellen) találta a legnagyobb konkrét
coverage-rést: a `cic-module-oracle-cloud` már ismeri a `Vcn`/`Subnet`
objektumokat (`module/schemas/core/{vcn,subnet}.json`,
`module/correspondence/vcn.json`), de a registry `general/` rétegében nem
volt canonical megfelelőjük. A `../network-interface/` sémának NEM ez a
scope-ja — az fizikai/logikai portot ír le, nem egy egész izolált
hálózati teret; a review pontosan ezt a rossz absztrakciós próbálkozást
(mindent NetworkInterface-be préselni) zárta ki.

## Scope — adat-oldali leírás, végrehajtás nélkül

Ez a séma azt írja le, MILYEN egy hálózati tér (cím-tartomány, DNS-beállítás,
lifecycle) — a tényleges végrehajtási réteg (pl. egy OCI VCN-adapter)
**szándékosan nincs itt** — `binding_surface.adapter_capabilities.
known_adapters: []`, explicit megjegyzéssel, ugyanúgy mint a
`../dhcp-service/`-nél.

Route-olás (route-table/route), security (network-security-group/
security-rule) és internet/NAT gateway-ek NEM tartoznak ide — ezek a
thead04 által javasolt, még meg nem írt `general/network/` tagok.

## Kapcsolódó séma

`../subnet/` — egy NetworkSpace-en belüli, cím-tartomány szerint
particionált al-hálózat, `network_space_ref` (`cic-reference`) mezőn
keresztül hivatkozik vissza erre a sémára.

## Aláírás

Nincs — ez `v0.1.dev`, még nem lett release-elve/aláírva
(`tools/registry_sign.py`).
