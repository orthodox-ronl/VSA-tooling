# Overzicht

Taakgerichte documentatie voor werken met de [VSA-tooling](@bron). Dit is het
**enige** startpunt voor handleidingen. Normatieve regels:
[Specificaties](../specification/README.md); snelle naslag:
[Referentie](../reference/README.md).

!!! note "Voor wie"
    Vooral notatie-auteurs en consumer-site builders. Koor / liturgie: niet
    hier — zie [Home](../index.md).

## Leespad

| Stap | Pagina                                                | Wanneer                                                          |
| ---- | ----------------------------------------------------- | ---------------------------------------------------------------- |
| 1    | [Starten](../getting-started/README.md)               | Omgeving en eerste `vsa`-commando’s                              |
| 2    | [mvsa schrijven 101](../guides/mvsa-schrijven-101.md) | `.mvsa` typen: L, stemmen, `@`-woorden, octaven                  |
| 3    | [Gebruikershandleiding](../guides/user-guide.md)      | Tour: welke taak → welke pagina                                  |
| 4    | [CLI-taken](../guides/cli-taken.md)                   | Commando kiezen zonder flags te lezen                            |
| 5    | [Validatie](../guides/validation.md)                  | [Diagnostische meldingen](@) en [severity](@) / [ernstniveau](@) |
| 6    | [SVG exporteren](../guides/svg-export.md)             | [VSA-notatie](@bron) als afbeelding / Hugo                       |
| 7    | [Integratie](../integratie/index.md)                  | Gebruik in andere repo’s / CI                                    |

## Overige handleidingen

| Pagina                                                              | Wat je er vindt                                      |
| ------------------------------------------------------------------- | ---------------------------------------------------- |
| [mvsa schrijven 101](../guides/mvsa-schrijven-101.md)               | Tutorial: L/stemmen, notatie, octaven, taken.        |
| [MusicXML-export](../guides/musicxml-export.md)                     | Export naar MusicXML / Coria.                        |
| [Rendering en fonts](../guides/rendering-fonts.md)                  | Fonts en SVG-metrics.                                |
| [Parochie-lokaal VSA](../guides/parochie-lokaal-vsa.md)             | Catalogus-includes (tool-kant).                      |
| [Testen en regressie](../guides/testing-and-regression.md)          | [Fixture](@)-mappen en pytest.                       |
| [Liturgikon-notatie](../guides/liturgikon-notatie.md)               | Historische neumenschrift-uitleg.                    |
| [Consumer-site — waar hoort wat](consumer-site.md)                  | Ownership + keten; presentatie = VSA-demo.           |
| [TEv2 in tool-docs](../guides/tev2-docs.md)                         | Glossary-pipeline en TermRefs.                       |
| [Navigatie-placeholders](../guides/hugo-navigation-placeholders.md) | `VSA-NAV`-markers (toolgedrag).                      |

Flags en foutcodes: [CLI-referentie](../reference/cli/index.md).

Organisatie-specs (terminologie, [zangstuk](@bron)-formaat):
[bron — documentatie](https://orthodox-ronl.github.io/bron/).
