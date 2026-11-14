# Score-IR (`.score-ir.json`) — schermtussenmodel (draft)

JSON-tussenmodel voor schermweergave (koormap / shortcode `muziek`, later
CoriB). Geen MuseScore-bestand; geen A4/colofon. Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                                   |
| -------- | -------------------------------------------------------- |
| Extensie | `.score-ir.json`                                         |
| Rol      | Standaardproduct (meta-key `score-ir`)                   |
| Sibling  | `{bron}.score-ir.json` (bijv. `lied.mvsa.score-ir.json`) |
| Wanneer  | Schermpad vóór OSMD; product uit elke notatiebron        |

Bijbehorend emit-product: [from-ir](from-ir.md)
(`{bron}.from-ir.musicxml`).

## Canoniciteit

Canoniek = velden/printvorm volgens [partituur-ir](../plans/partituur-ir.md)
(S8/S13 e.d.). C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp    | Regel                                      |
| ------------ | ------------------------------------------ |
| Frontmatter  | n.v.t. (JSON-schema in partituur-ir)       |
| Encoding     | UTF-8 JSON                                 |
| `lyricIndex` | Per stem volgorde van lyric-dragende noten |

## Syllabificatie

Underlay/syllabic-intentie in IR; zichtbare soft `-` niet als bronnorm in
JSON. Bron (C3) moet canonieke zing-deling hebben.

## Melisma en binding

| Id  | Regel                                               |
| --  | -----                                               |
| S13 | Compacte same-pitch melisma’s (o.a. gestipte ELM)   |
| S8  | Recite-spacers (`print.spacer` / `print.breveHead`) |

## Transliteratie

n.v.t. tenzij IR die laag modelleert (standaard: bronlyrics).

## Stemmen en partijen

Structuur van de notatiebron (SATB e.d.).

## Leesbaarheid

Bedoelde printvorm = checklists; scherm-emit:
[osmd-s8-recite](../plans/osmd-s8-recite.md). Geen MuseScore-paginamodel.

## Herkomst

Merge key `score-ir` (+ vaak `from-ir`) in [products-meta](products-meta.md).

## Conversies

| Richting                          | CLI                         |
| --------------------------------- | --------------------------- |
| `.vsa`/`.mvsa`/`.mscz` → Score-IR | `{straat} score-ir`         |
| Score-IR → from-ir MusicXML       | zelfde CLI met `--musicxml` |
| → OSMD-SVG                        | `mvsa svg --engine osmd`    |

## Validatie

Velden/regressies via partituur-ir + exporttests.

**C4 (fase 3):** na schrijven van Score-IR controleert
`require_canonical_score_ir_target` dat de JSON leesbaar is, `format` /
`profile` kloppen, `measures` een lijst is, en from-ir-emit
(`score_ir_to_musicxml`) slaagt. Aangesloten op `{straat} score-ir` /
`products` (key `score-ir`). Uitzondering: `--allow-noncanonical`.
Nog geen aparte S8/S13-checklistgate op het JSON-bestand.

---

## Recite / print-collapse (type-specifiek)

| Id  | Regel                                                |
| --  | -----                                                |
| S8  | Spacers/breve in IR; from-ir emit markers voor OSMD  |
| M10 | n.v.t. — geen Coria-playback-collapse in dit product |

**S8 / OSMD (contract A1):** `print.spacer` → from-ir
`<stem>none</stem>` + `<notehead>none</notehead>`. Adapter:
[`scripts/osmd-svg`](https://github.com/orthodox-ronl/VSA-tooling/tree/main/scripts/osmd-svg).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa --musicxml
mvsa score-ir examples\mvsa --musicxml
```

## Zie ook

- [from-ir](from-ir.md) · [mvsa-svg](mvsa-svg.md)
- [partituur-ir](../plans/partituur-ir.md)
- [Formaten & CLI — overzicht](index.md)
