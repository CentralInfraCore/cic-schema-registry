# Fejlesztői Munkafolyamat

Ez a dokumentum a séma keretrendszerrel való interakció tipikus munkafolyamatait vázolja fel, az első beállítástól egy új kiadás létrehozásáig.

## Első Beállítás

Mielőtt elkezdenéd, győződj meg róla, hogy a következő előfeltételek telepítve vannak a gépeden:
- `docker`
- `docker-compose`
- `make`
- `git`

Kövesd ezeket a lépéseket a projekt inicializálásához a repository klónozása után:

1.  **A Vault Aláíró Ügynök Elindítása:**
    A projekthez szükség van egy futó Vault példányra a kiadási artefaktumok aláírásához. Egy segédszkript biztosított egy ideiglenes, helyi Vault szerver futtatásához fejlesztés céljából.

    ```sh
    # Ezt a projekt gyökeréből kell futtatni egy külön terminálban
    ./tools/vault-sign-agent.sh -k /eleresi/ut/a/kulcsodhoz.pem -c /eleresi/ut/a/certedhez.crt --root-ca-file /eleresi/ut/a/CICRootCA.crt
    ```
    Ez az ügynök a háttérben fog futni.

2.  **Python Függőségek Telepítése:**
    Ez a parancs lefordítja a `requirements.in` fájlt, és telepíti az összes szükséges Python csomagot egy helyi `./p_venv` könyvtárba, amelyet a Docker konténer gyorsítótárként használ.

    ```sh
    make infra.deps
    ```

3.  **Docker Image-ek Építése:**
    Építsd meg a `setup` és `builder` szolgáltatásokhoz szükséges Docker image-eket.

    ```sh
    make build
    ```

4.  **A Fejlesztői Konténer Elindítása:**
    Ez elindítja a `builder` konténert a háttérben.

    ```sh
    make up
    ```

5.  **Git Hook-ok Inicializálása:**
    Ez a szkript beállítja a `commit-msg` Git hookot, amely automatikusan aláírja a commitjaidat a futó Vault ügynök segítségével.

    ```sh
    make repo.init
    ```

A környezeted most már teljesen be van állítva és készen áll a fejlesztésre.

## Napi Fejlesztési Feladatok

Ez a tipikus ciklus, amelyet a sémák módosításakor vagy létrehozásakor követni fogsz.

1.  **Séma Módosítása:**
    Végezd el a kívánt módosításokat egy sémafájlon a `general/`,
    `standards/` vagy `providers/` alatt (NEM `/schemas` — az egy
    örökölt, ebben a repóban nem használt könyvtárnév). Egy már
    közzétett (release-aláírt) `-src<év>.yaml` fájlt SOHA ne szerkessz
    helyben — új verziófájlt hozz létre helyette.

2.  **Validálás Futtatása:**
    A `make validate` parancs (örökölt `tools/compiler.py validate`)
    NEM validálja a registry tartalmát — csak egy bundle-template-et
    tölt be. A valódi ellenőrzés:

    ```sh
    make registry.validate   # base-chain coverage + verzió-evolúció
    make registry.latest     # LATEST.yaml drift + frozen-file guard
    ```

3.  **Tesztek Futtatása:**
    Annak érdekében, hogy maguk az eszközök is megfelelően működjenek, futtasd a `pytest` tesztcsomagot.

    ```sh
    make test
    ```

4.  **Módosítások Commit-olása:**
    Amikor készen vagy, commit-old a módosításaidat. A `commit-msg` hook automatikusan lefut, csatlakozik a helyi Vault ügynökhöz, és egy aláírási blokkot fűz a commit üzenetedhez.

    ```sh
    git add .
    git commit -m "feat: Séma frissítése új tulajdonságokkal"
    ```

## Kiadás Létrehozása

**Nincs bundle-release, nincs kiadási ág, nincs Git tag** — ez az
örökölt base-repo modell, amit a `proposals/schema-registry` §5
explicit visszavont. Minden séma-fájl a saját, önálló, fájlonként
aláírt egysége (`proposals/schema-registry/README.md` §5 a teljes
indoklásért).

Amikor egy séma-fájl tartalma véglegesített, aláírod közvetlenül,
branch/tag nélkül:

1.  **Győződj meg róla, hogy a fájl tartalma végleges** — az aláírás
    egyszeri, fájlonkénti (`AlreadySignedError`, ha újra megpróbálod).

2.  **Futtasd az aláíró parancsot:**

    ```sh
    python -m tools.registry_sign general/network/dhcp-service/dhcp-service.v0.1.0-src2026.yaml
    ```

    Ehhez futó Vault (az 1. lépésben indított `vault-sign-agent.sh`) és
    `cic-countersign` szolgáltatás szükséges — lásd a script
    környezeti változóit (`VAULT_ADDR`, `VAULT_TOKEN`,
    `COUNTERSIGN_ADDR`, `COUNTERSIGN_CA_FILE`, `DEV_VAULT_CA_FILE`).

3.  **Mi történik:**
    - `build_hash` = `sha256` a fájl nyers bájtjai felett.
    - Szerzői Vault Transit aláírás a `build_hash` felett.
    - CICSourceCA ellenjegyzés (mTLS-en keresztül, `vault-mtls-client`).
    - `release:`/`cic_countersign:` blokk hozzáfűzve a fájl végéhez
      (byte-szinten, a meglévő tartalom változatlanul marad).

4.  **Commit + PR:** a most aláírt fájlt commitold és PR-ozd `main`
    ellen, mint bármilyen más módosítást — nincs külön "release"
    Git-művelet.
