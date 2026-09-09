# NetworkInterface

**Réteg:** `general/network/` — platform-agnosztikus domain composition
**Kind:** `DomainComposition` (`cic:network:NetworkInterface`)

## Mit ír le

Fizikai/logikai hálózati interfész (switch/router port, VLAN, bond) mint
`ManagedEntity` specializáció — ugyanaz a "termék" szintű megközelítés,
mint a `general/storage/storage-resource/` és `general/compute/
compute-resource/` esetében: cím-alapú routing (`backend`/`provider`/
`location`/`id`) + capability-tag mechanizmus a variancia kezelésére.

## Valós, konkrét kapocs a `standards/` réteghez

A `binding_surface.adapter_capabilities.known_adapters` **explicit
megnevezi**, melyik adapter melyik `standards/yang/` YANGBlock-okra épül:

```yaml
- name: switch-netconf-adapter
  backend: switch
  yang_blocks: [ietf-interfaces-physical, ietf-interfaces-vlan]
```

Ez egy konkrét, valós bizonyíték arra, hogy a három-réteg (`general`/
`standards`/`providers`) modell működik: a `general/` domain composition
tudja, hogy a `standards/yang/` alatti IETF building block-okra
támaszkodik, név szerint — de a séma-szintű mezőket nem veszi át, csak
hivatkozik rájuk.

## Ismételten előforduló inkonzisztencia — harmadik eset

`binding_surface.adapter: network-adapter` — ez **egyik valós adapter
nevével sem egyezik** (a valósak: `ovs-adapter`, `switch-netconf-adapter`).
Ez **pontosan ugyanaz a hiba-minta**, mint amit a `cic-kubernetes`-nél
találtunk (`kubernetes-adapter`, ami szintén egyik valós adapterrel sem
egyezett) — tehát ez nem egyedi elgépelés, hanem **egy visszatérő,
rendszerszintű mintázat** a forrás-repókban: a domain composition egy
generikus `<domain>-adapter` placeholder nevet ír a `binding_surface.
adapter` mezőbe, amit sosem cseréltek ki a tényleges adapter(ek)
nevére. Érdemes lenne ezt egy közös issue-ban jelezni mindhárom forrás-
repóban (`cic-network`, `cic-kubernetes`, és ellenőrizni `cic-storage`/
`cic-compute`-ot is — azoknál a mező helyesen `storage-adapter`/nem
egyértelmű compute-nál, mert ott 3 adapter van, cím szerint routolva,
nincs egyetlen `adapter:` mező).

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-network` repó `network/@v0.4.1` tag-jéből
(`schemas/domain/network-interface.yaml`), `metadata.version` a release
verziójára (`v0.4.1`) állítva, plusz minimális whitespace-tisztítás.
**Fontos**: NEM a `devel` ágon lévő, hiányos (adapterek nélküli)
`schemas/examples/network-interface.yaml`-ből származik — az egy régebbi,
korlátozottabb változat.

**Ténylegesen, `openssl`-lel ellenőrizve**: szerzői Vault Transit aláírás +
CICSourceCA ellenjegyzés a `build_hash` felett, mindkettő érvényes, ugyanaz
a 2026-os CA-lánc, mint minden korábbi migrációnál.

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben.
