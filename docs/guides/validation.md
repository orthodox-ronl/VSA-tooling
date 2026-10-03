# Validatie

!!! note "Voor wie / wanneer"
    **Voor:** notatie-auteur die foutmeldingen wil begrijpen en oplossen.
    **Wanneer:** tijdens schrijven, vóór export, of in CI.
    **Niet:** SVG maken — dat is [SVG exporteren](svg-export.md) /
    [`vsa svg`](../reference/cli/svg.md).

**Antwoord in het kort:** `vsa validate` controleert of [VSA-notatie](@bron)
bruikbaar is. Lees de foutregel (bestand → blok → regel → code), herstel, opnieuw.

## Wanneer valideren?

| Situatie                         | Valideren?                               |
| -------------------------------- | ---------------------------------------- |
| Tijdens het schrijven van `.vsa` | Ja                                       |
| Vóór SVG / MusicXML / Hugo-build | Ja                                       |
| In CI op content-source          | Ja                                       |
| Alleen snel een plaatje bekijken | Optioneel — zie validate ≠ svg hieronder |

## Validate ≠ svg

| Commando                                       | Controleert semantiek? | Schrijft SVG? |
| ---------------------------------------------- | ---------------------- | ------------- |
| [`vsa validate`](../reference/cli/validate.md) | Ja                     | Nee           |
| [`vsa svg`](../reference/cli/svg.md)           | Nee (alleen parse)     | Ja            |

Voorbeeld: `examples\minimal\050_svg_demo.vsa` kan op `validate` falen
(semantische mismatch) en toch met `vsa svg` renderen. Wil je
[geldige VSA-notatie](@), draai eerst `validate`.

## Snel starten

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\docs-walkthroughs\svg-phrase-kort.vsa
```

Bij succes: `OK`. Map valideren:

```cmd
vsa validate examples\consumer-minimal\content-source
```

## Wat wordt gecontroleerd?

| Controle                                                                 | Voorbeeld van fout |
| ------------------------------------------------------------------------ | ------------------ |
| [scope](@) is goed afgesloten                                            | `{tekst`           |
| [scope](@) is niet leeg                                                  | `{}`               |
| geen whitespace binnen [scope](@)                                        | `{te kst}`         |
| geen losse sluitaccolade                                                 | `tekst}`           |
| [pitch-marker](@) is goed afgesloten                                     | `[//:`             |
| [pitch-marker](@) heeft dubbele punt                                     | `[//]`             |
| [toonhoogte-overgang](@) verbindt opeenvolgende hoogtes zonder mismatch  | zie liturgie-keten |
| [hoogte-modifier](@)- en [lengte-modifier](@)-posities passen bij elkaar | `{/&\tekst_}`      |

## Succesoutput

Bij geldige notatie schrijft `vsa validate` alleen:

```text
OK
```

Exitcode: `0`. Details: [`vsa validate`](../reference/cli/validate.md).

## Foutoutput lezen

Concrete [fail-fixture](@)
(`examples\docs-walkthroughs\validate-unclosed-scope.vsa`):

```text
{tekst
```

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\docs-walkthroughs\validate-unclosed-scope.vsa
```

```text
validate-unclosed-scope.vsa:1:1
ERROR: VSA-SYNTAX-UNCLOSED-SCOPE: Scope zonder afsluitende accolade.
{tekst
^
```

| Deel                           | Betekenis                                  |
| ------------------------------ | ------------------------------------------ |
| `validate-unclosed-scope.vsa`  | bestand waarin de fout zit                 |
| `1:1`                          | regel en kolom                             |
| `VSA-SYNTAX-UNCLOSED-SCOPE`    | foutcode ([diagnostic](@))                 |
| tekst erna + `^`               | uitleg en positie-indicator                |

**Fix:** sluit de [scope](@) af, bijvoorbeeld `{tekst}`.

In Markdown met [VSA-blokken](@) ziet de locatie er zo uit:

```text
examples\demo.md:blok-1:1:1: VSA-SYNTAX-EMPTY-SCOPE: Scope zonder zangelement.
```

| Deel                     | Betekenis                           |
| ------------------------ | ----------------------------------- |
| `examples\demo.md`       | Markdown-bestand                    |
| `blok-1`                 | eerste [VSA-blok](@) in dat bestand |
| `1:1`                    | regel en kolom binnen dat blok      |
| `VSA-SYNTAX-EMPTY-SCOPE` | foutcode ([diagnostic](@))          |
| tekst erna               | uitleg                              |

## Diagnose bij problemen

| Symptoom / melding                               | Oorzaak                                            | Fix                                                                                      |
| ------------------------------------------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `VSA-SYNTAX-EMPTY-SCOPE`                         | `{}` of lege [scope](@)                            | [Zangelement](@) tussen `{` en `}` zetten                                                |
| `VSA-SYNTAX-UNCLOSED-SCOPE` (of vergelijkbaar)   | Ontbrekende `}`                                    | [Scope](@) afsluiten; regel/kolom in de melding volgen                                   |
| Semantische modifier-mismatch                    | Aantal hoogte- ≠ lengte-posities                   | [Modifiers](@) tellen; zie [semantics](../specification/semantics.md)                    |
| `VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH`            | Lokale markering wijkt af van berekende cursor     | Markering of scopes aanpassen; of bewuste sprong via [toonhoogte-overgang](@)            |
| `VSA-SEMANTIC-PITCH-TRANSITION-MISMATCH`         | Linker-EHM van `[oud:nieuw]` klopt niet met cursor | Linkerhoogte laten matchen met de huidige markering/cursor                               |
| `OK` lokaal, CI faalt                            | Andere map / andere `vsa.toml`                     | Zelfde pad als CI; severity-overrides controleren                                        |
| SVG werkt, validate faalt                        | `svg` doet geen volle semantiek                    | Verwacht gedrag — zie hierboven; herstel of accepteer bewust                             |

### Liturgie-keten: bewuste hoogtesprong

Eindigt een antifoon op `[//:]` en begint een tropaar “in het echt” op
`[/:]`, dan faalt validate zonder overgang. Zet tussen beide stukken een
stille [toonhoogte-overgang](@) — die verschijnt niet op het blad:

```text
[//:] … einde antifoon … [//:]
[//:/]
[/:] Gij … begin tropaar … [/:]
```

Gebruik geen kunstmatige dalende EHM op het eerste woord van de tropaar
(bijvoorbeeld `{\Gij}`): dat verandert de melodie.

Concrete fail + Fix: man-page [`vsa validate`](../reference/cli/validate.md).

## Severity-overrides

In [vsa.toml](@) kun je sommige **semantische** meldingen tijdelijk als
[severity](@) `warning` zetten. Syntaxfouten blijven altijd hard.

```toml
[validation.severity]
VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH = "warning"
```

```cmd
vsa validate bestand.vsa --config vsa.toml
```

## Zie ook

- [`vsa validate`](../reference/cli/validate.md) — synopsis, flags, fail-voorbeelden
- [Diagnostics-referentie](../reference/diagnostics.md)
- [Specificatie — validatie](../specification/validation.md)
- [Voorbeelden — fouten](../reference/voorbeelden/fouten.md)
