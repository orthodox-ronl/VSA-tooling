# `*.from-ir.musicxml` — MusicXML uit Score-IR (OSMD)

MusicXML geëmit uit [Score-IR](score-ir.md) voor het **schermpad** (OSMD),
niet voor Coria-playback. Start: [contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                                         |
| -------- | -------------------------------------------------------------- |
| Extensie | `.from-ir.musicxml`                                            |
| Rol      | Standaardproduct (meta-key `from-ir`)                          |
| Sibling  | `{bron}.from-ir.musicxml` (bijv. `lied.mvsa.from-ir.musicxml`) |
| Wanneer  | Scherm-OSMD / `--musicxml` bij `{straat} score-ir`             |

## Canoniciteit

Canoniek = bedoelde printvorm uit Score-IR (S8/S13 e.d.), niet M\* Coria.
C1–C4: [contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).
Hubs: [partituur-ir](../plans/partituur-ir.md) ·
[osmd-s8-recite](../plans/osmd-s8-recite.md).

## Inhoud en metadata

| Onderwerp   | Regel          |
| ----------- | -------------- |
| Frontmatter | n.v.t.         |
| Encoding    | UTF-8 MusicXML |

## Syllabificatie

Syllabic / underlay volgt Score-IR (zelfde informatiedichtheid als blad;
R8-achtige underlay waar van toepassing). Soft `-` niet als losse eis in
dit XML-bestand.

## Melisma en binding

| Id  | Regel                                                |
| --  | -----                                                |
| S13 | Compacte same-pitch eindvorm (niet I1-tussenbestand) |
| S8  | Spacers / breve-markers voor recite-print            |

## Transliteratie

n.v.t. tenzij de IR die laag meeneemt (standaardpad: bronlyrics).

## Stemmen en partijen

Zoals in Score-IR (SATB-structuur van de bron).

## Leesbaarheid

Scherm ≠ A4-blad. Emit-markers (spacer `stem/notehead none`, breve): zie
[score-ir](score-ir.md) · [osmd-s8-recite](../plans/osmd-s8-recite.md).

## Herkomst

Merge key `from-ir` in [products-meta](products-meta.md).

## Conversies

| Richting              | CLI                                          |
| --------------------- | -------------------------------------------- |
| Notatiebron → from-ir | `{straat} score-ir … --musicxml`             |
| from-ir → OSMD-SVG    | `mvsa svg --engine osmd` / bibliotheek embed |

## Validatie

Checklist S8/S13 via IR-keten; bibliotheek schermpad-controles.

---

## Recite / print-collapse (type-specifiek)

Zelfde bedoeling als partituur (S8), andere emit dan MuseScore-`.mscz`.
**Geen** M10-playback-explode (dat is Coria-`.mxl`).

## Zie ook

- [score-ir](score-ir.md) · [mvsa-svg](mvsa-svg.md)
- [Formaten & CLI — overzicht](index.md)
