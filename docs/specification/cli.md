# CLI-contract

Dit document beschrijft het functionele contract van de VSA-CLI.

De taakgerichte uitleg hoort in `docs/guides/`; dit document legt vast welke commando's, exitcodes en hoofdgedragingen onderdeel zijn van de toolinginterface.

# VSA CLI referentie

Deze referentie beschrijft elk commando afzonderlijk.

Gebruik de gebruikershandleiding (`docs/guides/user-guide.md`) voor taakgerichte uitleg.

## Algemene uitgangspunten

De voorbeelden gaan uit van:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
```

Paden zijn relatief aan die map, tenzij je absolute paden gebruikt.

## Exitcodes

| Exitcode | Betekenis                         |
| -------- | --------------------------------- |
| `0`      | commando succesvol                |
| `1`      | fout gevonden of commando mislukt |

In CMD kun je de exitcode direct na een commando bekijken met:

```cmd
echo %ERRORLEVEL%
```

## `vsa --version`

### Doel

Toon de geïnstalleerde versie van de tool.

### Gebruik

```cmd
vsa --version
```

### Output

```text
vsa 0.1.0
```

### Fouten

Als `vsa` niet gevonden wordt:

```text
'vsa' is not recognized...
```

Dan is de tool niet geïnstalleerd in de actieve Python-omgeving.

Oplossing:

```cmd
test
```

## `vsa validate <bestand-of-map>`

### Doel

Controleer of VSA-invoer bruikbaar is voor verdere verwerking.

### Gebruik

```cmd
vsa validate <bestand-of-map>
```

### Inputvarianten

| Input          | Voorbeeld                                  | Gedrag                                          |
| -------------- | ------------------------------------------ | ----------------------------------------------- |
| `.vsa` bestand | `examples\minimal\001_plain_text.vsa`      | controleert één VSA-bestand                     |
| `.md` bestand  | `pagina.md`                                | controleert [VSA-blokken](@) in Markdown        |
| map            | `examples\consumer-minimal\content-source` | zoekt recursief naar `.vsa`, `.md`, `.markdown` |

### Wat wordt gecontroleerd?

| Fase        | Controle                                                                   |
| ----------- | -------------------------------------------------------------------------- |
| syntaxscan  | accolades, lege [scopes](@), whitespace in [scopes](@), [pitch-markers](@) |
| [parser](@) | of de [VSA](@) naar interne structuur kan worden omgezet                   |
| semantiek   | of modifier-aantallen logisch bij elkaar passen                            |

### Succesoutput

```text
OK
```

### Foutoutput

Vorm:

```text
bron:regel:kolom: FOUTCODE: uitleg
```

Voorbeeld:

```text
examples\demo.md:blok-1:1:1: VSA-SYNTAX-EMPTY-SCOPE: Scope zonder zangelement.
```

### Veelvoorkomende foutcodes

| Foutcode                                | Betekenis                                   | Wat doen?                                                |
| --------------------------------------- | ------------------------------------------- | -------------------------------------------------------- |
| `VSA-SYNTAX-EMPTY-SCOPE`                | `{}` gevonden                               | zet tekst of [zangelement](@) in de [scope](@)           |
| `VSA-SYNTAX-UNCLOSED-SCOPE`             | `{tekst` zonder `}`                         | sluit de [scope](@) af                                   |
| `VSA-SYNTAX-UNEXPECTED-CLOSE-BRACE`     | losse `}`                                   | verwijder of herstel de [scope](@)                       |
| `VSA-SYNTAX-WHITESPACE-IN-SCOPE`        | spatie binnen `{...}`                       | splits tekst buiten de scope of gebruik correcte notatie |
| `VSA-SYNTAX-UNCLOSED-PITCH-MARKER`      | `[` zonder `]`                              | sluit [pitch-marker](@) af                               |
| `VSA-SYNTAX-PITCH-MARKER-MISSING-COLON` | [pitch-marker](@) zonder `:`                | gebruik bijvoorbeeld `[:]`                               |
| `VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH`  | aantallen hoogte/lengteposities passen niet | controleer samengestelde [modifiers](@)                  |

### Wat doe je bij fouten?

1. Open het genoemde bestand.
2. Zoek het genoemde [VSA-blok](@).
3. Corrigeer de genoemde fout.
4. Draai hetzelfde commando opnieuw.
5. Herhaal tot `OK`.

## `vsa parse <bestand.vsa> --ast`

### Doel

Debuggen hoe de [parser](@) een VSA-bestand intern ziet: de [Abstract Syntax Tree](@)
([AST](@)) als JSON.

### Gebruik

```cmd
vsa parse <bestand.vsa> --ast
```

### Parameters

| Parameter       | Verplicht | Betekenis                          |
| --------------- | --------- | ---------------------------------- |
| `<bestand.vsa>` | ja        | VSA-bestand                        |
| `--ast`         | nee       | toon de interne structuur als JSON |

### Output met `--ast`

JSON met nodes (`ScopeNode`, `TextNode`, `PitchMarkerNode`, …).

Voorbeeldvorm:

```json
{
  "type": "Document",
  "nodes": [
    {
      "type": "PitchMarkerNode",
      "height_modifier": ["/"]
    },
    {
      "type": "ScopeNode",
      "height_modifier": ["/"],
      "text": "Hei",
      "length_modifier": ["_"]
    }
  ]
}
```

### Output zonder `--ast`

```text
OK
```

als het bestand gelezen kan worden.

### Wanneer gebruiken?

| Gebruik                                          | Ja/nee                  |
| ------------------------------------------------ | ----------------------- |
| gewone eindcontrole                              | nee, gebruik `validate` |
| parserdebugging                                  | ja                      |
| regressietest maken                              | ja                      |
| controleren of tekst als `TextNode` wordt gezien | ja                      |

## `vsa blocks <bestand.md> [--json]`

### Doel

[VSA-blokken](@) in een Markdownbestand vinden.

### Gebruik

```cmd
vsa blocks <bestand.md>
```

```cmd
vsa blocks <bestand.md> --json
```

### Parameters

| Parameter      | Verplicht | Betekenis                               |
| -------------- | --------- | --------------------------------------- |
| `<bestand.md>` | ja        | Markdownbestand                         |
| `--json`       | nee       | toon uitgebreide machineleesbare output |

### Output zonder `--json`

```text
1 VSA-blok(ken) gevonden
```

### Output met `--json`

Per blok:

| Veld         | Betekenis                     |
| ------------ | ----------------------------- |
| `start_line` | beginregel in Markdownbestand |
| `end_line`   | eindregel in Markdownbestand  |
| `metadata`   | blokinstellingen              |
| `body`       | VSA-inhoud                    |
| `ast`        | interne parserstructuur       |

### Wanneer gebruiken?

| Situatie                              | Gebruik         |
| ------------------------------------- | --------------- |
| controleren of blokken herkend worden | zonder `--json` |
| [metadata](@)/body/[AST](@) bekijken  | met `--json`    |

## `vsa svg <input.vsa> <output.svg>`

### Doel

Maak een SVG-afbeelding van één VSA-bestand.

### Gebruik

```cmd
vsa svg <input.vsa> <output.svg>
```

### Parameters

| Parameter      | Verplicht | Betekenis            |
| -------------- | --------- | -------------------- |
| `<input.vsa>`  | ja        | VSA-bronbestand      |
| `<output.svg>` | ja        | doelbestand voor SVG |

### Opties

| Optie                      | Default             | Betekenis             |
| -------------------------- | ------------------- | --------------------- |
| `--max-line-width <getal>` | `vsa.toml` of `800` | maximale regelbreedte |

### Output

Een bestand:

```text
output.svg
```

### Let op

Dit commando verwerkt geen Markdownblokken.

Voor Markdown gebruik je:

```cmd
vsa process
```

of:

```cmd
vsa build-markdown
```

## `vsa process <bestand-of-map> <output-dir>`

### Doel

SVG-bestanden genereren uit [VSA-blokken](@) in Markdown.

### Gebruik

```cmd
vsa process <bestand-of-map> <output-dir>
```

### Inputvarianten

| Input               | Gedrag                                        |
| ------------------- | --------------------------------------------- |
| één Markdownbestand | verwerkt alle [VSA-blokken](@) in dat bestand |
| map                 | zoekt recursief naar Markdownbestanden        |

### Parameters

| Parameter          | Verplicht | Betekenis                   |
| ------------------ | --------- | --------------------------- |
| `<bestand-of-map>` | ja        | invoer                      |
| `<output-dir>`     | ja        | map voor gegenereerde SVG's |

### Opties

| Optie                      | Default             | Betekenis           |
| -------------------------- | ------------------- | ------------------- |
| `--no-validate`            | niet actief         | validatie overslaan |
| `--max-line-width <getal>` | `vsa.toml` of `800` | SVG-regelbreedte    |

### Output

Alleen SVG-bestanden.

Geen Markdown wordt herschreven.

### Wanneer gebruiken?

Gebruik dit als je:

- alleen SVG's wilt;
- wilt controleren hoe SVG-bestanden eruitzien;
- nog geen Hugo-Markdown wilt genereren.

## `vsa build-markdown <input-dir> <output-dir> <assets-dir>`

### Doel

Maak Hugo-geschikte Markdown en SVG-bestanden.

### Gebruik

```cmd
vsa build-markdown <input-dir> <output-dir> <assets-dir>
```

### Parameters

| Parameter      | Verplicht | Betekenis                                 |
| -------------- | --------- | ----------------------------------------- |
| `<input-dir>`  | ja        | bronmap met handmatig geschreven Markdown |
| `<output-dir>` | ja        | doelmap voor gegenereerde Markdown        |
| `<assets-dir>` | ja        | doelmap voor gegenereerde SVG-bestanden   |

### Output

| Output   | Voorbeeld                                        |
| -------- | ------------------------------------------------ |
| Markdown | `generated\content\toon-1.md`                    |
| SVG      | `generated\static\vsa\toon-1-block-1.svg`        |

### Wat wordt vervangen?

In bron-Markdown:

```markdown
::: vsa-notatie
{tekst}
:::
```

wordt in output-Markdown:

```html
<img class="vsa-notation" src="/vsa/demo-block-1.svg" alt="VSA notatie">
```

of:

```go-html-template
{{< vsa src="/vsa/demo-block-1.svg" >}}
```

### Opties

| Optie                          | Default              | Betekenis              |
| ------------------------------ | -------------------- | ---------------------- |
| `--assets-url-prefix <prefix>` | `vsa.toml` of `/vsa` | URL-prefix in Markdown |
| `--max-line-width <getal>`     | `vsa.toml` of `800`  | SVG-regelbreedte       |
| `--output-mode img`            | `vsa.toml` of `img`  | gebruik `<img>`        |
| `--output-mode shortcode`      | `vsa.toml` of `img`  | gebruik Hugo shortcode |

### Padvoorbeelden

Commando:

```cmd
vsa build-markdown examples\consumer-minimal\content-source generated\content generated\static\vsa
```

Betekenis:

| Deel   | Pad                                        | Betekenis       |
| ------ | ------------------------------------------ | --------------- |
| input  | `examples\consumer-minimal\content-source` | bron            |
| output | `generated\content`                        | nieuwe Markdown |
| assets | `generated\static\vsa`                     | SVG-bestanden   |

### Wat doe je bij problemen?

| Probleem                      | Controle                              |
| ----------------------------- | ------------------------------------- |
| build stopt met fout          | draai `vsa validate <input-dir>`      |
| afbeelding niet zichtbaar     | controleer `assets-url-prefix`        |
| shortcode zichtbaar als tekst | controleer Hugo shortcode-bestand     |
| oude output blijft zichtbaar  | verwijder `generated` en bouw opnieuw |

## `vsa pdf <bestand.md>`

### Doel

Maak een A4-PDF van één Markdownbestand: VSA-blokken, includes en pagebreaks
worden net als bij `build-markdown` opgelost; daarna print Edge/Chrome.

### Gebruik

```cmd
vsa pdf <bestand.md> -o uit.pdf
```

### Output

| Output | Voorbeeld        |
| ------ | ---------------- |
| PDF    | `uit.pdf`        |

Fouten (validatie) gebruiken hetzelfde formaat als `vsa validate`.

## `vsa.toml`

### Doel

Projectdefaults vastleggen.

### Voorbeeld

```toml
[rendering]
max-line-width = 800

[hugo]
assets-url-prefix = "/vsa"
output-mode = "img"

# Alternatief:
# output-mode = "shortcode"
```

### Defaults

| Instelling          | Default |
| ------------------- | ------- |
| `max-line-width`    | `800`   |
| `assets-url-prefix` | `/vsa`  |
| `output-mode`       | `img`   |

### Voorrang

```text
CLI-optie
  ↓
vsa.toml
  ↓
default
```

## Scripts

| Script                         | Wat doet het?               |
| ------------------------------ | --------------------------- |
| `test`                         | installeert lokale omgeving |
| `scripts\test.cmd`             | draait tests                |
| `scripts\ci.cmd`               | draait lokale CI            |
| `serve`                        | MkDocs docs lokaal serveren |

## Diagnosevolgorde

Bij problemen:

```cmd
vsa validate <input>
```

Daarna:

```cmd
scripts\test.cmd
```

Daarna eventueel:

```cmd
vsa blocks <bestand.md> --json
```

En als rendering vreemd is:

```cmd
vsa svg <bestand.vsa> output.svg
start output.svg
```

## `vsa template validate <pad>`

### Doel

Valideer een `template.yaml` (of een map met zulke bestanden) tegen schema en
documentregels.

### Gebruik

```cmd
vsa template validate docs\specification-vsa-templates\library
vsa template validate docs\specification-vsa-templates\library\tropaar-toon-4\template.yaml
```

### Output

Bij succes: één `OK`-regel per bestand. Bij fout: `pad: ERROR: CODE: …` en
exitcode `1`.

## `vsa mvsa …`

### Doel

Draft-tooling voor meerstemmige `.mvsa`-bestanden (L + SATB). Zie
[specification-mvsa](../specification-mvsa/README.md) en de man-pagina
[reference/cli/mvsa.md](../reference/cli/mvsa.md).

### Gebruik

```cmd
vsa mvsa validate examples\mvsa
vsa mvsa validate examples\mvsa\alleluia-toon-8.mvsa
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa --section schets-a-bladcijfer -o generated\intocht-a.mxl
```

### Opties (`musicxml`)

| Optie                | Betekenis                                                          |
| -------------------- | ------------------------------------------------------------------ |
| `-o`, `--output`     | Uitvoerbestand (default: `<stem>.mxl` naast het bronbestand).      |
| `--section SECTION`  | Alleen deze `@sectie`-id exporteren (default: alle secties).       |

### Output

- `validate`: per geldig bestand `<pad>: OK`; anders diagnostiek en exitcode `1`.
- `musicxml`: `Geschreven: <pad>` of fout op stderr.