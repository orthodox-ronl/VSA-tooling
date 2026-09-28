# Scripts voor VSA Tooling

Uitvoerbare commando's in `scripts/` (PATH: `.\scripts`). Org-conventie:
https://github.com/orthodox-ronl/bron/blob/main/docs/specs/repo-scripts.md

Scripts mogen redactionele `content-source` niet herschrijven.
CI gebruikt `examples\consumer-minimal\content-source`.

## Commando's

| Commando | Doel |
| -------- | ---- |
| `test` | pytest (`test -v` i.p.v. test-verbose) |
| `check` | CI-spiegel: pytest + consumer-minimal validate/build-markdown |
| `serve` | MkDocs preview zonder TEv2 |
| `serve-tev2` | MkDocs preview met TEv2 |
| `build` | TEv2 + MkDocs `--strict` (CI-pariteit) |
| `build --no-tev2` | MkDocs zonder TEv2 |
| `clean` | tijdelijke bestanden weg |
| `import` | zip uit Downloads uitpakken |
| `run-example` | `vsa` op een voorbeeld-`.vsa` |
| `mvsa` | top-level `mvsa` (≡ `vsa mvsa`; bron `.mvsa`) |
| `mxl` | top-level `mxl` (import / mscz; bron `.mxl`) |
| `mscz` | top-level `mscz` (import / mxl; bron `.mscz`) |
| `check-docs` | docs-hygiene |

Python-helpers blijven in `scripts/`. Oude namen (`docs-serve`, `ci`, `bootstrap`) zijn aliases.

Geen aparte bootstrap-stap: `_ensure` checkt PATH (Python 3.14, optioneel Node) en pip't packages.
