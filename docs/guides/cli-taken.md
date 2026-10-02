# CLI-taken

Deze pagina helpt kiezen welk commando bij welke taak hoort. Voor de
volledige syntax, alle argumenten/opties en foutgevallen per commando: zie de
man-pagina's onder [CLI-referentie](../reference/cli/index.md).

## Commando kiezen

| Taak                                      | Commando                                                                                                                                     |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Versie tonen                              | [`vsa --version`](../reference/cli/index.md)                                                                                                 |
| [VSA-notatie](@bron) controleren          | [`vsa validate <bestand-of-map>`](../reference/cli/validate.md)                                                                              |
| [AST](@) bekijken                         | [`vsa parse <bestand.vsa> --ast`](../reference/cli/parse.md)                                                                                 |
| [VSA-blokken](@) in Markdown vinden       | [`vsa blocks <bestand.md>`](../reference/cli/blocks.md)                                                                                      |
| Eén SVG maken                             | [`vsa svg <input.vsa> <output.svg>`](../reference/cli/svg.md)                                                                                |
| Markdownbestanden verwerken naar SVG      | [`vsa process <input> <output>`](../reference/cli/process.md)                                                                                |
| [Hugo-output](@) genereren                | [`vsa build-markdown …`](../reference/cli/build-markdown.md)                                                                                 |
| Markdown + VSA naar A4-PDF                | [`vsa pdf <bestand.md>`](../reference/cli/pdf.md)                                                                                            |
| `zoek=`-includes oplossen naar catalogus  | [`vsa resolve-catalogus <bestand.md>`](../reference/cli/resolve-catalogus.md)                                                                |
| Lettergreepstreepjes (bestand of map)     | [`vsa syllabify <pad>`](../reference/cli/syllabify.md)                                                                                       |
| Platte gezongen tekst (zoekindex)         | [`vsa text <pad>`](../reference/cli/text.md) (`.vsa` / `.mvsa` / MusicXML / `.mscz`)                                                         |
| MusicXML exporteren                       | [`vsa musicxml <input.vsa> <output.mxl>`](../reference/cli/musicxml.md)                                                                      |
| mvsa valideren (draft)                    | [`vsa mvsa validate <pad>`](../reference/cli/mvsa.md#vsa-mvsa-validate)                                                                      |
| mvsa → SATB MusicXML (draft)              | [`vsa mvsa musicxml <pad> [-o …] [--section …]`](../reference/cli/mvsa.md#vsa-mvsa-musicxml)                                                 |
| mvsa → Coria met hulptekst-keuze          | [`vsa mvsa musicxml … --hulptekst-as-parts`](../reference/cli/mvsa.md#vsa-mvsa-musicxml) + [`@taal`](../specification-mvsa/keywords.md#taal) |
| mvsa → blad met tweede tekstregel         | [`vsa mvsa mscz … --hulptekst`](../reference/cli/mvsa.md#vsa-mvsa-mscz)                                                                      |
| mvsa → MuseScore / print-PDF (draft)      | [`vsa mvsa mscz`](../reference/cli/mvsa.md#vsa-mvsa-mscz) / [`pdf`](../reference/cli/mvsa.md#vsa-mvsa-pdf)                                   |
| `.mvsa` leren schrijven                   | [mvsa schrijven 101](mvsa-schrijven-101.md)                                                                                                  |

## Exitcodes

| Exitcode | Betekenis                         |
| -------- | --------------------------------- |
| `0`      | commando succesvol                |
| `1`      | fout gevonden of commando mislukt |

Controle in CMD:

```cmd
echo %ERRORLEVEL%
```

## Veelgebruikte voorbeelden

```cmd
vsa validate examples\minimal\001_plain_text.vsa
```

```cmd
vsa blocks examples\minimal\031_markdown_block_metadata.md --json
```

```cmd
vsa musicxml mijn-lied.vsa mijn-lied.mxl
```

```cmd
vsa text mijn-lied.mscz.mxl -o generated\mijn-lied.mscz.lyrics.txt
```

## Bronnen

Gebaseerd op:

- `docs/guides/user-guide.md`
- `docs/reference/cli/index.md` (en de losse man-pagina's per subcommando)
- `docs/guides/svg-export.md`
- `docs/guides/musicxml-export.md`
