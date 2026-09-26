# Subnet

**Réteg:** `general/network/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:network:Subnet`)

## Mit ír le

Egy `../network-space/` (VCN/VPC/VNet) belüli, cím-tartomány szerint
particionált al-hálózat — OCI Subnet, AWS Subnet, Azure Subnet közös
absztrakciója. Ugyanaz a coverage-rés, egy szinttel lejjebb, mint a
`../network-space/`-nél — lásd ott a "Miért kellett" szakaszt.

## Scope — adat-oldali leírás, végrehajtás nélkül

Kizárólag a particionálás maga (cím-tartomány, `network_space_ref`-en
keresztüli hovatartozás, elhelyezkedés, publikus elérhetőség). NEM
tartozik ide:

- route-tábla-hozzárendelés (`general/network/route-table/`, még nincs megírva)
- security group-hozzárendelés (`general/network/network-security-group/`, még nincs megírva)
- a DHCP-vel szétosztott DNS/search-domain opciók (OCI `DhcpOptions`-szerű
  fogalom) — ez külön canonical objektum, lásd `../dhcp-service/README.md`-t:
  a `DHCPService` egy valódi DHCP szervert ír le, az OCI `DhcpOptions` csak
  DNS/search-domain beállítást egy subnet/VCN szinten — a két fogalom
  szándékosan nem lett összemosva (thead04).

A tényleges végrehajtási réteg (pl. egy OCI Subnet-adapter) **szándékosan
nincs itt** — `binding_surface.adapter_capabilities.known_adapters: []`.

## Aláírás

Nincs — ez `v0.1.dev`, még nem lett release-elve/aláírva
(`tools/registry_sign.py`).
