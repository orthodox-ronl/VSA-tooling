# Changelog

## Unreleased

- MVSA-import: A/T/B spiegelen op **duur** t.o.v. S (niet noot-index/lyrics),
  zodat lange noten + lyric-loze spacers (typisch MSCZ) Bb/T niet verschuiven
- MVSA-import: gerichte lyric-hacks — spaties in `end`-lyrics, `we-der-ke`,
  geen valse `dag-gaan`/`steun-van`/`Heer-richt`, `Ja_-cob` / `zon_-daars`
- MVSA L-normaalvorm: lone standaard-`~` weglaten; `~` blijft bij `&`-melisma
  en na recite-`)` (kuiser + import)
- MVSA-import: ASCII-waarschuwingsbanner na `# Imported:` (schets/checklist;
  alle entrypoints `mvsa`/`mxl`/`mscz import`)
- Testfixture `examples/mvsa/test-alleluia-toon-8.mvsa` hersteld (multi-schets
  voor import/normalize/export-roundtrips; ≠ catalogus-`alleluia-toon-8`)
- MVSA→MusicXML: soft-wrap-`-` over systeembraken houdt de lopende toon
  (beginanker/`@start` reset); zelfde carry in eindanker-check en normalize

## 0.2.0 - MVSA-authoring, export en preview-audio

- MVSA: parser, validatie, normalize/align, **`mvsa kuiser`** (canonieke authoring-vorm)
- Export: MusicXML, MSCZ, PDF, preview-**audio** (`vsa audio` / `vsa mvsa audio` via MuseScore)
- Speelplan / layout voor partituur-navigatie
- Align bewaart leidende `|:` (repeat-start) op alle stokken
- Consumer-pin: tag `0.2.0` i.p.v. alleen `@main`

## 0.1.0 - eerste werkende ontwikkelversie

Bevat:

- parser;
- syntaxvalidatie;
- semantische validatie;
- SVG-rendering;
- Markdown/Hugo preprocessing;
- GitHub Actions CI;
- preview/productie build artifacts.

Nog niet stabiel:

- finale SVG-layout;
- MusicXML-export;
- meerstemmige VSA-uitbreiding.
