# `.mp3` / `.ogg` / `.wav` — preview-luisteren

Rol: een variant van een zangstuk **even beluisteren** (idee van de klank),
niet partituurlayout en niet oefenen-met-stemkeuze (dat blijft Coria). Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                                |
| -------- | ----------------------------------------------------- |
| Extensie | `.mp3` (default) / `.ogg` / `.wav`                    |
| Rol      | Standaardproduct (meta-key `mp3`; ogg/wav vooral los) |
| Sibling  | `{stam}.{bron}.mp3` (bijv. `lied.mscz.mp3`)           |
| Wanneer  | Preview op de consumer-site                           |

Afgeleide via MuseScore uit playback-``.mxl`` (of notatiebron / fallback
``.mscz``). De toolchain schrijft het artefact; de consumer zet de
afspeelknop.

## Canoniciteit

Canoniek = checklist A1–A5 hieronder. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp     | Regel                                                  |
| ------------- | ------------------------------------------------------ |
| Frontmatter   | n.v.t.                                                 |
| Encoding      | Container (mp3/ogg/wav); geen tekstinhoud              |
| Tempo / klank | Uit score (MIDI in playback-MXL + `@tempo` in `.mvsa`) |

## Syllabificatie

n.v.t. — geen lyrics in het audiobestand. Bron moet wel canonieke
zing-deling hebben vóór export (C3); geen soft `-` “in” audio.

## Melisma en binding

n.v.t. op het audiobestand. Klinkende noten volgen playback-MXL (M5a e.d.).

## Transliteratie

n.v.t.

## Stemmen en partijen

Alle parts gemengd (MuseScore-default); geen stemkeuze-wizard (A3).

## Leesbaarheid

n.v.t. (geen blad).

## Herkomst

Merge key `mp3` in [products-meta](products-meta.md).

## Conversies

| Bron    | Commando                                               |
| ------- | ------------------------------------------------------ |
| `.vsa`  | `vsa audio` (deling in de bron; geen stille syllabify) |
| `.mvsa` | `mvsa mp3` / `ogg` / `wav`                             |
| `.mscz` | `mscz mp3` / `ogg` / `wav`                             |
| `.mxl`  | via notatiestraat; geen cross-street audio             |

## Validatie

A1–A5 (hand/CI speelbaarheid + trim). ffmpeg op PATH voor A5.

---

## Checklist audio (type-specifiek)

| #   | Eis                   | Toelichting                                |
| --  | ---                   | -----------                                |
| A1  | Speelbaar             | Gangbare spelers / HTML5 `<audio>`         |
| A2  | Pitch/duur-equivalent | Zelfde klinkende noten als playback-`.mxl` |
| A3  | Geen stemkeuze        | Alle parts gemengd                         |
| A4  | Geen partituur-eis    | Lyrics/layout geen vereiste                |
| A5  | Geen sleepstilte      | ≤ ~10 ms stilte na laatste sample (ffmpeg) |

Preview-bitrate: mp3 LAME `-q:a 5`; ogg Vorbis `-q:a 4`. Canonieke
playback-MXL: piano per partij (M8).

## Ownership (type-specifiek)

| Laag        | Verantwoordelijkheid                               |
| ----------- | -------------------------------------------------- |
| VSA-tooling | Artefact genereren                                 |
| Consumer    | Afspeelknop                                        |
| bron        | Exportcontract `mp3-player` (org; afronden elders) |

## Zie ook

- [CLI — `vsa audio`](../reference/cli/audio.md)
- [`.mxl`](mxl.md) · [`.midi`](midi.md) (los MIDI — niet gepland)
- [Formaten & CLI — overzicht](index.md)
