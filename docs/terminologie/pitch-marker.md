---
slug: pitch-marker
term: pitch-marker
termType: concept
glossaryTerm: Pitch-marker
glossaryText: "een [bracket-directive](@) / [bracket-token](@) met de vorm `[<EHM>:]`, waarbij `<EHM>` leeg is of een geldige [EHM](@) bevat."
glossaryAlias: Hoogte-markering
formPhrases:
  - pitch-marker
  - pitch-markers
  - hoogte-markering
  - hoogte-markeringen
  - toonhoogte-markering
  - toonhoogte-markeringen
  - hoogtemarker
  - hoogtemarkers
glossaryNotes:
  - "Voorbeeld: `[:]` of `[/:]` vóór of na zangtekst; zonder afsluitende `:` is het geen pitch-marker."
  - "Onderscheid met [toonhoogte-overgang](@): `[//:/]` is geen pitch-marker (niet-lege inhoud na de middelste `:`)."
---

# Pitch-marker

Een pitch-marker / [hoogte-markering](@) geeft in [VSA](@) een relatieve
toonhoogte of toonpositie aan. Vorm: `[<EHM>:]` — bijvoorbeeld `[:]` of `[/:]`.

De [parser](@) bewaart pitch-markers als positionele tokens in de volgorde van
de bron; een [bracket-directive](@) zonder afsluitende dubbele punt valt niet
onder dit begrip. Een [toonhoogte-overgang](@) `[<EHM>:<EHM>]` is een ander
token: die eindigt niet op `:]` en wordt niet als pitch-marker gerenderd.

Goede/valide voorbeelden van Pitch-marker zijn:
- `[:]` of `[/:]` (afgesloten met `:`)
- Lege of geldige [EHM](@) vóór de `:`

Geen goede/niet valide voorbeelden van Pitch-marker zijn:
- `[/]` zonder `:` ([control-token](@) of andere)
- `[//:/]` ([toonhoogte-overgang](@), geen markering)
- Ongeldige [EHM](@)-vorm binnen de brackets

## Motivatie

Zonder expliciete markering is relatieve toonhoogte in platte tekst niet
machineleesbaar. Pitch-markers maken hoogte-afspraken in de notatie toetsbaar
(validatie) en renderbaar (SVG).

## Gerelateerd / verder lezen

- [hoogte-modifier](@), [bracket-directive](@), [vsa-scope](@), [EHM](@),
  [toonhoogte-overgang](@)
- Specificatie: [syntax](../specification/syntax.md) (bracket-/hoogte-secties)
