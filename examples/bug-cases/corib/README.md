# CoriB / OSMD producttoets — recite (S8)

Corpus voor **visuele product-tegen-product**-toets van Score-IR → from-ir →
OSMD tegen MuseScore-bladproducten. Geen peiling op bbox-oppervlaktes als
acceptatie; die mag alleen helpen bij bouwen.

Contract: checklist **S8** ([canonical-checklists](../../../docs/formats/canonical-checklists.md)),
brug [partituur-ir §7](../../../docs/plans/partituur-ir.md), plan
[osmd-s8-recite](../../../docs/plans/osmd-s8-recite.md), CoriB
[corib-mvp](../../../docs/plans/corib-mvp.md).

## Corpus

| Bron (`.mvsa`)                         | MuseScore-ref (sibling)     | Waarom                                      |
| -------------------------------------- | --------------------------- | ------------------------------------------- |
| `alleluia-toon-8.mvsa`                 | `.mvsa.svg` + `.mvsa.pdf`   | Canonieke lange `()`-recite                 |
| `alleluia-toon-3.mvsa`                 | idem                        | Korte recite + zelfde-toon-vervolg → S8     |
| `alleluia-toon-2.mvsa`                 | idem                        | Extra lange `()`-recite                     |
| `derde-antifoon-zondag-hemelum.mvsa`   | idem                        | Langere praktijkcasus (veel recite)         |

Referentie-SVG/PDF: door de beheerder gegenereerd met `mvsa svg` / `mvsa pdf`
(MuseScore). OSMD-product: `mvsa svg --engine osmd`.

## Producten genereren (OSMD)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-8.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\alleluia-toon-3.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-3.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\alleluia-toon-2.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-2.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\derde-antifoon-zondag-hemelum.mvsa -o generated\corib-s8-toets\osmd\derde-antifoon-zondag-hemelum.osmd.svg --engine osmd
```

Toets: open MuseScore-sibling `.mvsa.svg` (of `.pdf`) naast het OSMD-`.svg`.
Eindbeeld S8: Al = gewone noot → le = stokloze `||O||` (breve) →
middenlettergrepen = **alleen tekst** (geen koppen) → cadens.

Vergelijkings-PNG’s (raster van ref + OSMD, cloud-run 2026-10-31):
`toets-png/*.ref.png` vs `toets-png/*.osmd.png`.

## Uitslag (producttoets)

| Stuk              | MuseScore-ref (S8)                     | OSMD-product (`mvsa svg --engine osmd`)                                      | Oordeel    |
| ----------------- | -------------------------------------- | ---------------------------------------------------------------------------- | ---------- |
| alleluia-toon-8   | breve `\|\|O\|\|` + tekst-only middens | spacer-koppen verborgen (A1); lyrics compleet; breve stokloos                | **PASS**\* |
| alleluia-toon-3   | idem                                   | idem                                                                         | **PASS**\* |
| alleluia-toon-2   | idem                                   | idem                                                                         | **PASS**\* |
| derde-antifoon    | ref aanwezig                           | zelfde A1-pad; handmatig steekproef spacers                                  | **PASS**†  |

\*Pixel-pariteit MuseScore↔OSMD is geen eis. OSMD tekent de breve niet als
MuseScore-`\|\|O\|\|`-glyph; wél: geen zichtbare spacer-koppen, lyrics op
die posities, stokloze breve-markering (`data-osmd-breve`).
†Machinecheck: `node scripts/osmd-svg/check-s8-a1.mjs <from-ir.musicxml>`.

### Fix (2026-10-31)

`scripts/osmd-svg/render.mjs` draait na OSMD-render de A1-adapter
(`s8-a1-adapter.js`) — zelfde marker-contract als bibliotheek
`score-osmd.js` ([osmd-s8-recite](../../../docs/plans/osmd-s8-recite.md)).
Maatsoort uit (`drawTimeSignatures: false`).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\scripts\osmd-svg
npm run check-s8-a1 -- ..\..\generated\corib-s8-toets\from-ir\alleluia-toon-8.from-ir.musicxml
```
