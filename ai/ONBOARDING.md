# Onboarding (AI)

## 1 perc alatt

- **Mi ez:** a CIC ökoszisztéma konszolidált séma-tárolója (`general/`,
  `standards/`, `providers/`) — NEM egy template, amiből más repók
  örökölnek. A `tools/compiler.py`/`tools/infra.py` réteg a base-repo-ból
  öröklött, bundle-alapú tooling maradványa; a registry-specifikus
  munka `tools/registrylib/` + `tools/registry_validate.py` +
  `tools/registry_sign.py`.
- **Entrypoint:** `tools/registry_validate.py` — a valódi corpus-check
  (base-chain coverage + verzió-evolúció). `tools/generate_latest.py` —
  LATEST.yaml + frozen-file guard. `tools/registry_sign.py` — fájlonkénti
  Vault+CICSourceCA aláírás.
- **Signing mechanizmus:** `tools/git_hook_commit-msg.sh` — ECDSA SHA256
  Vault Transit, staged tree digest → signature + certificate a commit
  message-be (commit-szintű). Fájlonkénti tartalmi aláírás külön,
  `tools/registry_sign.py`-jal.
- **Séma-tartalom:** `tools/registrylib/` (`paths.py`, `identity.py`,
  `coverage.py`, `bundle.py`, `latest.py`, `signing.py`) — NEM
  `tools/schemalib/` (az nem létezik ebben a repóban).
- **Mérce:** `make test` — pytest suite, jelenleg ~86% coverage
  (`tools/` egészére, `make infra.coverage`). Ez kell zöldnek lennie.
- **Konfiguráció:** `project.yaml` — a base-repo örökölt
  `compiler_settings`-je (a registry-specifikus tooling nem ebből
  konfigurálódik).

## Mielőtt bármit írsz

Olvasd el: `ai/SYSTEM_CONTEXT.md`, `CLAUDE.md` "Jelenlegi, valódi
állapot" — ott van a legfrissebb, pontos rés-lista (mit NEM ellenőriz
ma semmi).

**Ami kész, ne írd felül:**

| Implementált | Állapot |
|---|---|
| `tools/registrylib/` (`paths.py`, `identity.py`, `coverage.py`) | Kész, tesztelve — de lásd `CLAUDE.md` a mélységi réseket (`#79`/`#80`/`#94`/`#96`) |
| `tools/registry_sign.py` + `tools/registrylib/signing.py` | Kész, élő teszttel bizonyítva — 52/52 fájl aláírva |
| `tools/generate_latest.py` (LATEST.yaml + frozen-file guard) | Kész, 9 könyvtáron |
| `tools/git_hook_commit-msg.sh` signing hook | Élesben használt |

## Hogyan ellenőrzöl

```bash
make test                # pytest suite — ez kell zöldnek
make registry.validate   # a valódi corpus-check (base-chain coverage + verzió-evolúció)
make registry.latest     # LATEST.yaml drift + frozen-file guard
make build                # Docker image build
```

`make validate` (örökölt `tools/compiler.py validate`) létezik, de csak
egy bundle-template-et tölt be, NEM a registry tartalmát — ezért nincs
a CI-ben, ne használd corpus-check gyanánt.

## Ha gond van

Javasolj `project.yaml` schema változást (`project.schema.yaml`-hoz), ne térj el csendben a meglévő signing formátumtól.