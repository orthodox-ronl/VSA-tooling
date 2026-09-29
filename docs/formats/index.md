# Bestandsformaten & CLI

Overzicht van de **bronformaten** die de toolchain leest of schrijft, en de
**commando’s / `.cmd`-scripts** per bron. Normatieve details staan in de
specificaties; dit is de navigatiehub.

## Conversiematrix (kort)

Rijen = bron, kolommen = doel. Diagonaal = normaliseren naar canonieke vorm.

| Bron ↓ \ Doel → | `.vsa`          | `.mvsa`          | `.mxl`          | `.mscz`             | `.mp3` / audio         | `.midi`              |
| --------------- | --------------- | ---------------- | --------------- | ------------------- | ---------------------- | -------------------- |
| **`.vsa`**      | (waar relevant) | —                | `vsa musicxml`  | via mxl / templates | `vsa audio`            | — (niet gepland)     |
| **`.mvsa`**     | —               | `mvsa normalize` | `mvsa musicxml` | `mvsa mscz`         | `mvsa audio`           | — (niet gepland)     |
| **`.mxl`**      | —               | `mxl import`     | (checklist)     | `mxl mscz`          | `vsa audio`            | — (niet gepland)     |
| **`.mscz`**     | —               | `mscz import`    | `mscz mxl`      | (checklist)         | `vsa audio` (fallback) | — (niet gepland)     |
| **`.midi`**     | —               | —                | —               | —                   | —                      | — (niet gepland)     |

- **Audio (``.mp3`` / ``.ogg`` / ``.wav``):** preview-luisteren; CLI
  [`vsa audio`](../reference/cli/audio.md) — zie [`.mp3` / audio](audio.md).
- **``.midi`` / ``.mid``:** **niet gepland** (preview = audio) — zie [`.midi`](midi.md).
- Volledige matrix / keuzes: [mvsa-conversies](../plans/mvsa-conversions.md).
- Normaalvorm-checklists MXL / MSCZ / PDF: [canonieke checklists](canonical-checklists.md)
  (MXL = vier parts; MSCZ = twee balken SA/TB zonder stem-labels).
  Leesbaarheid partituur: [MSCZ-leesbaarheid](mscz-leesbaarheid.md).

## Bestandsformaten

| Extensie                       | Rol                                 | Spec / profiel                                                                          | CLI (bron = command)                     |
| ------------------------------ | ----------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------- |
| [`.vsa`](vsa.md)               | Eenstemmige VSA-bron                | [Specificatie VSA](../specification/README.md)                                          | [`vsa`](../reference/cli/index.md)       |
| [`.mvsa`](mvsa.md)             | Meerstemmige tekstbron (draft)      | [specification-mvsa](../specification-mvsa/README.md)                                   | [`mvsa`](../reference/cli/mvsa.md)       |
| [`.mxl` / `.musicxml`](mxl.md) | MusicXML (Coria / bewerking)        | [checklists](canonical-checklists.md) · [MusicXML-export](../guides/musicxml-export.md) | [`mxl`](../reference/cli/mxl.md)         |
| [`.mscz`](mscz.md)             | MuseScore-partituur                 | [checklists](canonical-checklists.md) · templates                                       | [`mscz`](../reference/cli/mscz.md)       |
| [`.mp3` / audio](audio.md)     | Preview-luisteren (afgeleide)       | dunne checklist; MuseScore                                                              | [`vsa audio`](../reference/cli/audio.md) |
| [`.midi` / `.mid`](midi.md)    | Los MIDI (niet gepland)             | superseded door audio                                                                   | —                                        |

## Commando’s

| Command             | Bron                          | Man-pagina                                 |
| ------------------- | ----------------------------- | ------------------------------------------ |
| `vsa`               | `.vsa` (+ Markdown-workflows) | [CLI-overzicht](../reference/cli/index.md) |
| `vsa audio`         | `.mxl` / `.vsa` / …           | [`audio`](../reference/cli/audio.md)       |
| `mvsa` ≡ `vsa mvsa` | `.mvsa`                       | [`mvsa`](../reference/cli/mvsa.md)         |
| `mxl`               | `.mxl` / `.musicxml`          | [`mxl`](../reference/cli/mxl.md)           |
| `mscz`              | `.mscz`                       | [`mscz`](../reference/cli/mscz.md)         |

Na `pip install -e .` staan `vsa`, `mvsa`, `mxl` en `mscz` op PATH.

## Bestandsnaamgeving (kort)

In `generated/` bij voorkeur `stem.brontype.doeltype` (laatste = echte
extensie), bv. `alleluia.mvsa.mxl` of `lied.mvsa.mp3`. CLI-`-o` mag simpel
blijven. Details:
[canonieke checklists — naamgeving](canonical-checklists.md#bestandsnaamgeving-conventie).

## Windows `.cmd`-scripts

In de repo-root (via `scripts\`):

| Script             | Roept aan                |
| ------------------ | ------------------------ |
| `scripts\mvsa.cmd` | `python -m vsa.cli_mvsa` |
| `scripts\mxl.cmd`  | `python -m vsa.cli_mxl`  |
| `scripts\mscz.cmd` | `python -m vsa.cli_mscz` |

Details: [Scripts (cmd)](scripts.md) · [scripts/README](https://github.com/orthodox-ronl/VSA-tooling/blob/main/scripts/README.md).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd -h
scripts\mxl.cmd -h
scripts\mscz.cmd -h
```
