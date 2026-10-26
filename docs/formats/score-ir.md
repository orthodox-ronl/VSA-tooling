# Score-IR (`.score-ir.json`) — schermtussenmodel (draft)

Contracten (S8/S13 e.d.): [contract-index](contract-index.md).

JSON-tussenmodel voor schermweergave (koormap / shortcode `muziek`,
later CoriB). Geen MuseScore-bestand; geen A4/colofon. Het productcontract
geldt voor **elke** notatiebron (`.vsa` / `.mvsa` / `.mscz`); de
bronstraat bepaalt alleen de CLI (`vsa score-ir` / `mvsa score-ir` /
`mscz score-ir`). Zie
[contract-index — universele productcatalogus](contract-index.md#universele-productcatalogus).

**Productieschermpad:** Score-IR → MusicXML (uit IR) → OSMD. Print/blad blijft
MuseScore. Brugcontract: [partituur-ir §7](../plans/partituur-ir.md).
Bedoelde printvorm = checklists; OSMD-emit: [osmd-s8-recite](../plans/osmd-s8-recite.md).

**Sibling-artifacts** (naamgeving `{bron}.score-ir.json` /
`{bron}.from-ir.musicxml`):

| Artifact                         | Voorbeeld                     |
| -------------------------------- | ----------------------------- |
| Score-IR JSON                    | `lied.mvsa.score-ir.json`     |
| MusicXML uit IR (OSMD)           | `lied.mscz.from-ir.musicxml`  |

Schrijf beide met ``{straat} score-ir … --musicxml`` (zonder pad; werkt
ook op een map). Alleen de eigen bronextensie per straat.

**Print-eindvorm (S8/S13):** Score-IR bewaart recite-spacers
(`print.spacer` / `print.breveHead`) en compacte same-pitch melisma’s;
from-ir MusicXML emitteert die voor het schermpad (zelfde informatiedichtheid
als blad-SVG, geen MuseScore-paginamodel). Details:
[partituur-ir §4.4](../plans/partituur-ir.md).

**S8 / OSMD (contract A1):** `print.spacer` → from-ir
`<stem>none</stem>` + `<notehead>none</notehead>` (lyrics blijven op de
noot). Dat is een **stabiele marker** voor de scherm-OSMD-adapter, geen
belofte dat OSMD/VexFlow de kop zelf verbergt (peiling:
[osmd-s8-recite](../plans/osmd-s8-recite.md)). Breve-midden:
`notehead breve` + `stem none` (geen `type=breve`).

| Onderwerp                         | Waar                                                                                 |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| Contract (velden, partituur)      | [partituur-ir](../plans/partituur-ir.md)                                             |
| Scherm- / CoriB-brug              | [partituur-ir §7](../plans/partituur-ir.md)                                          |
| CLI                               | `{straat} score-ir` — o.a. [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir) |
| Score-IR → MusicXML (OSMD)        | `vsa.score_ir_musicxml` · CLI ``--musicxml``                                         |
| Browser-spike                     | `examples/spikes/partituur-browser/`                                                 |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa --musicxml
mvsa score-ir examples\mvsa --musicxml
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a.score-ir.json --musicxml generated\score-ir\1a.from-ir.musicxml
```
