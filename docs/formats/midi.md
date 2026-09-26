# `.mid` / `.midi` — afspelen

Rol: een **[variant](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)**
van een [zangstuk](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
**afspelen** (klank / oefenen), niet partituurlayout.

## Status

| Onderwerp | Stand |
| --------- | ----- |
| Rol in de conversiematrix | Gepland / open |
| Canonieke checklist | Nog dun — zie hieronder |
| CLI-command | **Open** (geen `midi`-entrypoint vastgelegd) |

MIDI in MusicXML-`part-list` (instrument/channel) bij `.mxl`-export is iets
anders: dat is metadata in MusicXML, geen los `.mid`-bestand. Zie
[rendering — playback](../specification/rendering.md#profiel-playback).

## Voorlopige checklist (richting)

| # | Eis | Toelichting |
| - | --- | ----------- |
| D1 | Speelbaar | Bestand opent/afspeelt in gangbare spelers. |
| D2 | Pitch/duur-equivalent | Zelfde klinkende noten als de gekozen bron-representatie (binnen afronding). |
| D3 | Meerstemmig waar bron SATB is | Stemmen hoorbaar gescheiden of gemengd — keuze nog open. |
| D4 | Geen partituur-eis | Lyrics/layout/streepjes geen vereiste voor MIDI. |

## Conversies (open)

Mogelijke richtingen (CLI-namen nog niet gekozen):

- `.vsa` / `.mvsa` / `.mxl` / `.mscz` → `.mid` of `.midi`
- (optioneel later) reverse — buiten scope tot er een use case is

## Bestandsnaamgeving

Zelfde conventie als elders: in `generated/` bij voorkeur
`stem.brontype.midi` (of `.mid`); CLI-default mag simpel blijven. Zie
[canonieke checklists — naamgeving](canonical-checklists.md#bestandsnaamgeving-conventie).

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) (Coria-playback via MusicXML)
- [mvsa-conversies](../plans/mvsa-conversions.md)
