# `.mxl` / `.musicxml` — MusicXML

Compressed MusicXML (`.mxl`) of platte XML (`.musicxml`). Gebruikt voor
**Coria-playback** (`playback`) en partituurbewerking (`engraving`). Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                                 |
| -------- | ------------------------------------------------------ |
| Extensie | `.mxl` / `.musicxml` / `.xml`                          |
| Rol      | Standaardproduct (meta-key `mxl`) of bewerkingsbestand |
| Sibling  | `{stam}.{bron}.mxl` (bijv. `lied.mvsa.mxl`)            |
| Wanneer  | Coria-oefenen / MusicXML-brug                          |

Dit is **geen** herdefinitie van de MusicXML-standaard: we documenteren
**onze** export-/importprofielen.

## Canoniciteit

Canoniek (Coria/playback) = checklist **M\*** —
[canonical-checklists §MXL](canonical-checklists.md#checklist-mxl-coria-playback):
vier parts S/A/T/B; piano-MIDI per part (M8); enz. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp                       | Regel                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Frontmatter                     | n.v.t. (XML)                                                                                                |
| Encoding                        | UTF-8 XML                                                                                                   |
| Uitvoeraanwijzingen uit `.mvsa` | [uitvoeraanwijzingen](../specification-mvsa/uitvoeraanwijzingen.md) (cesuur, dynamiek, cresc/dim, tempo, …) |

## Syllabificatie

Zing-deling komt uit de canonieke bron. Export default **zonder** stille
syllabify; `--syllabify` = expliciete uitzondering (C3). Op playback:
syllabic begin/middle/end waar van toepassing. Hub:
[syllabificatie](syllabificatie.md).

## Melisma en binding

| Id     | Regel                                                                               |
| --     | -----                                                                               |
| M5a    | Same-pitch melisma samentrekken (één lettergreep → één noot; gestipte ELM’s intact) |
| Hyphen | ≠ melisma (L3)                                                                      |

## Transliteratie

n.v.t. als tweede lyric-laag in standaard playback-`.mxl`.

## Stemmen en partijen

**Vier aparte parts** S/A/T/B met lyrics per part (M2) — anders dan
partituur-`.mscz` (twee balken).

## Leesbaarheid

Playback-layout ≠ blad. Geen partituur-R\* op Coria-`.mxl`. Renderdetails:
[Rendering — MusicXML](../specification/rendering.md#musicxml-export).

## Herkomst

Product: merge key `mxl` in [products-meta](products-meta.md).

## Conversies

| Richting                        | CLI                                 | Opmerking             |
| ------------------------------- | ----------------------------------- | --------------------- |
| `.vsa`/`.mvsa`/`.mscz` → `.mxl` | `vsa mxl` / `mvsa mxl` / `mscz mxl` | C3/C4                 |
| `.mxl` → `.mvsa`                | `mxl mvsa`                          | Werkbank-uitzondering |
| `.mxl` → `.mscz`                | `mxl mscz`                          |                       |
| Normalize                       | `mxl normalize`                     | Naar M\*              |

## Validatie

[`mxl validate`](../reference/cli/mxl.md) — M2/M8 e.d. Zelfde
checklist als **C4** na `vsa`/`mvsa`/`mscz mxl` en `products` (profiel
`mono` voor `.vsa`, `satb` anders); zie
[contract-index §C4](contract-index.md#canoniciteit-en-conversiegates-c).

---

## Recite en print-collapse (type-specifiek)

| Id  | Regel                                                                          |
| --  | -----                                                                          |
| M10 | **Geen** print-recite-collapse / breve: elke lettergreep een klinkende noot    |
| S8  | Print-collapse hoort bij partituur (`.mscz` / Score-IR), niet bij Coria-`.mxl` |

Oefenhoek-Coria-transforms: `VSA-demo/scripts/mscz-product-transforms.md`.

## Typische commando’s

```cmd
mxl mvsa generated\alleluia.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl mscz generated\alleluia.mxl -o generated\from-mxl.mscz
```

Via repo-script: `scripts\mxl.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mvsa`](mvsa.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
