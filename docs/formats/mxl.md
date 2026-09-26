# `.mxl` / `.musicxml` — MusicXML

Compressed MusicXML (`.mxl`) of platte XML (`.musicxml`). Gebruikt voor
**Coria-playback** (`playback`-profiel) en partituurbewerking
(`engraving`).

## Wat hoort hier

| Onderwerp | Waar |
| --------- | ---- |
| Export vanuit `.vsa` | [`vsa musicxml`](../reference/cli/musicxml.md), [MusicXML-export](../guides/musicxml-export.md) |
| Export vanuit `.mvsa` | [`mvsa musicxml`](../reference/cli/mvsa.md#vsa-mvsa-musicxml) |
| Import → `.mvsa` | [`mxl import`](../reference/cli/mxl.md) |
| → `.mscz` | [`mxl mscz`](../reference/cli/mxl.md) |
| Normatieve renderdetails | [Rendering — MusicXML](../specification/rendering.md#musicxml-export) |

Dit is **geen** herdefinitie van de MusicXML-standaard: we documenteren
**onze** export-/importprofielen.

## Typische commando’s

```cmd
mxl import generated\alleluia.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl mscz generated\alleluia.mxl -o generated\from-mxl.mscz
```

Via repo-script: `scripts\mxl.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mvsa`](mvsa.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
