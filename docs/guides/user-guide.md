# Gebruikershandleiding — tour

!!! note "Voor wie / wanneer"
    **Voor:** notatie-auteur of wie de CLI nog niet kent.
    **Wanneer:** je wilt weten *welke pagina* bij jouw taak hoort.
    **Niet:** volledige flags of foutcodes — die staan in de
    [CLI-referentie](../reference/cli/index.md).

**Antwoord in het kort:** kies je taak in de tabel hieronder; open die pagina;
flags alleen in de man-page.

## Wat doet de tool?

De VSA-tool helpt bij [VSA-notatie](@bron): controleren, als SVG tonen, en
Markdown/Hugo-sites bouwen ([hugo-output](@)).

```text
VSA-notatie  →  validate  →  SVG / MusicXML / Hugo-Markdown
```

## Welke taak → welke pagina?

| Ik wil …                                           | Ga naar                                                                      |
| -------------------------------------------------- | ---------------------------------------------------------------------------- |
| Lokaal installeren en eerste `OK`                  | [Starten](../getting-started/README.md)                                      |
| `.mvsa` leren typen (L, stemmen, octaven)          | [mvsa schrijven 101](mvsa-schrijven-101.md)                                  |
| Het juiste commando kiezen                         | [CLI-taken](cli-taken.md)                                                    |
| Begrijpen waarom validate faalt                    | [Validatie](validation.md) · [`vsa validate`](../reference/cli/validate.md)  |
| Eén bestand of site als SVG                        | [SVG exporteren](svg-export.md)                                              |
| MusicXML / Coria                                   | [MusicXML-export](musicxml-export.md)                                        |
| Hugo-consumer / waar hoort wat                     | [Consumer-site](../manuals/consumer-site.md)                                 |
| Tool in een andere repo of CI                      | [Integratie](../integratie/index.md)                                         |
| Formele taalregels                                 | [Specificaties](../specification/README.md)                                  |

## Klaar als …

| Doel                         | Check                                                                              |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| Omgeving OK                  | `vsa --version` toont een versie                                                   |
| Notatie OK                   | `vsa validate examples\docs-walkthroughs\svg-phrase-kort.vsa` → `OK`               |
| Eerste SVG                   | `vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa …` schrijft een `.svg`     |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
test
vsa validate examples\docs-walkthroughs\svg-phrase-kort.vsa
```

## Belangrijk onderscheid

| Commando                                         | Doet wél                         | Doet níet                                      |
| ------------------------------------------------ | -------------------------------- | ---------------------------------------------- |
| [`vsa validate`](../reference/cli/validate.md)   | Syntax + semantiek controleren   | SVG schrijven                                  |
| [`vsa svg`](../reference/cli/svg.md)             | Eén `.vsa` → SVG                 | Volledige semantische validatie (zie man-page) |

## Zie ook

- Hub: [Handleidingen](../manuals/index.md)
- Alle flags: [CLI-referentie](../reference/cli/index.md)
- Org-docs: [bron](https://orthodox-ronl.github.io/bron/)
