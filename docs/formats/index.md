# Bestandsformaten & CLI

Overzicht van de **bronformaten** die de toolchain leest of schrijft, en de
**commando’s / `.cmd`-scripts** per bron. Normatieve details staan in de
specificaties; dit is de navigatiehub.

## Conversiematrix (kort)

Rijen = bron, kolommen = doel. Diagonaal = normaliseren naar canonieke vorm.

| Bron ↓ \ Doel → | `.vsa` | `.mvsa` | `.mxl` | `.mscz` |
| --------------- | ------ | ------- | ------ | ------- |
| **`.vsa`** | (waar relevant) | — | `vsa musicxml` | via mxl / templates |
| **`.mvsa`** | — | `mvsa normalize` | `mvsa musicxml` | `mvsa mscz` |
| **`.mxl`** | — | `mxl import` | — | `mxl mscz` |
| **`.mscz`** | — | `mscz import` | `mscz mxl` | — |

Volledige matrix en keuzes: [mvsa-conversies](../plans/mvsa-conversions.md).

## Bestandsformaten

| Extensie | Rol | Spec / profiel | CLI (bron = command) |
| -------- | --- | -------------- | -------------------- |
| [`.vsa`](vsa.md) | Eenstemmige VSA-bron | [Specificatie VSA](../specification/README.md) | [`vsa`](../reference/cli/index.md) |
| [`.mvsa`](mvsa.md) | Meerstemmige tekstbron (draft) | [specification-mvsa](../specification-mvsa/README.md) | [`mvsa`](../reference/cli/mvsa.md) |
| [`.mxl` / `.musicxml`](mxl.md) | MusicXML (Coria / bewerking) | [MusicXML-export](../guides/musicxml-export.md) | [`mxl`](../reference/cli/mxl.md) |
| [`.mscz`](mscz.md) | MuseScore-partituur | Templates / MuseScore-keten | [`mscz`](../reference/cli/mscz.md) |

## Commando’s

| Command | Bron | Man-pagina |
| ------- | ---- | ---------- |
| `vsa` | `.vsa` (+ Markdown-workflows) | [CLI-overzicht](../reference/cli/index.md) |
| `mvsa` ≡ `vsa mvsa` | `.mvsa` | [`mvsa`](../reference/cli/mvsa.md) |
| `mxl` | `.mxl` / `.musicxml` | [`mxl`](../reference/cli/mxl.md) |
| `mscz` | `.mscz` | [`mscz`](../reference/cli/mscz.md) |

Na `pip install -e .` staan `vsa`, `mvsa`, `mxl` en `mscz` op PATH.

## Windows `.cmd`-scripts

In de repo-root (via `scripts\`):

| Script | Roept aan |
| ------ | --------- |
| `scripts\mvsa.cmd` | `python -m vsa.cli_mvsa` |
| `scripts\mxl.cmd` | `python -m vsa.cli_mxl` |
| `scripts\mscz.cmd` | `python -m vsa.cli_mscz` |

Details: [Scripts (cmd)](scripts.md) · [scripts/README](https://github.com/orthodox-ronl/VSA-tooling/blob/main/scripts/README.md).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd -h
scripts\mxl.cmd -h
scripts\mscz.cmd -h
```
