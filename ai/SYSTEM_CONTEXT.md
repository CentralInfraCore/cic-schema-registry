# System Context (AI számára)

Olvasd el mielőtt bármit módosítasz.

---

## Mi ez a rendszer?

Ez a szakasz alább a `base-repo` sablon öröklött, generikus leírása — az
ALATTA lévő build/signing infrastruktúra a `cic-schema-registry`-re is
érvényes, de ez a repó ennél specifikusabb: **konszolidált séma-registry**,
`general`/`standards`/`providers` könyvtárszerkezettel, egy séma = egy fájl
elven, fájlonként független verziózással és aláírással (nem bundle-release).
A teljes tervezés: `cic-primitives` repó, `proposals/schema-registry/README.md`.
Ennek a repónak a saját, valódi állapota: `CLAUDE.md` "Jelenlegi, valódi
állapot" szakasza — ez a fájl (öröklött scaffold) NEM frissült még teljesen
a registry-specifikus tartalommal.

Az öröklött, generikus leírás:

A `base-repo` egy **infrastruktúra sablon**. Nem tartalmaz üzleti logikát — a szerepe az, hogy a belőle
származtatott production repók (pl. CIC-Schemas, CIC-Relay) egységes build, signing és release
infrastruktúrát örököljenek Renovate-en keresztül.

A bizalom alapja: minden commit és release artefaktum kriptográfiailag aláírt.
Az aláírás Vault Transit ECDSA SHA256 alapú, a tanúsítványlánc a CICRootCA-ig visszakövethető.

---

## A három réteg

```
tools/compiler.py     CLI belépési pont — argument parsing, service wiring
tools/infra.py        ReleaseManager — Git/Vault workflow orchestrátor
tools/schemalib/      Schema pipeline library (csak repo_type=schema esetén aktív)
  ├── loader.py       YAML betöltés $ref feloldással
  ├── validator.py    Integritás ellenőrzés + jsonschema validálás
  └── artifact.py     Checksum, signing payload, artefaktum összeállítás
tools/releaselib/     Git/Vault service absztrakciók
  ├── git_service.py
  ├── vault_service.py
  └── exceptions.py
tools/finalize_release.py  IDEIGLENES — CIC central signing (relay váltja fel)
```

---

## A signing mechanizmus

`tools/git_hook_commit-msg.sh` — minden `git commit` triggereli:

1. `git write-tree` → staged tree snapshot
2. Determinisztikus tar stream → SHA256 digest (base64)
3. Vault Transit: `POST /v1/transit/sign/cic-my-sign-key` (prehashed ECDSA)
4. Vault KV: `GET /v1/cic-my-sign-key/data/crt` → PEM tanúsítvány
5. `[signing-metadata]` + `[certificate]` blokk → commit message végére

**Ez a formátum invariáns.** Minden aláíró komponensnek (fejlesztő, Renovate bot) ugyanezt kell produkálnia.

---

## repo_type routing

A `project.yaml` `compiler_settings.repo_type` értéke határozza meg, mely parancsok elérhetők:

| repo_type | Elérhető parancsok |
|---|---|
| `module` | `release`, `get-name` |
| `schema` | `release`, `release-dependency`, `release-schema`, `validate`, `get-name` |
| `workflow` | `release`, `get-name` |

---

## Nyitott trust bootstrap probléma

A `finalize_release.py` ideiglenes megoldás a CIC central signing-re.
A végleges megoldás a CIC-Relay recorder komponense lesz — amikor a relay trust ecosystem bootstrapped.