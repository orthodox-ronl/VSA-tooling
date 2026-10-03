---
slug: toonhoogte-overgang
term: toonhoogte-overgang
termType: concept
glossaryTerm: Toonhoogte-overgang
glossaryText: "een [bracket-directive](@) van de vorm `[<oude-EHM>:<nieuwe-EHM>]` die een bewuste sprong in relatieve toonhoogte aangeeft zonder zichtbare output op het blad."
glossaryAlias: Pitch-transition
formPhrases:
  - toonhoogte-overgang
  - toonhoogte-overgangen
  - pitch-transition
  - pitch-transitions
  - pitch transition
  - pitch transitions
glossaryNotes:
  - "Org-term (discoverability): [bron/docs/terms/toonhoogte-overgang.md](https://github.com/orthodox-ronl/bron/blob/main/docs/terms/toonhoogte-overgang.md). Normatieve syntax/semantiek/rendering blijft hier in VSA-tooling."
  - "Onderscheid met [pitch-marker](@) / [hoogte-markering](@): markering eindigt op `:]`; overgang heeft niet-lege inhoud na de middelste `:` vóór `]`."
---

# Toonhoogte-overgang

Een toonhoogte-overgang / pitch-transition is een stil [bracket-token](@) dat
de relatieve toonhoogte-cursor van de ene [EHM](@) naar een andere zet,
zonder glyph of spatie in SVG/print.

Vorm: `[<oude-EHM>:<nieuwe-EHM>]` — bijvoorbeeld `[//:/]` (van `//` naar `/`)
of `[:/]` (van do naar `/`).

De linker-EHM moet overeenkomen met de berekende cursor ná het voorgaande
materiaal. Daarna staat de cursor op de rechter-EHM. Volgende
[hoogte-markeringen](@) controleren weer tegen die nieuwe cursor.

Dit is **geen** [pitch-marker](@): `[/:]` en `[//:]` blijven gewone
zichtbare markeringen.

## Motivatie

In één liturgie-notatie kunnen opeenvolgende stukken bewust op een andere
relatieve hoogte beginnen. Workarounds die de gezongen tekst verdraaien
(bijvoorbeeld een kunstmatige dalende EHM op het eerste woord) zijn
onaanvaardbaar. De toonhoogte-overgang lost de
`VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH` op zonder het blad te wijzigen.

## Gerelateerd / verder lezen

- [pitch-marker](@), [bracket-directive](@), [EHM](@), [laddergraad](@)
- Specificatie: [syntax](../specification/syntax.md),
  [semantics](../specification/semantics.md),
  [rendering](../specification/rendering.md)
- Handleiding: [Validatie](../guides/validation.md)
