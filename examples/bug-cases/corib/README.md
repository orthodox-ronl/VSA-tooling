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

## Uitslag (2026-10-31, producttoets)

| Stuk              | MuseScore-ref (S8)                         | OSMD-product (`mvsa svg --engine osmd`)                         | Oordeel   |
| ----------------- | ------------------------------------------ | --------------------------------------------------------------- | --------- |
| alleluia-toon-8   | breve `\|\|O\|\|` + tekst-only middens     | alle spacer-koppen **zichtbaar** (zwarte stokloze koppen)       | **FAIL**  |
| alleluia-toon-3   | idem + melisma-slurs ok op ref             | spaties/koppen i.p.v. tekst-only recite; 4/4 zichtbaar          | **FAIL**  |
| alleluia-toon-2   | idem                                       | zelfde spacer-lek                                               | **FAIL**  |
| derde-antifoon    | (ref aanwezig; veel S8 in from-ir)         | OSMD-SVG gegenereerd; zelfde A1-gat verwacht                    | **FAIL*** |

\*Antifoon: from-ir bevat honderden `notehead none`-spacers; product-OSMD
heeft geen A1-hide (zie hieronder).

### Oorzaak (kort)

1. **from-ir emit is correct (A1-marker):** spacers = `stem none` +
   `notehead none` + lyric; midden = `notehead breve` + `stem none`
   (bevestigd in `generated/corib-s8-toets/from-ir/*.from-ir.musicxml`).
2. **Productketen past de bibliotheek-A1-adapter niet toe:**
   `scripts/osmd-svg/render.mjs` rendert OSMD **zonder** spacer-koppen te
   verbergen. OSMD/VexFlow tekent `notehead none` als zichtbare kop
   ([osmd-s8-recite](../../../docs/plans/osmd-s8-recite.md) run 1).
3. Bijvangst: OSMD toont vaak **maatsoort 4/4**; MuseScore-ref (layout
   `muziek` / partituur) niet — apart van S8, wel productverschil.

### Volgende fix-run (nog niet gedaan)

Poort A1-hide naar `scripts/osmd-svg` (zelfde marker-contract als
bibliotheek `score-osmd.js`), daarna opnieuw product-SVG genereren en
visueel toetsen tegen deze siblings.
