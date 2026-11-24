# VSA-tooling

VSA-tooling is de gereedschapskist voor het schrijven, controleren, renderen en
publiceren van VSA-notatie.

De repository bevat de Python CLI (`vsa`) en documentatie (MkDocs Material).
Een voorbeeld-Hugo-consumer staat in
[VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

## Waarvoor is deze repo?

| Workflow                   | Doel                                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| VSA-notatie                | VSA-bronnen valideren, parsen en renderen naar SVG of MusicXML/MXL.                                                         |
| Markdown-build             | Markdown met `::: vsa-notatie`, `:::include`, `:::coria` en print/web-directives omzetten naar publiceerbare content.       |
| Parochie- en bronmateriaal | Lokale en bron-zangstukken via logische verwijzingen opnemen in samenstellingen, via `id:`- en `lokaal:`-verwijzingen.      |

## Huidige status

De kern is werkend en behoorlijk gedekt door regressietests. De belangrijkste
functies zijn aanwezig:

- VSA valideren: `vsa validate`
- VSA naar SVG renderen: `vsa svg`
- VSA naar MusicXML/MXL exporteren: `vsa musicxml`
- VSA-blokken in Markdown inspecteren: `vsa blocks`
- Markdown verwerken naar SVG-assets: `vsa process`
- Markdown bouwen: `vsa build-markdown`

De projectrichting en actuele open punten staan in
[docs/status-en-roadmap.md](docs/status-en-roadmap.md).

## Commando's

Org-conventie: [repo-scripts](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/repo-scripts.md). Python **3.14**.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
test
serve
```

| Commando               | Doel                        |
| ---------------------- | --------------------------- |
| `test`                 | pytest                      |
| `check`                | CI-spiegel                  |
| `serve` / `serve-tev2` | MkDocs preview              |
| `build`                | TEv2 + MkDocs (CI-pariteit) |

```cmd
vsa --version
vsa validate examples\minimal\001_plain_text.vsa
```

Docs: `serve`. Voorbeeldconsumer: repo VSA-demo, commando's `check` / `serve`.

## Belangrijke mappen

| Pad                          | Inhoud                                                                       |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `src/vsa/`                   | Python package met parser, validators, renderers, markdownverwerking en CLI. |
| `tests/`                     | Unit- en regressietests voor parser, validatie, rendering en workflows.      |
| `examples/minimal/`          | Kleine VSA-voorbeelden voor testen en uitleg.                                |
| `examples/regression/`       | Vastgelegde input/output-cases voor regressies.                              |
| `examples/consumer-minimal/` | Minimale Markdown/VSA-fixture voor CI-smoke.                                 |
| `docs/`                      | Gebruikersdocs, specs, plannen (MkDocs-bron).                                |
| `scripts/`                   | Windows-commando's (`test`, `check`, `serve`, `build`).                      |

## Documentatie

Gepubliceerde docs (MkDocs Material):

| Omgeving                  | URL                                                       |
| ------------------------- | --------------------------------------------------------- |
| Productie (`main`)        | https://orthodox-ronl.github.io/VSA-tooling/              |
| Preview (andere branches) | https://orthodox-ronl.github.io/VSA-tooling/preview/      |

Lokaal:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
serve
```

| Document                                                                                                | Gebruik                                          |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| [docs/guides/user-guide.md](docs/guides/user-guide.md)                                                  | Taakgerichte uitleg voor gebruikers van de tool. |
| [docs/reference/cli.md](docs/reference/cli.md) / [docs/specification/cli.md](docs/specification/cli.md) | CLI-naslag en CLI-contract.                      |
| [docs/guides/reuse-vsa-tooling.md](docs/guides/reuse-vsa-tooling.md)                                    | Extern hergebruik van `vsa-tool` en workflows.   |
| [docs/guides/parochie-lokaal-vsa.md](docs/guides/parochie-lokaal-vsa.md)                                | Parochie-lokaal materiaal en catalogus-includes. |
| [docs/status-en-roadmap.md](docs/status-en-roadmap.md)                                                  | Projectstatus en roadmap.                        |
| [docs/specification/](docs/specification/)                                                              | Normatieve VSA-specificatie.                     |
| [docs/plans/](docs/plans/)                                                                              | Plannen en toekomstvoorstellen.                  |
| [docs/history/](docs/history/)                                                                          | Ontwerpgeschiedenis.                             |

Zie [docs/reference/cli.md](docs/reference/cli.md) voor CLI-details.

## Ontwikkelen

Draai tijdens ontwikkeling:

```cmd
scripts\test.cmd
```

Draai voor een bredere lokale controle:

```cmd
scripts\ci.cmd
```

De repo bevat veel historische stapdocumenten. Die blijven nuttig als achtergrond, maar de actuele status hoort in [docs/status-en-roadmap.md](docs/status-en-roadmap.md).
