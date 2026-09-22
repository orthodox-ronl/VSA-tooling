# Traceerbaarheid

Deze tabel legt vast uit welke bestaande documenten de geconsolideerde specificatie is opgebouwd.

| Nieuw document  | Primaire bron(nen)                                                                                                                                                                                                                                                    | Opmerking                                                    |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `overview.md`   | `docs/spec/vsa-spec-v1.0.1.md`                                                                                                                                                                                                                                        | Inleiding en terminologie                                    |
| `syntax.md`     | `docs/spec/vsa-spec-v1.0.1.md`                                                                                                                                                                                                                                        | Kernsyntax, bloksyntax, [modifiers](@), pitchmarkers en EBNF |
| `semantics.md`  | `docs/spec/vsa-spec-v1.0.1.md`, `docs/spec/vsa-height-markers.md`                                                                                                                                                                                                     | Muzikale betekenis en hoogte-markerbeleid                    |
| `validation.md` | `docs/spec/vsa-spec-v1.0.1.md`, `docs/guides/validation.md`                                                                                                                                                                                                           | Syntax- en semantische fouten plus severity-overrides        |
| `directives.md` | `docs/spec-control-tokens.md`, `docs/spec/include-vsa.md`, `docs/spec/vsa-comments.md`, `docs/spec-vsa-document-samenstellen.md`                                                                                                                                      | Directives en documentcompositie                             |
| `rendering.md`  | `docs/spec/vsa-svg-rendering-spec.md`, `docs/spec/vsa-glyph-model.md`, `docs/spec/vsa-glyph-layout-rules.md`, `docs/spec/vsa-layout-algorithm.md`, `docs/spec/vsa-svg-dom-structure.md`, `docs/spec/vsa-rendering-config-model.md`, `docs/spec/vsa-height-markers.md` | SVG-, glyph-, layout- en configcontract                      |
| `cli.md`        | `docs/cli-reference.md` (nu `docs/reference/cli.md` / deze map)                                                                                                                                                                                                       | CLI-interfacecontract                                        |

## Niet opgenomen als normatief onderdeel

| Bron                                                                | Reden                                                                          |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `docs/specification-mvsa/`                                          | draft mvsa; nog niet normatief VSA 1.0; zie die map                            |
| `docs/plans/mvsa-v0-syntax.md`                                      | werkontwerp/geschiedenis mvsa; bij conflict wint `specification-mvsa/`         |
| `docs/plans/vsa-polyphony-proposal.md`                              | vervangen door mvsa; alleen doorverwijzing + open restpunten                   |
| `docs/spec/vsa-spec-v1.md` (historisch, zie `git show 9ff66f94^:…`) | oudere versie; vervangen door consolidatie in deze map                         |
| `docs/todo*.md`                                                     | open werk; hoort in proces/history, niet in normatieve specificatie            |
| `docs/architecture/parser-stap-*.md` / `docs/history/parser-steps/` | implementatiegeschiedenis                                                      |

## Controlepunt

Deze specificatiemap bevat geconsolideerde inhoud, maar vervangt `docs/` nog niet. In fase 3-review moet per document worden vastgesteld of de consolidatie volledig en juist is.
