# `vsa validate` — VSA-invoer controleren

!!! note "Waartoe"
    Controleren of `.vsa`- of Markdown-invoer [geldige VSA-notatie](@) bevat
    vóór verdere verwerking (SVG, Hugo-Markdown, MusicXML). Dit schrijft
    **geen** SVG — zie [`vsa svg`](svg.md).

Controleer of `.vsa`- of Markdown-invoer [geldige VSA-notatie](@) bevat voor
verdere verwerking (SVG, Hugo-Markdown, MusicXML).

## Synopsis

```text
vsa validate [-h] [--config CONFIG] [--summary] path
```

## Beschrijving

`vsa validate` voert drie controlefasen achtereenvolgens uit op elk gevonden
[VSA-blok](@) of [vsa-bestand](@bron):

| Fase        | Controle                                                                   |
| ----------- | -------------------------------------------------------------------------- |
| syntaxscan  | accolades, lege [scopes](@), whitespace in [scopes](@), [pitch-markers](@) |
| [parser](@) | of de [VSA](@) naar interne structuur kan worden omgezet                   |
| semantiek   | of hoogte- en [lengte-modifiers](@) logisch (in aantal) bij elkaar passen  |

`path` mag verwijzen naar één bestand of naar een map:

| Input          | Voorbeeld                                     | Gedrag                                             |
| -------------- | --------------------------------------------- | -------------------------------------------------- |
| `.vsa`-bestand | `examples\minimal\001_plain_text.vsa`         | Controleert één VSA-bestand.                       |
| `.md`-bestand  | `pagina.md`                                   | Controleert alle [VSA-blokken](@) in dat bestand.  |
| Map            | `examples\consumer-minimal\content-source`    | Zoekt recursief naar `.vsa`, `.md` en `.markdown`. |

Als er meerdere fouten zijn, toont de tool ze zoveel mogelijk allemaal in één
keer — je hoeft niet telkens één fout te herstellen en opnieuw te draaien.

## Argumenten en opties

| Naam               | Verplicht | Betekenis                                                                                | Default                               | Beperkingen   |
| ------------------ | --------- | ---------------------------------------------------------------------------------------- | ------------------------------------- | ------------- |
| `path`             | Ja        | Bestand of map om te controleren.                                                        | —                                     | Moet bestaan. |
| `--config CONFIG`  | Nee       | Pad naar een alternatief `vsa.toml` (severity-overrides, zie [config.md](../config.md)). | Auto-detectie van `vsa.toml`          | —             |
| `--summary`        | Nee       | Compacte, eenregelige foutmeldingen tonen, zonder broncontextregel.                      | Uit (volledige context met bronregel) | —             |
| `-h`, `--help`     | Nee       | Toon hulp voor dit subcommando.                                                          | —                                     | —             |

## Output

- **stdout**: bij succes de tekst `OK`; bij fouten de foutmeldingen (zie hieronder).
- **stderr**: niet gebruikt door dit commando; onverwachte fouten uit andere
  commando's gaan naar stderr, maar validatiemeldingen zelf gaan naar stdout.
- Er worden geen bestanden of mappen aangemaakt.

## Exit status

| Exitcode | Betekenis                      |
| -------- | ------------------------------ |
| `0`      | Geen fouten gevonden (`OK`).   |
| `1`      | Eén of meer fouten gevonden.   |

## Voorbeelden — succes

```cmd
vsa validate examples\minimal\001_plain_text.vsa
```

Verwachte output:

```text
OK
```

Ook een map valideert in één keer:

```cmd
vsa validate examples\consumer-minimal\content-source
```

Verwachte output:

```text
OK
```

!!! note "Let op bij `050_svg_demo.vsa`"
    `examples\minimal\050_svg_demo.vsa` is bewust een SVG-renderdemo en
    bevat een [hoogte-markering](@) die niet overeenkomt met het aantal
    scope-modifiers. `vsa validate` op dat bestand faalt daarom met
    `VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH` (zie hieronder). Gebruik voor een
    schone validatie-demo bijvoorbeeld `001_plain_text.vsa` of
    `002_scope_plain.vsa`.

Er worden geen bestanden geschreven; de output verschijnt alleen op het
scherm.

## Voorbeelden — falen

```cmd
vsa validate examples\expected-fail\unclosed-scope.vsa
```

Voorbeeldinvoer (`examples\expected-fail\unclosed-scope.vsa`):

```text
{tekst
```

Verwachte output:

```text
unclosed-scope.vsa:1:1
ERROR: VSA-SYNTAX-UNCLOSED-SCOPE: Scope zonder afsluitende accolade.
{tekst
^
```

Exitcode: `1`.

Fix: sluit de [scope](@) af, bijvoorbeeld `{tekst}`.

Een ander typisch geval — semantische mismatch tussen hoogte- en
[lengte-modifiers](@):

```cmd
vsa validate examples\minimal\050_svg_demo.vsa
```

Verwachte output:

```text
050_svg_demo.vsa:1:32
ERROR: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH: computed = marker + 2
[:] {/Hei_}{/lig_} is de Heer. [:]
                               ^
```

Fix: pas de eindmarkering of het aantal [hoogte-modifiers](@) aan, of draai
`vsa validate --summary` voor een compacte lijst als je meerdere van dit
soort fouten tegelijk wilt zien.

### Veelvoorkomende foutcodes

| Foutcode                                   | Betekenis                                         | Wat doen?                                                                |
| ------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------ |
| `VSA-SYNTAX-EMPTY-SCOPE`                   | `{}` gevonden                                     | Zet tekst of een [zangelement](@) in de [scope](@).                      |
| `VSA-SYNTAX-UNCLOSED-SCOPE`                | `{tekst` zonder `}`                               | Sluit de [scope](@) af.                                                  |
| `VSA-SYNTAX-UNEXPECTED-CLOSE-BRACE`        | Losse `}`                                         | Verwijder of herstel de [scope](@).                                      |
| `VSA-SYNTAX-WHITESPACE-IN-SCOPE`           | Spatie binnen `{...}`                             | Splits tekst buiten de scope of gebruik correcte notatie.                |
| `VSA-SYNTAX-UNCLOSED-PITCH-MARKER`         | `[` zonder `]`                                    | Sluit de [pitch-marker](@) af.                                           |
| `VSA-SYNTAX-PITCH-MARKER-MISSING-COLON`    | Pitch-marker zonder `:`                           | Gebruik bijvoorbeeld `[:]`.                                              |
| `VSA-SYNTAX-INVALID-PITCH-TRANSITION`      | Ongeldige toonhoogte-overgang                     | Gebruik `[<oude-EHM>:<nieuwe-EHM>]` met geldige EHM-waarden.             |
| `VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH`     | Aantallen hoogte-/lengteposities passen niet      | Controleer samengestelde [modifiers](@).                                 |
| `VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH`      | Berekende hoogte komt niet overeen met marker     | Pas de eindmarkering of de scope-modifiers aan; of gebruik een overgang. |
| `VSA-SEMANTIC-PITCH-TRANSITION-MISMATCH`   | Linkerhoogte van `[oud:nieuw]` klopt niet         | Laat de linker-EHM overeenkomen met de huidige cursor.                   |

Zie [diagnostics.md](../diagnostics.md) voor de volledige lijst en severity-instellingen.

## Zie ook

- [`vsa parse`](parse.md) — parserdebugging op één bestand.
- [`vsa svg`](svg.md), [`vsa process`](process.md), [`vsa build-markdown`](build-markdown.md) — draaien impliciet validatie (behalve met `--no-validate`).
- Handleiding: [Validatie](../../guides/validation.md), [CLI-taken](../../guides/cli-taken.md)
- Foutcodes en [severity](@): [config.md](../config.md), [diagnostics.md](../diagnostics.md)
