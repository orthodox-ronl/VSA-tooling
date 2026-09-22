# Overzicht

Deze map bevat de geconsolideerde **normatieve specificatie** van [VSA](@)
versie 1.0.

[VSA](@) ([Vereenvoudigde Slavische Accentnotatie](vsa@)) is een tekstgebaseerde
domeinspecifieke taal voor Slavische accentnotatie. De specificatie beschrijft
wat de [VSA-notatie](@bron) en de [vsa-toolset](@) moeten betekenen.
Architectuurkeuzes, implementatiegeschiedenis en gebruikershandleidingen staan
buiten deze map.

## Documenten

| Document                            | Wat je er leest                                                                                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Doel en scope](overview.md)        | Doel, scope, terminologie en status.                                                                                                                 |
| [Syntax](syntax.md)                 | [VSA-notatie](@bron)-syntax, [VSA-blokken](@), [modifiers](@) ([EHM](@)/[ELM](@)), [pitch-markers](@) / [hoogte-markeringen](@) en EBNF.             |
| [Semantiek](semantics.md)           | Muzikale betekenis van [scopes](@), [modifiers](@), [muzikale posities](@) en [do-context](@) / [tooncontext](@).                                    |
| [Validatie](validation.md)          | Validatieregels, [diagnostics](@) / [diagnostische meldingen](@) en [severity](@) / [ernstniveau](@).                                                |
| [Directives](directives.md)         | [Control-tokens](@), [bracket-directives](@) / [bracket-tokens](@), comments, [vsa-inline-include](@) en document-samenstelling.                     |
| [Rendering](rendering.md)           | SVG via de [renderer](@), [glyphmodel](@) / [glyphs](@), layout, [projectconfiguratie](@) en export.                                                 |
| [CLI](cli.md)                       | CLI-contract voor gebruikers- en buildcommando’s.                                                                                                    |
| [Conformance](conformance.md)       | Criteria voor [parser](@), [validator](@), [renderer](@) en CLI.                                                                                     |
| [Error-handling](error-handling.md) | Foutafhandeling en [diagnostics](@) / [diagnostische meldingen](@).                                                                                  |
| [Voorbeelden](examples.md)          | Normatieve voorbeelden bij de specificatie.                                                                                                          |
| [Versioning](versioning.md)         | Versiebeleid van de specificatie.                                                                                                                    |
| [Traceability](traceability.md)     | Herkomst van de geconsolideerde onderdelen.                                                                                                          |
| [Open punten](open-points.md)       | Bekende open specificatievragen.                                                                                                                     |

Draft meerstemmige invoer (nog niet VSA 1.0):
[`docs/specification-mvsa/`](../specification-mvsa/README.md).
