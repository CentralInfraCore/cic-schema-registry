# DHCPService

**Réteg:** `general/network/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:network:DHCPService`)

## Mit ír le

DHCP szolgáltatás — cím-pool, lease-kezelés, static reservation. Ugyanaz a
"service resource" mintázat, mint a `../network-interface/`-nél: cím-alapú
routing (`backend`/`provider`/`location`/`id`) + capability-tag mechanizmus.

## Miért kellett

A `standards/yang/ietf-interfaces-vlan`/`ietf-interfaces-l2vlan` blokkok
`dhcp_service` mezője (`type: ref, target_kind: DHCPService`) egy
**lógó referencia** volt — nyolc fájl hivatkozott a `DHCPService`
típusra, de sehol nem létezett a definíciója. Ugyanaz a hibaminta, mint
a `#44`-ben javított lógó `interface_type` referencia.

`../network-interface/` saját maga explicit kizárja: *"Service réteg
(routing protokollok, NAT, DHCP szerver, cloud VPC) — NEM ide
tartozik."* — ez a fájl az a service-réteg objektum, amire ez a
kizárás mutat.

## Scope — adat-oldali leírás, végrehajtás nélkül

Ez a séma azt írja le, MILYEN egy DHCP szolgáltatás
(config/state/operations/notifications) — a tényleges végrehajtási
réteg (pl. `isc-dhcp-adapter`/`kea-adapter`/`dnsmasq-adapter`, a
`../switch-netconf-adapter/`/`../ovs-adapter/` mintáját követve)
**szándékosan nincs itt** — `binding_surface.adapter_capabilities.
known_adapters: []`, explicit megjegyzéssel. A jelenlegi munka fókusza
az adat-oldal; a végrehajtási réteg később készül el.

## Aláírás

Fájlonkénti release-aláírás: `v0.1.0` a `tools/registry_sign.py`
(proposals/schema-registry §5) szerint valódi Vault author-aláírással és
CICSourceCA ellenjegyzéssel van ellátva (`release:`/`cic_countersign:` blokk
a fájl végén).
