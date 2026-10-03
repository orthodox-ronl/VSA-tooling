# Diagnostiek-referentie

## Foutoutput

De standaardvorm is:

```text
bron:regel:kolom: FOUTCODE: uitleg
```

Voorbeeld:

```text
examples\demo.md:blok-1:1:1: VSA-SYNTAX-EMPTY-SCOPE: Scope zonder zangelement.
```

## Exitcodes

| Exitcode | Betekenis                         |
| -------- | --------------------------------- |
| `0`      | Geen blokkerende fouten           |
| `1`      | Fout gevonden of commando mislukt |

## Veelvoorkomende foutcodes

| Foutcode                                   | Betekenis                                           | Herstelactie                                              |
| ------------------------------------------ | --------------------------------------------------- | --------------------------------------------------------- |
| `VSA-SYNTAX-EMPTY-SCOPE`                   | `{}` gevonden                                       | Zet tekst of [zangelement](@) in de [scope](@)            |
| `VSA-SYNTAX-UNCLOSED-SCOPE`                | `{tekst` zonder `}`                                 | Sluit de [scope](@) af                                    |
| `VSA-SYNTAX-UNEXPECTED-CLOSE-BRACE`        | Losse `}`                                           | Verwijder of herstel de [scope](@)                        |
| `VSA-SYNTAX-WHITESPACE-IN-SCOPE`           | Spatie binnen `{...}`                               | Splits tekst buiten de scope                              |
| `VSA-SYNTAX-UNCLOSED-PITCH-MARKER`         | `[` zonder `]`                                      | Sluit [pitch-marker](@) af                                |
| `VSA-SYNTAX-PITCH-MARKER-MISSING-COLON`    | Pitch-marker zonder `:`                             | Gebruik bijvoorbeeld `[:]`                                |
| `VSA-SYNTAX-INVALID-PITCH-TRANSITION`      | Ongeldige `[oud:nieuw]`-vorm                        | Gebruik geldige EHM aan beide zijden                      |
| `VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH`     | Hoogte- en lengteposities passen niet bij elkaar    | Controleer samengestelde [modifiers](@)                   |
| `VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH`      | Lokale markering wijkt af van berekende cursor      | Markering of scopes aanpassen                             |
| `VSA-SEMANTIC-PITCH-TRANSITION-MISMATCH`   | Linker-EHM van toonhoogte-overgang klopt niet       | Pas `[oud:nieuw]` of voorgaande notatie aan               |

## Severity

| Severity  | Effect                                    |
| --------- | ----------------------------------------- |
| `error`   | Verwerking faalt; exitcode meestal `1`    |
| `warning` | Melding tonen; verwerking mag doorgaan    |

## Obsolete pitchmarker-foutcodes

| Foutcode                                      | Status    | Opmerking                                      |
| --------------------------------------------- | --------- | ---------------------------------------------- |
| `VSA-SEMANTIC-MISSING-FINAL-PITCH-MARKER`     | Obsolete  | Ontbrekende eindmarkering is toegestaan        |
| `VSA-SEMANTIC-EMPTY-FINAL-PITCH-MARKER`       | Obsolete  | `[:]` is geldig als neutrale hoogte            |
