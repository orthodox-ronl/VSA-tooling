# Muziek-only SVG uit `.vsa` (scherm)

Afgeleide **SVG** met alleen de VSA-notatie (geen titel/colofon). Bedoeld
voor schermweergave. Zelfde productrol als [mvsa-SVG](mvsa-svg.md); andere
pipeline (native VSA-renderer). Start: [contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                           |
| -------- | ------------------------------------------------ |
| Extensie | `.svg` (sibling `.vsa.svg`)                      |
| Rol      | Standaardproduct (meta-key `svg` bij vsa-straat) |
| Sibling  | `lied.vsa` → `lied.vsa.svg`                      |
| Wanneer  | Catalogus-/koormap-scherm zonder MuseScore       |

## Canoniciteit

Canoniek = muziek-only, trim/viewBox op inhoud; geen blad-chrome. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

Geen frontmatter in de SVG. Titel/colofon horen in `index.md.pdf`, niet hier.

## Syllabificatie

**Strip** soft `-` in zichtbare underlay (schermtekst doorlopend), tenzij
translit-product — zie [syllabificatie](syllabificatie.md) ·
[translit-svg](translit-svg.md).

## Melisma en binding

Volgt VSA-renderregels / K2; hyphen ≠ melisma.

## Transliteratie

n.v.t. op standaard `.vsa.svg`. Tweede schrift: [translit-svg](translit-svg.md).

## Stemmen en partijen

n.v.t. (eenstemmig).

## Leesbaarheid

Alleen notatie; geen overlapping met titelblokken (die ontbreken bewust).

## Herkomst

Merge key `svg` in [products-meta](products-meta.md).

## Conversies

| Bron   | CLI                                  |
| ------ | ------------------------------------ |
| `.vsa` | [`vsa svg`](../reference/cli/svg.md) |

## Validatie

Visueel + products-versheid.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa -o generated\vsa\phrase.vsa.svg
```

## Zie ook

- [mvsa-svg](mvsa-svg.md) · [translit-svg](translit-svg.md)
- [Formaten & CLI — overzicht](index.md)
