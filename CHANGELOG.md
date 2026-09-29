# Changelog

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
