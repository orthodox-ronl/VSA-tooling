# Outputreferentie

## Outputtypen

| Output       | Gebruik                                      |
| ------------ | -------------------------------------------- |
| SVG          | Visuele weergave van [VSA-notatie](@bron)    |
| Markdown     | Hugo-geschikte publicatie-output             |
| JSON         | Machineleesbare inspectie                    |
| [AST](@)     | Interne parserrepresentatie                  |
| MusicXML     | Muzikale export                              |
| PDF          | A4-afdruk van één Markdownbestand            |

## SVG

```cmd
vsa svg <input.vsa> <output.svg>
```

SVG wordt gebruikt voor visuele rendering van één VSA-bestand.

## Markdown + SVG-assets

```cmd
vsa build-markdown <input-dir> <output-dir> <assets-dir>
```

| Output     | Voorbeeld                                        |
| ---------- | ------------------------------------------------ |
| Markdown   | `generated\content\toon-1.md`                    |
| SVG        | `generated\static\vsa\toon-1-block-1.svg`        |

## Markdown-output modes

| Mode        | Outputvorm                                      |
| ----------- | ----------------------------------------------- |
| `img`       | `<img class="vsa-notation" src="...">`          |
| `shortcode` | `{{< vsa src="..." >}}`                         |

## JSON bij `vsa blocks --json`

| Veld         | Betekenis                          |
| ------------ | ---------------------------------- |
| `start_line` | Beginregel in Markdownbestand      |
| `end_line`   | Eindregel in Markdownbestand       |
| `metadata`   | Blokinstellingen                   |
| `body`       | VSA-inhoud                         |
| `ast`        | Interne parserstructuur            |

## AST-voorbeeld

```json
{
  "type": "Document",
  "nodes": [
    {
      "type": "ScopeNode",
      "height_modifier": ["/"],
      "text": "Hei",
      "length_modifier": ["_"]
    }
  ]
}
```

## MusicXML

MusicXML-export gebruikt [metadata](@) uit `.vsa`-frontmatter en renderer-/exportconfiguratie.

| Metadata                 | Gebruik in MusicXML                         |
| ------------------------ | ------------------------------------------- |
| `identificatie.title`    | Titel / werknaam                            |
| `identificatie.composer` | Componist of bron                           |
| `muziek.tempo`           | Tempo-informatie                            |
| `muziek.part-name`       | Partijnaam                                  |
| `muziek.midi-*`          | Playbackinstellingen                        |

## PDF (site-Markdown)

```cmd
md pdf <bestand.md>
md pdf <bestand.md> -o uit.pdf
```

A4-PDF van één Markdownbestand na dezelfde VSA/include/pagebreak-keten als
`build-markdown`. Default sibling: `<bronnaam>.pdf`. Vereist Edge, Chrome of
Chromium (`CHROME_PATH`). Verouderd alias: `vsa pdf`. Zie
[`md`](cli/md.md). Partituur-PDF: `mvsa pdf` / `mscz pdf`.

