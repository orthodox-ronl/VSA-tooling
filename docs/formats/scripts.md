# Windows `.cmd`-scripts (formaten)

Dunne wrappers rond de Python-entrypoints. Ze doen `_ensure` (venv / `vsa`
importeerbaar) en roepen daarna de top-level CLI aan.

## Formaat-scripts

| Script                 | Equivalent                            | Bron                 |
| ---------------------- | ------------------------------------- | -------------------- |
| `scripts\mvsa.cmd`     | `mvsa …` / `python -m vsa.cli_mvsa`   | `.mvsa`              |
| `scripts\mxl.cmd`      | `mxl …` / `python -m vsa.cli_mxl`     | `.mxl` / `.musicxml` |
| `scripts\mscz.cmd`     | `mscz …` / `python -m vsa.cli_mscz`   | `.mscz`              |
| `scripts\markdown.cmd` | `markdown …` / `python -m vsa.cli_md` | `.md` / `.markdown`  |

Na `pip install -e .` kun je ook zonder script `mvsa`, `mxl`, `mscz`,
`markdown` op PATH aanroepen. Geen `md`-entrypoint: op Windows is `md`
makedir. De `.cmd`-bestanden werken altijd vanuit de repo-root.

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling

scripts\mvsa.cmd -h
scripts\mvsa.cmd validate examples\mvsa
scripts\mvsa.cmd normalize examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.normalized.mvsa
scripts\mxl.cmd normalize generated\alleluia.mxl -o generated\alleluia.norm.mxl
scripts\mscz.cmd mxl generated\alleluia.mscz -o generated\y.mxl
scripts\mscz.cmd svg generated\alleluia.mscz -o generated\alleluia.svg
scripts\mscz.cmd pdf generated\alleluia.mscz -o generated\alleluia.pdf
scripts\mscz.cmd normalize generated\alleluia.mscz --layout partituur
scripts\markdown.cmd pdf examples\consumer-minimal\content-source\index.md
```

In handleidingen en voorbeelden: altijd `scripts\*.cmd` (of `vsa`/`mvsa`/`mxl`/`mscz`/`markdown`
op PATH na install). Geen `python -m vsa.cli…` als gebruikerscommando.

## Overige repo-scripts

Installatie, testen, docs-build: zie
[scripts/README.md](https://github.com/orthodox-ronl/VSA-tooling/blob/main/scripts/README.md)
(`test`, `serve`, `build`, `run-example`, …).

## Man-pagina’s

- [`mvsa`](../reference/cli/mvsa.md)
- [`mxl`](../reference/cli/mxl.md)
- [`mscz`](../reference/cli/mscz.md)
- [`markdown`](../reference/cli/markdown.md)
- [CLI-overzicht](../reference/cli/index.md)

## Zie ook

- [Formaten & CLI — overzicht](index.md)
