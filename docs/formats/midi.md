# `.mid` / `.midi` — los MIDI-bestand (niet gepland)

Rol historisch: een **[variant](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)**
van een [zangstuk](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
als **los MIDI-bestand**. Voor **preview-luisteren** op de bibliotheek-site
gebruik je [audio (``.mp3``)](audio.md) — dat is geïmplementeerd.

## Status

**Niet gepland.** De use case “even horen hoe het stuk klinkt” is afgedekt door
`vsa audio` / `mvsa audio`. Een aparte `.mid`-CLI staat niet meer op de
mvsa-backlog ([open-points — Klaar](../specification-mvsa/open-points.md)).

| Onderwerp                 | Stand                                                        |
| ------------------------- | ------------------------------------------------------------ |
| Rol in de conversiematrix | Niet gepland (audio dekt preview)                            |
| Canonieke checklist       | —                                                            |
| CLI-command               | Geen — gebruik [`vsa audio`](../reference/cli/audio.md)      |

MIDI in MusicXML-`part-list` (instrument/channel) bij `.mxl`-export blijft
iets anders: metadata in MusicXML, geen los `.mid`-bestand. Zie
[rendering — playback](../specification/rendering.md#profiel-playback).

## Als er later toch een use case komt

Dan opnieuw openen via [open-points](../specification-mvsa/open-points.md) met
een concreet doel (bijv. download voor DAW). Voorlopige checklist uit de oude
richting:

| #   | Eis                           | Toelichting                                                                  |
| --- | ----------------------------- | ---------------------------------------------------------------------------- |
| D1  | Speelbaar                     | Bestand opent/afspeelt in gangbare spelers.                                  |
| D2  | Pitch/duur-equivalent         | Zelfde klinkende noten als de gekozen bron-representatie (binnen afronding). |
| D3  | Meerstemmig waar bron SATB is | Stemmen hoorbaar gescheiden of gemengd.                                      |
| D4  | Geen partituur-eis            | Lyrics/layout/streepjes geen vereiste voor MIDI.                             |

## Zie ook

- [`.mp3` / audio](audio.md) (preview-luisteren — werkend)
- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) (playback via MusicXML)
- [mvsa-conversies](../plans/mvsa-conversions.md)
