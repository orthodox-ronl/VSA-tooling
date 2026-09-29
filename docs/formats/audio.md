# `.mp3` / `.ogg` / `.wav` — preview-luisteren

Rol: een **[variant](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)**
van een [zangstuk](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
**even beluisteren** (idee van de klank), niet partituurlayout en niet
oefenen-met-stemkeuze (dat blijft Coria).

Het bestand is een **afgeleide**: gegenereerd uit playback-``.mxl`` (of
``.vsa`` / ``.mvsa`` / fallback ``.mscz``) via MuseScore. De toolchain schrijft
alleen het artefact; de **consumer-site** (bijv. bibliotheek) zet de
afspeelknop.

## Status

| Onderwerp                 | Stand                                      |
| ------------------------- | ------------------------------------------ |
| Rol in de conversiematrix | Werkend                                    |
| Canonieke checklist       | Dun — zie hieronder                        |
| CLI-command               | `vsa audio` / `mvsa audio`                 |

## Checklist (richting)

| #   | Eis                           | Toelichting                                                                  |
| --- | ----------------------------- | ---------------------------------------------------------------------------- |
| A1  | Speelbaar                     | Bestand opent/afspeelt in gangbare spelers / HTML5 ``<audio>``.              |
| A2  | Pitch/duur-equivalent         | Zelfde klinkende noten als playback-``.mxl`` (binnen MuseScore-afronding).   |
| A3  | Geen stemkeuze                | Alle parts gemengd (MuseScore-default); geen wizard.                         |
| A4  | Geen partituur-eis            | Lyrics/layout/streepjes geen vereiste voor het audiobestand.                 |

## Conversies

| Bron                         | Commando                                      |
| ---------------------------- | --------------------------------------------- |
| ``.mxl`` / ``.musicxml``     | `vsa audio` / `mvsa audio`                    |
| ``.vsa``                     | `vsa audio` (via playback MusicXML)           |
| ``.mvsa``                    | `mvsa audio` (via playback MusicXML)          |
| ``.mscz``                    | `vsa audio` / `mvsa audio` (fallback via mxl) |

Default-formaat: **``.mp3``**. Optioneel ``--format ogg`` of ``wav``, of
``[audio] format`` in ``vsa.toml``.

Klank en tempo komen uit de score (MIDI in playback-MXL + tempo). Canonieke
playback-MXL gebruikt **piano** op elke partij (checklist M8). Bitrate en
extra instrumentkeuze buiten die piano zijn in v1 MuseScore-defaults.

## Bestandsnaamgeving

In ``generated/`` bij voorkeur ``stem.brontype.mp3`` (of ``.ogg`` / ``.wav``).
CLI-default mag simpel blijven. Zie
[canonieke checklists — naamgeving](canonical-checklists.md#bestandsnaamgeving-conventie).

## Ownership

| Laag        | Verantwoordelijkheid                                      |
| ----------- | --------------------------------------------------------- |
| VSA-tooling | Artefact genereren (`vsa audio` / `mvsa audio`)           |
| Consumer    | Afspeelknop / ``:::include mp3-player`` (gepland)         |
| bron        | Exportcontract ``mp3-player`` (nog afronden)              |

## Zie ook

- [CLI — `vsa audio`](../reference/cli/audio.md)
- [`.mxl`](mxl.md) (playback-bron)
- [`.midi`](midi.md) (los MIDI — **niet gepland**; preview = audio)
- [Formaten & CLI — overzicht](index.md)
