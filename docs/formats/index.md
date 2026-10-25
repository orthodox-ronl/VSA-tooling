# Bestandsformaten & CLI

Overzicht van de **bronformaten** die de toolchain leest of schrijft, en de
**commando’s / `.cmd`-scripts** per bron. Normatieve details staan in de
specificaties; dit is de navigatiehub.

**Contracten (checklists, layoutprofielen, Score-IR/OSMD):** start bij de
[contract-index](contract-index.md). Herkomst van `products`-siblings:
[products-meta](products-meta.md). Straat-CLI’s / producten (plan):
[straat-CLIs](../plans/straat-clis.md).

## Conversiematrix (kort)

Rijen = bron, kolommen = doel. Diagonaal = normaliseren naar canonieke vorm.

| Bron ↓ \ Doel → | `.vsa`                          | `.mvsa`                                    | `.mxl`                     | `.mscz`              | `.mp3` / audio         | `.midi`              |
| --------------- | ------------------------------- | ------------------------------------------ | -------------------------- | -------------------- | ---------------------- | -------------------- |
| **`.vsa`**      | validate (geen `vsa normalize`) | —                                          | `vsa musicxml`             | via mxl / templates  | `vsa audio`            | — (niet gepland)     |
| **`.mvsa`**     | —                               | `mvsa normalize` / `kuiser` / `transpose`  | `mvsa mxl` · `score-ir`    | `mvsa mscz`          | `mvsa mp3`/`ogg`/`wav` | — (niet gepland)     |
| **`.mxl`**      | —                               | `mxl mvsa`                                 | `mxl normalize`            | `mxl mscz`           | `vsa audio`            | — (niet gepland)     |
| **`.mscz`**     | —                               | `mscz mvsa`                                | `mscz mxl`                 | `mscz normalize`     | `vsa audio` (fallback) | — (niet gepland)     |
| **`.midi`**     | —                               | —                                          | —                          | —                    | —                      | — (niet gepland)     |

- **Audio (``.mp3`` / ``.ogg`` / ``.wav``):** preview-luisteren; CLI
  [`vsa audio`](../reference/cli/audio.md) — zie [`.mp3` / audio](audio.md).
- **``.midi`` / ``.mid``:** **niet gepland** (preview = audio) — zie [`.midi`](midi.md).
- **Zoektekst in canonieke `.vsa` / `.mvsa`:** veld `zoektekst` in
  YAML-frontmatter — [zoektekst](zoektekst.md). Extractie / export:
  [`vsa text`](../reference/cli/text.md) op `.vsa` / `.mvsa` / MusicXML /
  `.mscz` (geen aparte matrixkolom; schrijft geen `.mvsa`-sibling). Alias op
  MuseScore-bron: [`mscz text`](../reference/cli/mscz.md).
- Volledige matrix / keuzes: [mvsa-conversies](../plans/mvsa-conversions.md).
- **Score → `.mvsa`** (`.mxl` / `.mscz`): **werkbank-bewerkvorm** (niet
  catalogus-klaar); soft-wrap, holds, recite; default `--pitch ag-vsa` (a–g
  per systeem + EHM + eindankers) — zie
  [`mxl mvsa`](../reference/cli/mxl.md) / [`mscz mvsa`](../reference/cli/mscz.md).
- Normaalvorm-checklists MXL / MSCZ / PDF: [canonieke checklists](canonical-checklists.md)
  (MXL = vier parts; MSCZ = twee balken SA/TB zonder stem-labels).
  Leesbaarheid partituur: [MSCZ-leesbaarheid](mscz-leesbaarheid.md).

## Bestandsformaten

| Extensie                       | Rol                                 | Spec / profiel                                                                          | CLI (bron = command)                                                                     |
| ------------------------------ | ----------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| [`.vsa`](vsa.md)               | Eenstemmige VSA-bron                | [Specificatie VSA](../specification/README.md)                                          | [`vsa`](../reference/cli/index.md)                                                       |
| [`.mvsa`](mvsa.md)             | Meerstemmige tekstbron (draft)      | [specification-mvsa](../specification-mvsa/README.md)                                   | [`mvsa`](../reference/cli/mvsa.md)                                                       |
| [Score-IR](score-ir.md)        | Scherm-JSON uit `.mvsa` (draft)     | [partituur-ir](../plans/partituur-ir.md)                                                | [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir)                                |
| [vsa-SVG](vsa-svg.md)          | Muziek-only SVG uit `.vsa` (scherm) | Native VSA-renderer; sibling ``.vsa.svg``                                               | [`vsa svg`](../reference/cli/svg.md)                                                     |
| [mvsa-SVG](mvsa-svg.md)        | Muziek-only partituur-SVG (koormap) | MuseScore-brug; layout ``muziek``; Style o.a. ``--compact``                             | [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg) / [`mscz svg`](../reference/cli/mscz.md) |
| [`.mxl` / `.musicxml`](mxl.md) | MusicXML (Coria / bewerking)        | [checklists](canonical-checklists.md) · [MusicXML-export](../guides/musicxml-export.md) | [`mxl`](../reference/cli/mxl.md)                                                         |
| [`.mscz`](mscz.md)             | MuseScore-partituur                 | [checklists](canonical-checklists.md) · templates                                       | [`mscz`](../reference/cli/mscz.md)                                                       |
| [`.mp3` / audio](audio.md)     | Preview-luisteren (afgeleide)       | dunne checklist; MuseScore                                                              | [`vsa audio`](../reference/cli/audio.md)                                                 |
| [`.midi` / `.mid`](midi.md)    | Los MIDI (niet gepland)             | superseded door audio                                                                   | —                                                                                        |

## Commando’s

| Command             | Bron                                      | Man-pagina                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------ |
| `vsa`               | `.vsa` (+ Markdown-workflows)             | [CLI-overzicht](../reference/cli/index.md) |
| `vsa text`          | `.vsa` / `.mvsa` / MusicXML / `.mscz`     | [`text`](../reference/cli/text.md)         |
| `vsa audio`         | `.mxl` / `.vsa` / …                       | [`audio`](../reference/cli/audio.md)       |
| `mvsa`              | `.mvsa`                                   | [`mvsa`](../reference/cli/mvsa.md)         |
| `mxl`               | `.mxl` / `.musicxml`                      | [`mxl`](../reference/cli/mxl.md)           |
| `mscz`              | `.mscz` (`mxl`/`svg`/`pdf`/`normalize`/…) | [`mscz`](../reference/cli/mscz.md)         |

Na `pip install -e .` staan `vsa`, `mvsa`, `mxl` en `mscz` op PATH.

## Bestandsnaamgeving (kort)

Zonder `-o` schrijft de CLI `stem.brontype.doeltype` naast de bron (laatste
segment = echte extensie), bv. `lied.mvsa` → `lied.mvsa.mscz`. In
`generated/` hetzelfde patroon, bv. `alleluia.mvsa.mxl`, `lied.mvsa.mp3`.
Optioneel lyrics-product uit `.mscz` / `.mxl`: `lied.mscz.lyrics.txt` via
[`vsa text`](../reference/cli/text.md) — niet verplicht naast canonieke
`.vsa` / `.mvsa` (daar: [`zoektekst`](zoektekst.md)). Expliciet `-o` mag
een korte naam blijven. Details:
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
