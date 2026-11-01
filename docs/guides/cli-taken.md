# CLI-taken

Deze pagina helpt kiezen welk commando bij welke taak hoort. Voor de
volledige syntax, alle argumenten/opties en foutgevallen per commando: zie de
man-pagina's onder [CLI-referentie](../reference/cli/index.md).

## Commando kiezen

| Taak                                                    | Commando                                                                                                                                                                                     |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Versie tonen                                            | [`vsa --version`](../reference/cli/index.md)                                                                                                                                                 |
| [VSA-notatie](@bron) controleren                        | [`vsa validate <bestand-of-map>`](../reference/cli/validate.md)                                                                                                                              |
| [AST](@) bekijken                                       | [`vsa parse <bestand.vsa> --ast`](../reference/cli/parse.md)                                                                                                                                 |
| [VSA-blokken](@) in Markdown vinden                     | [`vsa blocks <bestand.md>`](../reference/cli/blocks.md)                                                                                                                                      |
| Eén SVG maken (muziek-only; default sibling `.vsa.svg`) | [`vsa svg <input.vsa> [-o …]`](../reference/cli/svg.md)                                                                                                                                      |
| Markdownbestanden verwerken naar SVG                    | [`vsa process <input> <output>`](../reference/cli/process.md)                                                                                                                                |
| [Hugo-output](@) genereren                              | [`vsa build-markdown …`](../reference/cli/build-markdown.md)                                                                                                                                 |
| Pagina-Markdown naar A4-PDF (`index.md.pdf`)            | [`markdown pdf <bestand.md>`](../reference/cli/markdown.md#markdown-pdf)                                                                                                                     |
| Partituur-PDF uit `.vsa`                                | [`vsa pdf <pad.vsa>`](../reference/cli/pdf.md)                                                                                                                                               |
| `zoek=`-includes oplossen naar catalogus                | [`vsa resolve-catalogus <bestand.md>`](../reference/cli/resolve-catalogus.md)                                                                                                                |
| Lettergreepstreepjes (bestand of map)                   | [`vsa syllabify <pad>`](../reference/cli/syllabify.md)                                                                                                                                       |
| Platte gezongen tekst uit `.vsa`                        | [`vsa text <pad.vsa>`](../reference/cli/text.md)                                                                                                                                             |
| Platte gezongen tekst uit `.mvsa` of `.mscz`            | [`mvsa text`](../reference/cli/mvsa.md#mvsa-text) / [`mscz text`](../reference/cli/mscz.md)                                                                                                  |
| MusicXML exporteren                                     | [`vsa musicxml <input.vsa> <output.mxl>`](../reference/cli/musicxml.md) (Coria: `--syllabify`)                                                                                               |
| Standaardproducten (geen partituur-PDF)                 | [`vsa products`](../reference/cli/products.md) / [`mvsa products`](../reference/cli/mvsa.md#mvsa-products) / [`mscz products`](../reference/cli/mscz.md)                                     |
| `.vsa` canonieke notatie controleren                    | [`vsa validate`](../reference/cli/validate.md) (geen aparte `vsa normalize`)                                                                                                                 |
| mvsa valideren (draft)                                  | [`mvsa validate <pad>`](../reference/cli/mvsa.md#mvsa-validate)                                                                                                                              |
| `.mvsa` normaliseren (spelling / uitlijning)            | [`mvsa normalize`](../reference/cli/mvsa.md#mvsa-normalize)                                                                                                                                  |
| `.mxl` naar Coria/playback-profiel                      | [`mxl normalize`](../reference/cli/mxl.md)                                                                                                                                                   |
| mvsa → SATB MusicXML (draft)                            | [`mvsa mxl <pad> [-o …] [--section …]`](../reference/cli/mvsa.md#mvsa-mxl)                                                                                                                   |
| mvsa → Score-IR JSON (partituur; scherm/CoriB)          | [`mvsa score-ir <pad> [-o …]`](../reference/cli/mvsa.md#mvsa-score-ir)                                                                                                                       |
| Score-IR + MusicXML-siblings (OSMD-brug)                | [`mvsa score-ir <pad> --musicxml`](../reference/cli/mvsa.md#mvsa-score-ir) (siblings ``.score-ir.json`` + ``.from-ir.musicxml``)                                                             |
| mvsa → partituur-SVG (koormap; MuseScore of OSMD)       | [`mvsa svg <pad.mvsa> [-o …]`](../reference/cli/mvsa.md#mvsa-svg) (`--engine osmd` optioneel)                                                                                                |
| mscz → kale muziek-SVG                                  | [`mscz svg`](../reference/cli/mscz.md)                                                                                                                                                       |
| mscz → layout/leesbaarheid opnieuw                      | [`mscz normalize`](../reference/cli/mscz.md) (`--layout partituur`/`muziek`/`plain`)                                                                                                         |
| mvsa → Coria met translit-keuze (oefenen)               | [`mvsa mxl … --translit-as-parts`](../reference/cli/mvsa.md#mvsa-mxl) + [`@taal`](../specification-mvsa/keywords.md#taal)                                                                    |
| mvsa → blad/SVG met tweede tekstregel                   | [`mvsa mscz` / `svg … --translit`](../reference/cli/mvsa.md#mvsa-mscz) ([productbesluiten](../plans/kerkslavisch-transliteratie.md#5a-besluiten-productmodel-nu))                            |
| mvsa → MuseScore-partituur                              | [`mvsa mscz`](../reference/cli/mvsa.md#mvsa-mscz)                                                                                                                                            |
| Losse partituur-PDF uit `.mvsa` / `.mscz`               | [`mvsa pdf`](../reference/cli/mvsa.md#mvsa-pdf) / [`mscz pdf`](../reference/cli/mscz.md). Niet via `products`.                                                                               |
| mvsa → preview-audio (draft)                            | [`mvsa mp3`/`ogg`/`wav`](../reference/cli/mvsa.md#mvsa-mp3) (of top-level [`vsa audio`](../reference/cli/audio.md))                                                                          |
| MusicXML / MuseScore → `.mvsa` (**werkbank**)           | [`mxl mvsa`](../reference/cli/mxl.md) / [`mscz mvsa`](../reference/cli/mscz.md)                                                                                                              |
| Score ↔ `.mvsa` controleren (t.o.v. verse import)       | [`mscz compare`](../reference/cli/mscz.md#mscz-compare)                                                                                                                                      |
| Score → mvsa + ankers (navigatie / foutzoeken)          | `mxl mvsa …` / `mscz mvsa …` (default `ag-vsa`) daarna [`validate`](../reference/cli/mvsa.md#mvsa-validate)                                                                                  |
| `.mvsa` naar andere tonica (toonsoort)                  | [`mvsa transpose <pad> --to F4`](../reference/cli/mvsa.md#mvsa-transpose)                                                                                                                    |
| `.mvsa` leren schrijven                                 | [mvsa schrijven 101](mvsa-schrijven-101.md)                                                                                                                                                  |

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
vsa text mijn-lied.vsa
mvsa text mijn-lied.mvsa
mscz text mijn-lied.mscz
```

Elk van die commando’s leest alleen de eigen extensie. Platte tekst voor
editorzoeken hoort als veld `zoektekst` in de YAML-frontmatter van een
canonieke `.vsa` of `.mvsa` — zie [zoektekst](../formats/zoektekst.md).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa zoektekst examples\mvsa\alleluia-toon-1.mvsa
vsa zoektekst examples\mvsa --check
```

`products` schrijft het lyrics-bestand mee. Je hoeft het niet met de hand
naast de bron te zetten voor editorzoeken. Welk script bij welke taak
hoort: [Scripts (cmd)](../formats/scripts.md).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mxl mvsa generated\alleluia.mxl -o generated\alleluia.mxl.mvsa
mvsa validate generated\alleluia.mxl.mvsa
```

Andere tonica (modus blijft gelijk), sibling-uitvoer of `-o`:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa transpose examples\bug-cases\alleluia-9b-toon-3-vokn.mvsa --to F4
mvsa validate examples\bug-cases\alleluia-9b-toon-3-vokn.transposed.mvsa
```

## Bronnen

Gebaseerd op:

- `docs/guides/user-guide.md`
- `docs/reference/cli/index.md` (en de losse man-pagina's per subcommando)
- `docs/guides/svg-export.md`
- `docs/guides/musicxml-export.md`
