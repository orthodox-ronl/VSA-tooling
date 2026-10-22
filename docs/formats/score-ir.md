# Score-IR (`.score-ir.json`) — schermtussenmodel (draft)

JSON-tussenmodel tussen `.mvsa` en schermweergave (koormap-SVG, CoriB).
Geen MuseScore-bestand; geen A4/colofon.

| Onderwerp                         | Waar                                                                 |
| --------------------------------- | -------------------------------------------------------------------- |
| Contract (velden, partituur)      | [partituur-ir](../plans/partituur-ir.md)                             |
| CLI                               | [`vsa mvsa score-ir`](../reference/cli/mvsa.md#vsa-mvsa-score-ir)    |
| Score-IR → MusicXML (OSMD)        | `vsa.score_ir_musicxml` · CLI ``--musicxml``                         |
| Browser-spike                     | `examples/spikes/partituur-browser/`                                 |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a-vredeslitanie.score-ir.json
vsa mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a.score-ir.json --musicxml generated\score-ir\1a.from-ir.musicxml
```
