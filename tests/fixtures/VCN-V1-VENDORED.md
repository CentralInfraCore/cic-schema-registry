# Vendored — ne szerkeszd

Ez a könyvtár a `cic-factory` `fixtures/vcn-v1` bájtra azonos másolata (forrás commit:
`e5978f50d2512c5ac7536b9d81ffb1f054b75525`, PR `CentralInfraCore/cic-factory#37`). A `MANIFEST.sha256` minden fájlt rögzít, a
`tests/test_tools/test_vcn_fixture.py` ellenőrzi. Az `expected/` fájlokat nem igazítjuk a saját kimenetünkhöz; ha hibásnak
tűnnek, a forrásnál kell javítani. A registry a fixture 4. szakaszáért felel (`network-space.correspondence.yaml`).

`generate.py` (a forrás generátora, `--check` módban ellenőrzi a fájlokat) szándékosan **nincs** vendorolva: nem része a
`MANIFEST.sha256`-nak, és a repo `black`-je átformázná. A fixture forrása és generátora: `cic-factory` `fixtures/vcn-v1/`
(a fenti commit). A `README.md` hivatkozik rá — ez a forrásra vonatkozik.
