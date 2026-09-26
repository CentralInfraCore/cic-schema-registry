# DHCPOptions

**Réteg:** `general/network/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:network:DHCPOptions`)

## Mit ír le

A DHCP-vel egy `../network-space/` (VCN/VPC/VNet) belül szétosztott
bootstrap-paraméterek: DNS szerverek, domain name, search domain lista,
NTP szerverek — OCI `DhcpOptions`, AWS DHCP Options Set közös absztrakciója.

## Miért kellett — DHCPService != OCI DhcpOptions

A `theads/thead04.txt` OCI correspondence review explicit kimondta:
*"OCI DhcpOptions != CIC DHCPService... Nem kéne erőszakkal összekötni
őket. Valószínűleg hiányzik egy olyan canonical fogalom, mint DHCPOptions/
NetworkBootstrapOptions/SubnetClientConfiguration."*

A `../dhcp-service/` **egy valódi DHCP szervert** ír le — cím-pool,
lease-kezelés, static reservation (lásd annak saját README-jét, ami
explicit adat-oldal-only szándékkal épült, nem OCI-mappinggel). Az OCI
`DhcpOptions` ezzel szemben **nem szerver** — csak egy kis
paraméter-halmaz (elsősorban DNS + search domain), amit a felhő saját,
be nem konfigurálható DHCP-implementációja oszt szét a VCN-en belüli
instance-oknak. A két fogalom összemosása lett volna a hiba, amit a
review elkerülendőnek jelölt — ez a fájl a hiányzó, önálló canonical
válasz.

## Kapcsolat a NetworkSpace/Subnet-hez

`config_surface.network_space_ref` köti a szülő `../network-space/`-hez
(OCI-n és AWS-en is VCN/VPC-szinten él egy DHCP-paraméter-halmaz). Az,
hogy egy adott `../subnet/` felül tudja-e írni a szülő NetworkSpace
alapértelmezett DHCPOptions-ét (OCI-n igen, per-subnet override
lehetséges) — **ma nincs modellezve** a `../subnet/` sémában. Ez szándékos,
dokumentált nyitott pont, nem ennek az egy munkamenetnek kellett volna
eldöntenie.

## Scope — adat-oldali leírás, végrehajtás nélkül

`binding_surface.adapter_capabilities.known_adapters: []`, ugyanúgy mint
a `../network-space/`/`../subnet/`-nél — még nincs execution-layer adapter.

## Aláírás

Nincs — ez `v0.1.dev`, még nem lett release-elve/aláírva
(`tools/registry_sign.py`).
