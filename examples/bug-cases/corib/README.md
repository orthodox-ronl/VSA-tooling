# CoriB / OSMD producttoets — recite (S8)

Corpus voor **visuele product-tegen-product**-toets van Score-IR → from-ir →
OSMD tegen MuseScore-bladproducten. Geen peiling op bbox-oppervlaktes als
acceptatie; die mag alleen helpen bij bouwen.

Contract: checklist **S8** ([canonical-checklists](../../../docs/formats/canonical-checklists.md)),
brug [partituur-ir §7](../../../docs/plans/partituur-ir.md), plan
[osmd-s8-recite](../../../docs/plans/osmd-s8-recite.md), CoriB
[corib-mvp](../../../docs/plans/corib-mvp.md).

**Branch:** productwerk op `corib`; toets-artifacts (`toets-png/` +
`toets-svg/`) moeten **up-to-date op `development`** staan na elke
OSMD/S8/S13-wijziging die het schermbeeld raakt.

## Corpus

| Bron (`.mvsa`)                       | MuseScore-ref (sibling)   | Waarom                                  |
| ------------------------------------ | ------------------------- | --------------------------------------- |
| `alleluia-toon-8.mvsa`               | `.mvsa.svg` + `.mvsa.pdf` | Canonieke lange `()`-recite             |
| `alleluia-toon-3.mvsa`               | idem                      | Korte recite + zelfde-toon-vervolg → S8 |
| `alleluia-toon-2.mvsa`               | idem                      | Extra lange `()`-recite                 |
| `derde-antifoon-zondag-hemelum.mvsa` | idem                      | Langere praktijkcasus (veel recite)     |

Referentie-SVG/PDF: door de beheerder gegenereerd met `mvsa svg` / `mvsa pdf`
(MuseScore). OSMD-product: `mvsa svg --engine osmd`.

## Vastgelegde toetsbestanden

| Map          | Inhoud                                                                 |
| ------------ | ---------------------------------------------------------------------- |
| `toets-svg/` | `{stuk}.ref.svg` (= kopie MuseScore-sibling) + `{stuk}.osmd.svg`       |
| `toets-png/` | Raster van die SVG’s: `{stuk}.ref.png` vs `{stuk}.osmd.png`            |

Na elke wijziging aan from-ir / OSMD-adapter / S8/S13: **beide mappen
opnieuw vullen en committen** (zie hieronder). Anders kijkt de toets naar
verouderde beelden.

## Producten regenereren (OSMD + toetsbestanden)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling

REM OSMD-SVG per stuk (ook naar generated\ voor debug)
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-8.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\alleluia-toon-3.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-3.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\alleluia-toon-2.mvsa -o generated\corib-s8-toets\osmd\alleluia-toon-2.osmd.svg --engine osmd
mvsa svg examples\bug-cases\corib\derde-antifoon-zondag-hemelum.mvsa -o generated\corib-s8-toets\osmd\derde-antifoon-zondag-hemelum.osmd.svg --engine osmd

REM Vastleggen in toets-svg (ref = MuseScore-sibling; osmd = product)
copy /Y generated\corib-s8-toets\osmd\*.osmd.svg examples\bug-cases\corib\toets-svg\
copy /Y examples\bug-cases\corib\alleluia-toon-8.mvsa.svg examples\bug-cases\corib\toets-svg\alleluia-toon-8.ref.svg
copy /Y examples\bug-cases\corib\alleluia-toon-3.mvsa.svg examples\bug-cases\corib\toets-svg\alleluia-toon-3.ref.svg
copy /Y examples\bug-cases\corib\alleluia-toon-2.mvsa.svg examples\bug-cases\corib\toets-svg\alleluia-toon-2.ref.svg
copy /Y examples\bug-cases\corib\derde-antifoon-zondag-hemelum.mvsa.svg examples\bug-cases\corib\toets-svg\derde-antifoon-zondag-hemelum.ref.svg
```

PNG’s: open de SVG’s in de browser of rasteriseer (Puppeteer in
`scripts\osmd-svg`) naar `toets-png\*.ref.png` / `*.osmd.png`. Cloud-agents
doen dat in dezelfde ronde als de SVG-update.

Toets: open `toets-svg\*.ref.svg` naast `*.osmd.svg` (of de PNG’s).
Eindbeeld S8: Al = gewone noot → le = stokloze `||O||` (breve) →
middenlettergrepen = **alleen tekst** (geen koppen) → cadens.

## Uitslag (producttoets)

| Stuk            | MuseScore-ref (S8)                     | OSMD-product (`mvsa svg --engine osmd`)                       | Oordeel    |
| --------------- | -------------------------------------- | ------------------------------------------------------------- | ---------- |
| alleluia-toon-8 | breve `\|\|O\|\|` + tekst-only middens | spacer-koppen verborgen (A1); lyrics compleet; breve stokloos | **PASS**\* |
| alleluia-toon-3 | idem                                   | idem                                                          | **PASS**\* |
| alleluia-toon-2 | idem                                   | idem                                                          | **PASS**\* |
| derde-antifoon  | idem                                   | idem (A1 machinecheck)                                        | **PASS**\* |

\*Pixel-pariteit MuseScore↔OSMD is geen eis. S8-eisen wél: geen zichtbare
spacer-koppen; lyrics op die posities; breve als MuseScore-``||O||``-path
(`data-osmd-breve-glyph`); lettergreepstreepjes zichtbaar; lyrics in
**Source Sans 3**; OSMD-SVG met witte `rect.vsa-page-bg` (zelfde idee als
MuseScore-sibling). A1-adapter koppelt spacer/breve per measure-id (niet via
een y-systeemdrempel).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\scripts\osmd-svg
npm run check-s8-a1 -- ..\..\generated\corib-s8-toets\from-ir\alleluia-toon-8.from-ir.musicxml
```

### Fix (2026-10-31)

`scripts/osmd-svg/render.mjs` draait na OSMD-render de A1-adapter
(`s8-a1-adapter.js`) — spacer-hide + MuseScore-breve-path; Source Sans 3
via lokale WOFF2 + `@font-face` in de SVG. Contract:
[osmd-s8-recite](../../../docs/plans/osmd-s8-recite.md).
Maatsoort uit (`drawTimeSignatures: false`).

**S13 / T «lu» (alleluia-toon-2):** gestipte whole uit same-pitch-collapse
kreeg in Score-IR per ongeluk ELM ``~`` (gevulde kwart in OSMD). Fix:
ELM ``__.`` (+ ``lyricIndex`` per stem-volgorde, niet S-event-index).
Zie [score-ir](../../../docs/formats/score-ir.md) / [partituur-ir §4.4](../../../docs/plans/partituur-ir.md).

**CoriB-dichtheid + S8 op lange stukken:** graveerprofiel `coribCompact`;
A1-adapter groepeert op measure-id (y-drempel 150 px mengde systemen en
liet breve/spacers als zwarte koppen staan); lettergreepstreepjes niet
meer verbergen; maatnummer 1 nagetekend.
