# Validatie

Dit document beschrijft de normatieve validatieregels en het severity-model.

## Validatie en fouten

### Verwerkingspipeline

Een implementatie verwerkt een VSA-zangstuk bij voorkeur in deze volgorde:

```text
tekst
  ↓
lexen/parsen
  ↓
Abstract Syntax Tree (AST)
  ↓
syntactische validatie
  ↓
semantische validatie
  ↓
rendering of export
```

Een [renderer](@) of exporteur mag uitsluitend werken op een [zangstuk](@bron) dat syntactisch en semantisch geldig is.

### Syntactische fouten

Een syntactische fout treedt op wanneer de invoer niet voldoet aan de grammatica.
Hier is een aantal voorbeelden:

| Voorbeeld    | Fout                                         |
| ------------ | -------------------------------------------- |
| `{tekst`     | ontbrekende afsluitende accolade             |
| `{tekst&&_}` | ongeldige modifier-syntax                    |
| `{tekst _}`  | whitespace binnen een [zangelement-scope](@) |
| `{te/tekst}` | modifierteken `/` binnen [zangelement](@)    |
| `{}`         | ontbrekend [zangelement](@)                  |

Syntactische fouten worden gedetecteerd vóór semantische validatie.

### Semantische fouten

Een semantische fout treedt op wanneer de invoer syntactisch geldig is,
maar niet voldoet aan de betekenisregels van [VSA](@).
Het voorbeeld met `{+\neer}` gaat uit van een [do-context](@)
met parameters `do="C4"` en `mode="major"`.

| Voorbeeld              | Fout                                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `{/&\tekst_}`          | [hoogte-modifier](@) bevat twee posities; [lengte-modifier](@) bevat één positie                          |
| `[//:] tekst [/:]`     | eindmarkering komt niet overeen met berekende eindgraad, indien eindcontrole actief is                    |
| `[:] {+\neer} [:]`     | hoogte-markering mismatch: cursor staat op ti (graad −1), markering declareert do; accidens telt niet mee |

Halftoon-prefixen (`#`/`+`/`b`) zijn tijdelijke accidentals op de aankomsttoon.
Zij bewegen de diatonische cursor niet; marker-controle vergelijkt alleen
laddergraden. Zie [Interpretatie van EHMs](semantics.md#interpretatie-van-ehms).
Een verouderde schrijfwijze zoals `{-\tekst}` is geen geldige [EHM](@) (syntaxfout).

---


## Severity-overrides

Onderstaande regels komen uit de bestaande configuratiedocumentatie en horen bij het validatiecontract.

# VSA configuratie: severity-overrides

Deze pagina vult de gebruikershandleiding aan.

## Waarvoor gebruik je dit?

Gebruik severity-overrides als je sommige semantische aandachtspunten tijdelijk als waarschuwing wilt behandelen.

Standaard blijft semantiek hard:

```text
semantic diagnostic = error
```

Met config kun je specifieke foutcodes zachter maken:

```text
semantic diagnostic = warning
```

## Voorbeeld `vsa.toml`

```toml
[validation.severity]
VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH = "warning"
```

## Geldige severity-waarden

| Waarde    | Betekenis                                   |
| --------- | ------------------------------------------- |
| `error`   | validatie faalt                             |
| `warning` | melding tonen, maar verwerking mag doorgaan |

## Welke commando's gebruiken dit?

| Commando                                                       | Werkt met severity-config?        |
| -------------------------------------------------------------- | --------------------------------- |
| [`vsa validate`](../reference/cli/validate.md)                 | ja                                |
| [`vsa process`](../reference/cli/process.md)                   | ja                                |
| [`vsa build-markdown`](../reference/cli/build-markdown.md)     | ja                                |
| [`vsa svg`](../reference/cli/svg.md)                           | nee, parseert/render rechtstreeks |
| [`vsa blocks`](../reference/cli/blocks.md)                     | nee, inspecteert blokken          |
| [`vsa parse`](../reference/cli/parse.md)                       | nee, toont parseroutput           |

## Validate

```cmd
vsa validate bestand.vsa --config vsa.toml
```

Bij alleen warnings:

```text
WARNING: VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH
```

De exitcode is dan `0`.

Bij errors blijft de exitcode `1`.

## Process

```cmd
vsa process input.md generated\vsa --config vsa.toml
```

Bij alleen warnings worden SVG-bestanden gegenereerd.

## Build-markdown

```cmd
vsa build-markdown content generated\content static\vsa --config vsa.toml
```

Bij alleen warnings worden Markdown en SVG-bestanden gegenereerd.

## Wat blijft altijd hard?

Syntax-errors blijven altijd `error`.

Dat betekent:

```text
{onafgesloten
```

blijft validatie en generatie stoppen.

## Praktisch advies

Gebruik warnings tijdelijk bij migratie of experimenten.

Gebruik errors voor CI, demo-sites en [publicatie](@) wanneer de notatie stabiel moet zijn.


## Verouderde pitchmarker-foutcodes

De oude foutcodes `VSA-SEMANTIC-MISSING-FINAL-PITCH-MARKER` en `VSA-SEMANTIC-EMPTY-FINAL-PITCH-MARKER` zijn obsolete.

Een ontbrekende eindmarkering is toegestaan. Een eindmarkering `[:]` is geldig en betekent neutrale hoogte, equivalent aan `[-:]` c.q. `[~:]`.
