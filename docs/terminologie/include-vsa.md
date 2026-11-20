---
slug: include-vsa
term: include-vsa
termType: concept
glossaryTerm: "@include-vsa"
glossaryText: "een string die met `@include-vsa` begint, precies één ondersteunde resolverparameter bevat (`id=` of `lokaal=`) en tijdens verwerking door de body van het doelbestand wordt vervangen."
glossaryAlias: VSA-inline-include
formPhrases:
  - "@include-vsa"
  - "@include-vsa-directives"
  - vsa-inline-include
  - vsa-inline-includes
glossaryNotes:
  - "Voorbeeld: `refrein: @include-vsa lokaal=cherubijnenhymne/kastorski/groningen/groningen-vsa` — alleen de `@include-vsa …`-substring wordt vervangen."
---

# @include-vsa

`@include-vsa` / [vsa-inline-include](@) vervangt alleen de directive-substring
door [VSA](@)-bronmateriaal tijdens verwerking. Omringende tekst in dezelfde
regel blijft bestaan.

Voorbeeld:

```text
refrein: @include-vsa lokaal=cherubijnenhymne/kastorski/groningen/groningen-vsa
```

Goede/valide voorbeelden van @include-vsa zijn:
- Exact één van `id=` / `lokaal=`
- Alleen de directive-substring wordt vervangen

Geen goede/niet valide voorbeelden van @include-vsa zijn:
- Meerdere resolverparameters tegelijk
- Hele regel of heel [VSA-blok](@) wissen

## Motivatie

Zo kun je herbruikbare [VSA](@)-fragmenten (refreinen, gedeelde regels) één keer
onderhouden en op meerdere plaatsen includen, zonder de omringende regeltekst
te verliezen.

## Gerelateerd / verder lezen

- Referentie: [include-vsa](../reference/include-vsa.md)
- Org: [representatie](@bron), [samenstelling](@bron) — context waarin includes
  in publicatieketens voorkomen
