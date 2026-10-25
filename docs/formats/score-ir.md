# Score-IR (`.score-ir.json`) — schermtussenmodel (draft)

Contracten (S8/S13 e.d.): [contract-index](contract-index.md).

JSON-tussenmodel tussen `.mvsa` en schermweergave (koormap / shortcode
`muziek`, later CoriB). Geen MuseScore-bestand; geen A4/colofon.

**Productieschermpad:** Score-IR → MusicXML (uit IR) → OSMD. Print/blad blijft
MuseScore. Brugcontract: [partituur-ir §7](../plans/partituur-ir.md).
Bedoelde printvorm = checklists; OSMD-emit: [osmd-s8-recite](../plans/osmd-s8-recite.md).

**Sibling-artifacts** (naast `lied.mvsa`, zelfde naamgeving als andere
`mvsa`-exports):

| Artifact                         | Defaultnaam                   |
| -------------------------------- | ----------------------------- |
| Score-IR JSON                    | `lied.mvsa.score-ir.json`     |
| MusicXML uit IR (OSMD)           | `lied.mvsa.from-ir.musicxml`  |

Schrijf beide met ``mvsa score-ir … --musicxml`` (zonder pad; werkt ook
op een map).

**Print-eindvorm (S8/S13):** Score-IR bewaart recite-spacers
(`print.spacer` / `print.breveHead`) en compacte same-pitch melisma’s;
from-ir MusicXML tekent die voor OSMD (zelfde informatiedichtheid als
blad-SVG, geen MuseScore-paginamodel). Details:
[partituur-ir §4.4](../plans/partituur-ir.md).

| Onderwerp                         | Waar                                                                 |
| --------------------------------- | -------------------------------------------------------------------- |
| Contract (velden, partituur)      | [partituur-ir](../plans/partituur-ir.md)                             |
| Scherm- / CoriB-brug              | [partituur-ir §7](../plans/partituur-ir.md)                          |
| CLI                               | [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir)            |
| Score-IR → MusicXML (OSMD)        | `vsa.score_ir_musicxml` · CLI ``--musicxml``                         |
| Browser-spike                     | `examples/spikes/partituur-browser/`                                 |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa --musicxml
mvsa score-ir examples\mvsa --musicxml
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a.score-ir.json --musicxml generated\score-ir\1a.from-ir.musicxml
```
