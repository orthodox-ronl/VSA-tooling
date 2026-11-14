# `*.translit-*.svg` — transliteratie-SVG

Afgeleide SVG waarin een **tweede schriftlaag** (transliteratie) zichtbaar
is voor scherm/download. Start: [contract-index](contract-index.md).
Plan/diepte: [kerkslavisch-transliteratie](../plans/kerkslavisch-transliteratie.md).

## Identiteit

| Veld     | Waarde                                                               |
| -------- | -------------------------------------------------------------------- |
| Extensie | o.a. `.translit-ksl.svg` / `.translit-nls.svg` (consumer-naamgeving) |
| Rol      | Afgeleid schermproduct (bibliotheek publiceert per leaf)             |
| Sibling  | naast de notatiebron, bijv. `lied.vsa.translit-ksl.svg`              |
| Wanneer  | Tweede schrift zichtbaar moet zijn naast of i.p.v. standaard-SVG     |

## Canoniciteit

Canoniek = zelfde muziek/layout-intentie als het SVG-pad van de bron, plus
zichtbare translit-laag volgens `--translit` / `--translit-modus`
(`nls` / `ksl`). C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

Geen eigen frontmatter. Richting filtert welke passages lyric 2 mogen
krijgen (`nls` = ksl→Latijn; `ksl` = nl→Cyrillisch).

## Syllabificatie

**Zichtbare deling behouden** in de translit-weergave (niet strippen zoals
`.lyrics.txt`). Hub: [syllabificatie](syllabificatie.md).

## Melisma en binding

Volgt het onderliggende partituur-/SVG-pad (S13 e.d.).

## Transliteratie

Dit product **is** de translit-laag. CLI-vlaggen: `--translit`,
`--translit-modus` op o.a. `mvsa mxl` / `mvsa mscz` / SVG-keten — zie
[`mvsa`](../reference/cli/mvsa.md).

## Stemmen en partijen

Zoals bron; optioneel Coria `--translit-as-parts` (hulp-parts, volume 0)
op `.mxl` — niet per se in deze SVG.

## Leesbaarheid

Zelfde stacking/font-eisen als [vsa-svg](vsa-svg.md) / [mvsa-svg](mvsa-svg.md);
tweede lyric-regel mag de eerste niet onleesbaar bedekken (consumer/layout).

## Herkomst

Bibliotheek/products-pad; niet altijd universele meta-key — documenteer in
consumer als je runt. Tooling-merge waar de CLI dat schrijft.

## Conversies

Bron `.vsa`/`.mvsa` (+ translit-vlaggen) → SVG/MSCZ/MXL met lyric 2.
Zie man-pagina `mvsa` en bibliotheek `scripts\products.cmd`.

## Validatie

Visueel + consumer-checks; bron moet canonieke lyrics hebben (C3).

## Zie ook

- [vsa-svg](vsa-svg.md) · [mvsa-svg](mvsa-svg.md)
- [Formaten & CLI — overzicht](index.md)
