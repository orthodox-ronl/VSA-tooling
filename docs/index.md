# VSA-tooling — documentatie

Welkom bij de documentatie van de **VSA-toolchain**: [parser](@), validatie,
SVG- en MusicXML-export, Markdown-build en hergebruik in andere repositories.

Deze site is voor **wie de tool gebruikt of documenteert** — niet voor het koor
dat een dienst oefent. Daarvoor: de parochie-site
([VSA-demo](https://github.com/orthodox-ronl/VSA-demo) als voorbeeld).

## Wie ben je? (kies je route)

| Ik wil …                                               | Voor wie                    | Start hier                                                                                 |
| ------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------ |
| [VSA](@) schrijven / valideren / SVG maken             | Notatie-auteur              | [Starten](getting-started/README.md) · [Validatie](guides/validation.md)                   |
| Hugo/CI aan `vsa-tool` hangen                          | Consumer-site builder       | [Consumer-site](manuals/consumer-site.md) · [Integratie](integratie/index.md)              |
| Docs of TEv2 bijdragen                                 | Docs-/tool-contributor      | [TEv2 in tool-docs](guides/tev2-docs.md)                                                   |
| Formele taal-/toolregels                               | Spec-/PR-reviewer           | [Specificaties](specification/README.md) · [Terminologie](glossary.md)                     |
| [Zangstuk](@bron) / `access:` in de [bron-repo](@bron) | Bron-contentbeheerder       | [bron — handleidingen](https://orthodox-ronl.github.io/bron/manuals/)                 |
| Partituur oefenen / liturgie volgen                    | Koor / liturgie             | **Niet hier** — parochie-site / [VSA-demo](https://github.com/orthodox-ronl/VSA-demo) |

Rollen en toon: [bron — schrijfconventies](https://orthodox-ronl.github.io/bron/specs/schrijfconventies/).

## Wat vind je hier

| Sectie                                              | Wat je er vindt                                                                                         |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| [Starten](getting-started/README.md)                | Lokaal ontwikkelen: omgeving, `vsa --version`, valideren en een SVG maken.                              |
| [Formaten & CLI](formats/index.md)                  | `.vsa` / `.mvsa` / `.mxl` / `.mscz` / `.midi`, checklists, CLI en `.cmd`-scripts.           |
| [Handleidingen](manuals/index.md)                   | Taakgerichte uitleg (CLI-taken, validatie, export, consumer-site).                                      |
| [Specificaties](specification/README.md)            | Normatieve VSA-taal- en toolcontracts.                                                                  |
| [Referentie](reference/README.md)                   | Naslag: voorbeelden, CLI man-pagina’s, tokens, [diagnostics](@) en outputs.                             |
| [Integratie](integratie/index.md)                   | `vsa-tool` importeren in andere repo’s en CI; TEv2 in tool-docs.                                        |
| [Terminologie](glossary.md)                         | Gegenereerde glossary van tool-termen (+ geselecteerde bron-termen).                                    |
| [Plannen](plans/README.md)                          | Ontwikkelplannen. Die zijn niet normatief; bij twijfel gelden specificatie en handleidingen.            |

## Waar hoort wat?

| Vraag                                                      | Ga naar                                                                                      |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Hoe gebruik ik de VSA-CLI of bouw ik een consumer-site?    | [Starten](getting-started/README.md) of [Handleidingen](manuals/index.md)                    |
| Welk formaat / welk `mvsa`/`mxl`/`mscz`-commando?          | [Formaten & CLI](formats/index.md)                                                           |
| Wat moet de taal/tool formeel doen?                        | [Specificaties](specification/README.md)                                                     |
| Org-specs, [zangstuk](@bron)-formaat, glossary             | [bron — documentatie](https://orthodox-ronl.github.io/bron/)                            |

## Wat is dit *niet*

| Repo / site                                                | Rol                                                                |
| ---------------------------------------------------------- | ------------------------------------------------------------------ |
| [bron](https://orthodox-ronl.github.io/bron/)         | Org-specs en [zangstukken](@bron) (single source of truth)         |
| [VSA-demo](https://orthodox-ronl.github.io/VSA-demo/) | Hugo-presentatiesite / voorbeeldconsumer                           |
| **Deze site**                                              | Documentatie van de **tool**, geen liturgische browsable catalogus |

> **URL-cutover:** docs staan op `/` (`main`) en `/preview/` (andere branches).
> Oude paden `/docs/` en `/docs-preview/` zijn vervangen.

## Lokaal bekijken

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python -m pip install -r requirements-docs.txt
serve
```

Met TermRefs (na `npm install`): `serve-tev2` — zie
[TEv2 in tool-docs](guides/tev2-docs.md).

## Snel naar de tool

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
test
vsa --version
vsa validate examples\minimal\001_plain_text.vsa
```
