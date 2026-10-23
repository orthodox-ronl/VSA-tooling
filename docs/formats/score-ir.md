# Score-IR (`.score-ir.json`) — schermtussenmodel (draft)

JSON-tussenmodel tussen `.mvsa` en schermweergave (koormap / shortcode
`muziek`, later CoriB). Geen MuseScore-bestand; geen A4/colofon.

**Productieschermpad:** Score-IR → MusicXML (uit IR) → OSMD. Print/blad blijft
MuseScore. Brugcontract: [partituur-ir §7](../plans/partituur-ir.md).

**Sibling-artifacts** (naast `lied.mvsa`, zelfde naamgeving als andere
`mvsa`-exports):

| Artifact                         | Defaultnaam                   |
| -------------------------------- | ----------------------------- |
| Score-IR JSON                    | `lied.mvsa.score-ir.json`     |
| MusicXML uit IR (OSMD)           | `lied.mvsa.from-ir.musicxml`  |

Schrijf beide met ``mvsa score-ir … --musicxml`` (zonder pad; werkt ook
op een map).

| Onderwerp                         | Waar                                                                 |
| --------------------------------- | -------------------------------------------------------------------- |
| Contract (velden, partituur)      | [partituur-ir](../plans/partituur-ir.md)                             |
| Scherm- / CoriB-brug              | [partituur-ir §7](../plans/partituur-ir.md)                          |
| CLI                               | [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir)    |
| Score-IR → MusicXML (OSMD)        | `vsa.score_ir_musicxml` · CLI ``--musicxml``                         |
| Browser-spike                     | `examples/spikes/partituur-browser/`                                 |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa --musicxml
mvsa score-ir examples\mvsa --musicxml
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a.score-ir.json --musicxml generated\score-ir\1a.from-ir.musicxml
```
