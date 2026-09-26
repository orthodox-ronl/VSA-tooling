# Windows `.cmd`-scripts (formaten)

Dunne wrappers rond de Python-entrypoints. Ze doen `_ensure` (venv / `vsa`
importeerbaar) en roepen daarna de top-level CLI aan.

## Formaat-scripts

| Script | Equivalent | Bron |
| ------ | ---------- | ---- |
| `scripts\mvsa.cmd` | `mvsa …` / `python -m vsa.cli_mvsa` | `.mvsa` |
| `scripts\mxl.cmd` | `mxl …` / `python -m vsa.cli_mxl` | `.mxl` / `.musicxml` |
| `scripts\mscz.cmd` | `mscz …` / `python -m vsa.cli_mscz` | `.mscz` |

Na `pip install -e .` kun je ook zonder script `mvsa`, `mxl`, `mscz` op PATH
aanroepen. De `.cmd`-bestanden werken altijd vanuit de repo-root.

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling

scripts\mvsa.cmd -h
scripts\mvsa.cmd validate examples\mvsa
scripts\mxl.cmd import generated\alleluia.mxl --pitch doremi -o generated\x.mvsa
scripts\mscz.cmd mxl generated\alleluia.mscz -o generated\y.mxl
```

## Overige repo-scripts

Installatie, testen, docs-build: zie
[scripts/README.md](https://github.com/orthodox-ronl/VSA-tooling/blob/main/scripts/README.md)
(`test`, `serve`, `build`, `run-example`, …).

## Man-pagina’s

- [`mvsa`](../reference/cli/mvsa.md)
- [`mxl`](../reference/cli/mxl.md)
- [`mscz`](../reference/cli/mscz.md)
- [CLI-overzicht](../reference/cli/index.md)

## Zie ook

- [Formaten & CLI — overzicht](index.md)
