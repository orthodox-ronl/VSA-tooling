# Overzicht

`vsa` is de commandoregel-tool van de [vsa-toolset](@). Ermee controleer je
[geldige VSA-notatie](@), bekijk je de interne [parser](@)-structuur, en
genereer je SVG, Hugo-Markdown en MusicXML uit [vsa-bestanden](@bron) en Markdown.

Deze pagina geeft het overzicht. Elk subcommando heeft een eigen man-pagina
met de volledige argumentenlijst, voorbeelden en foutgevallen.

## Werkmap-conventie

Alle voorbeelden in deze referentie gaan uit van Windows `cmd.exe` en de
repository-root als werkmap:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
```

Paden in commando's zijn relatief aan die map, tenzij je een absoluut pad
opgeeft.

## Algemene syntax

```text
vsa [--config CONFIG] [--version] <subcommando> …
```

`vsa` zonder subcommando en zonder `--version` toont een foutmelding
(`Geen commando opgegeven.`) en stopt met exitcode `1`.

## Globale opties

| Optie             | Verplicht | Betekenis                                                                                                                               |
| ----------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `--config CONFIG` | Nee       | Pad naar een alternatief [vsa.toml](@). Zonder deze optie zoekt elk commando zelf naar [vsa.toml](@) (zie [`config.md`](../config.md)). |
| `--version`       | Nee       | Toon de geïnstalleerde versie en stop direct (subcommando wordt genegeerd).                                                             |
| `-h`, `--help`    | Nee       | Toon hulp. Werkt zowel op `vsa --help` als op `vsa <subcommando> --help`.                                                               |

Sommige subcommando's (`svg`, `process`, `build-markdown`, `musicxml`, `pdf`)
accepteren `--config` ook als **subcommando-optie**. Die overschrijft dan de
globale `--config`.

## Exitcodes

| Exitcode | Betekenis                           |
| -------- | ----------------------------------- |
| `0`      | Commando succesvol                  |
| `1`      | Fout gevonden of commando mislukt   |

Controleer in `cmd.exe` de laatste exitcode direct na een commando:

```cmd
echo %ERRORLEVEL%
```

## Subcommando's

| Subcommando                                      | Doel                                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| [`validate`](validate.md)                        | Controleer op [geldige VSA-notatie](@) (`.vsa`, `.md`, of een map).                        |
| [`parse`](parse.md)                              | Toon parseroutput of de interne [ast](@) van één [vsa-bestand](@bron).                     |
| [`blocks`](blocks.md)                            | Vind en inspecteer [VSA-blokken](@) in een Markdownbestand.                                |
| [`svg`](svg.md)                                  | Render één [vsa-bestand](@bron) naar één SVG-bestand.                                      |
| [`process`](process.md)                          | Genereer SVG-bestanden uit [VSA-blokken](@) in Markdown (zonder Markdown te herschrijven). |
| [`build-markdown`](build-markdown.md)            | Genereer Hugo-geschikte Markdown én SVG-assets uit content-source.                         |
| [`pdf`](pdf.md)                                  | Render één Markdownbestand (VSA, includes, pagebreaks) naar A4-PDF.                        |
| [`resolve-catalogus`](resolve-catalogus.md)      | Los `:::include … zoek="…"` op naar catalogus-paden (`bron:…` / `lokaal:…`).               |
| [`syllabify`](syllabify.md)                      | Lettergreepstreepjes in ongescoopte VSA-tekst (bestand/map; Pyphen nl_NL).                 |
| [`musicxml`](musicxml.md)                        | Exporteer [VSA](@) naar MusicXML (`.mxl` of `.musicxml`).                                  |

Elke pagina hierboven beschrijft de volledige syntax, alle argumenten en
opties (inclusief defaults), voorbeeldoutput, en typische foutgevallen. Deze
overzichtspagina herhaalt die details niet.

## Scripts

De onderstaande scripts gebruik je rond `vsa` zelf (installatie, testen,
docs). Zie [`scripts/README.md`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/scripts/README.md)
voor het volledige overzicht.

| Script                    | Doel                                                       |
| ------------------------- | ---------------------------------------------------------- |
| `test`                    | Installeert de lokale omgeving (`.venv`, `vsa`, pytest).   |
| `scripts\test.cmd`        | Draait de pytest-suite.                                    |
| `scripts\ci.cmd`          | Draait de volledige lokale CI (pytest + consumer-minimal). |
| `serve`                   | Serveert deze MkDocs-documentatie lokaal.                  |

## Diagnosevolgorde

Bij problemen: eerst [`vsa validate`](validate.md), daarna `scripts\test.cmd`, eventueel
[`vsa blocks`](blocks.md) `… --json`. Volledige uitleg:
[specification/cli.md](../../specification/cli.md#diagnosevolgorde).

## Verwante documentatie

- Taakgerichte uitleg per doel: [CLI-taken](../../guides/cli-taken.md)
- Gebruikershandleiding (tour + links): [gebruikershandleiding](../../guides/user-guide.md)
- Functioneel contract (normatief, alle commando's): [specification/cli.md](../../specification/cli.md)
- [vsa.toml](@)-instellingen en voorrangsregels: [config.md](../config.md)
- Foutcodes en [severity](@): [diagnostics.md](../diagnostics.md)
- SVG-workflow: [svg-export.md](../../guides/svg-export.md)
- MusicXML-workflow: [musicxml-export.md](../../guides/musicxml-export.md)
- Parochie-lokale [VSA](@) (catalogus, includes): [parochie-lokaal-vsa.md](../../guides/parochie-lokaal-vsa.md)
- Bron-contracten (org-breed, normatief): [conversie-vsa-svg](https://orthodox-ronl.github.io/bron/reference/conversie-vsa-svg/),
  [exporttype-svg](https://orthodox-ronl.github.io/bron/reference/exporttype-svg/),
  [catalogus-cli](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/)
