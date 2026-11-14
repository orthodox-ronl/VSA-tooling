# Partituur-SVG uit `.mvsa` of `.mscz` (koormap-brug)

Afgeleide **kale partituur-SVG**, inhoudshoogte na trim. Alleen muziek —
**geen** titel, copyright, colofon. Start: [contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                     |
| -------- | ------------------------------------------ |
| Extensie | `.svg` (sibling `{bron}.svg`)              |
| Rol      | Standaardproduct (meta-key `svg`)          |
| Sibling  | bijv. `lied.mvsa.svg`, `lied.mscz.svg`     |
| Wanneer  | Scherm-fallback + bouwsteen `index.md.pdf` |

Productvorm: **één tall-SVG** (compact Style), geen A4-bladreeks.

## Canoniciteit

Canoniek = layout `muziek` / compact tall; blad-chrome gestript. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).
Layout: [`.mscz` layoutprofielen](mscz.md#layoutprofielen---layout).

## Inhoud en metadata

Geen frontmatter. Default witte achtergrond; `--transparent` leeg.

## Syllabificatie

Underlay volgens MuseScore/OSMD-pad; soft `-` in bron. Schermstrip waar
van toepassing — [syllabificatie](syllabificatie.md). Lyric-bboxes niet
aan elkaar plakken (trailing space / postprocess).

## Melisma en binding

S13 / R7 via partituurketen; OSMD-pad: zelfde bedoeling.

## Transliteratie

n.v.t. op standaard SVG; zie [translit-svg](translit-svg.md).

## Stemmen en partijen

SA/TB zoals partituur-bron.

## Leesbaarheid

Trim `viewBox` op getekende inhoud; lyric-spacing ~0,45 spatium na export.
OSMD: S8 A1-adapter — [osmd-s8-recite](../plans/osmd-s8-recite.md).

## Herkomst

Merge key `svg` in [products-meta](products-meta.md).

## Conversies

| Bron    | CLI                                                               |
| ------- | ----------------------------------------------------------------- |
| `.mvsa` | [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg) (default compact) |
| `.mscz` | [`mscz svg`](../reference/cli/mscz.md)                            |
| OSMD    | `mvsa svg --engine osmd` (Score-IR → from-ir → headless OSMD)     |

## Validatie

Visueel + versheid; S8 bij `--engine osmd`.

---

## Recite / OSMD (type-specifiek)

`--engine osmd`: Score-IR → [from-ir](from-ir.md) →
[`scripts/osmd-svg`](https://github.com/orthodox-ronl/VSA-tooling/tree/main/scripts/osmd-svg)
(S8 spacer-hide + breve-pad). Scherm-hoofdpad site: OSMD-embed
([kale-muziek-svg](../plans/kale-muziek-svg-en-uitgaven.md)).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek.svg
scripts\mscz.cmd svg generated\spike-mscz\1a.mscz -o generated\spike-svg\1a-from-mscz.svg
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-osmd.svg --engine osmd
```

## Zie ook

- [score-ir](score-ir.md) · [`.mscz`](mscz.md) · [vsa-svg](vsa-svg.md)
- [Formaten & CLI — overzicht](index.md)
