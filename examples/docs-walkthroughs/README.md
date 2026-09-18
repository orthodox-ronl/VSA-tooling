# Docs-walkthroughs

Lokale fixtures voor mini-walkthroughs in guides, getting-started en
`docs/reference/voorbeelden/`. Geen runtime-afhankelijkheid van VSA-demo of
bron — bestanden hier mogen vrij worden aangepast.

## Naamconventie

Bestandsnamen beschrijven **wat het voorbeeld doet** (`svg-phrase-kort`,
`validate-unclosed-scope`, `coria-oefenlink`), niet de oorspronkelijke
bronnaam. Herkomst staat in deze README.

## Inhoud

| Pad                           | Doel                                          | Herkomst (onderwerp)                                                  |
| ----------------------------- | --------------------------------------------- | --------------------------------------------------------------------- |
| `svg-phrase-kort.vsa`         | Korte geldige frase → SVG / validate-OK       | Zelfde inhoud als `minimal/valid-demo.vsa` (“Heilig is de Heer”)      |
| `svg-phrase-lang.vsa`         | Langere regel + `--max-line-width`            | Uitbreiding van de Heilig-frase (`minimal/100_multiline_demo.vsa`)    |
| `svg-glyphs-overzicht.vsa`    | Breed glyph-/syntaxoverzicht → SVG            | Oude Hugo-demo `voorbeelden/rendering/glyphs-basis`                   |
| `svg-glyphs-hoogte.vsa`       | Compacte hoogtemarkers                        | Zelfde herkomst (sectie hoogtemarkers)                                |
| `svg-glyphs-lengte.vsa`       | Compacte lengtemarkers                        | Zelfde herkomst (sectie lengtemarkers)                                |
| `halftoon-accidens-cursor.vsa` | Liturgikon-kruis: accidens ≠ chromatische cursor; eindmarkers OK | Uitleg in `docs/guides/liturgikon-notatie.md` + `examples.md` |
| `validate-unclosed-scope.vsa` | Bewuste syntaxfout voor `vsa validate`        | Zelfde patroon als `expected-fail/unclosed-scope.vsa`                 |
| `coria-oefenlink/`            | Markdown + VSA + Coria-sibling voor oefenlink | Lokale kopie van tropaar zondag toon 3 (koormap Groningen / VSA-demo) |

## SVG-previews in docs

Gecommitte preview-SVG’s staan onder
`docs/guides/assets/walkthroughs/` en worden gegenereerd vanuit dit
manifest:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\sync-docs-walkthrough-svgs.py
```

CI/docs-check: `python scripts\sync-docs-walkthrough-svgs.py --check`.
