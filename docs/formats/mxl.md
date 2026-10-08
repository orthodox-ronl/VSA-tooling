# `.mxl` / `.musicxml` — MusicXML

Compressed MusicXML (`.mxl`) of platte XML (`.musicxml`). Gebruikt voor
**Coria-playback** (`playback`-profiel) en partituurbewerking
(`engraving`).

## Wat hoort hier

| Onderwerp                | Waar                                                                                                              |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Export vanuit `.vsa`     | [`vsa musicxml`](../reference/cli/musicxml.md), [MusicXML-export](../guides/musicxml-export.md)                   |
| Export vanuit `.mvsa`    | [`mvsa musicxml`](../reference/cli/mvsa.md#vsa-mvsa-musicxml)                                                     |
| Import → `.mvsa`         | [`mxl import`](../reference/cli/mxl.md) (= [`mvsa import`](../reference/cli/mvsa.md#vsa-mvsa-import); SATB P1–P4) |
| → `.mscz`                | [`mxl mscz`](../reference/cli/mxl.md)                                                                             |
| Platte gezongen tekst    | [`vsa text`](../reference/cli/text.md) (ook op `{stam}.mscz.mxl`)                                                 |
| Normatieve renderdetails | [Rendering — MusicXML](../specification/rendering.md#musicxml-export)                                             |

!!! warning "Import = werkbank"
    `mxl import` is een **bewerkvorm** voor de werkbank (woordstreepjes, lege
    recite, lossy). Zie
    [`mvsa import`](../reference/cli/mvsa.md#vsa-mvsa-import).

**Import:** de MusicXML-bron wordt direct geparst als vier parts (P1–P4 =
S/A/T/B). Soft-wrap ~80 tekens, same-pitch holds als `-`, multi-lettergreep
lyrics als recite. Kies `--pitch doremi`, `a-g` (alias `abc`), of `vsa`
(EHM + absolute eindankers op systeemeinden).

Dit is **geen** herdefinitie van de MusicXML-standaard: we documenteren
**onze** export-/importprofielen.

**Normaalvorm (checklist):**
[canonieke checklists — MXL](canonical-checklists.md#checklist-mxl-coria-playback)
(Coria / `playback`) — **vier aparte parts** S/A/T/B met lyrics per part;
**piano-MIDI** op elke part (`keyboard.piano.grand`, M8);
**geen** print-recite-collapse (M10). Same-pitch **melisma** samentrekken
(M5a): één lettergreep op dezelfde toon → **één** noot (gestipte ELM’s zoals
`_.` blijven intact; Coria stript ties). Semantiek deelt de kern met MSCZ;
layout divergeert (partituur-MusicXML = I1 tie-keten zonder gestipte
collapse-sommen; **MSCZ-postprocess** maakt daarna compacte gestipte noten).
Oefenhoek-Coria-transforms: `VSA-demo/scripts/mscz-product-transforms.md`.

## Typische commando’s

```cmd
mxl import generated\alleluia.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl import generated\alleluia.mxl --pitch vsa -o generated\from-mxl.vsa.mvsa
mvsa validate generated\from-mxl.vsa.mvsa
mxl mscz generated\alleluia.mxl -o generated\from-mxl.mscz
vsa text generated\alleluia.mxl -o generated\alleluia.lyrics.txt
```

Via repo-script: `scripts\mxl.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mvsa`](mvsa.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
- Platte tekst: [`vsa text`](../reference/cli/text.md)
