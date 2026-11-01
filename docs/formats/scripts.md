# Windows-scripts (de gereedschappen)

De gereedschappen van VSA-tooling zijn de `.cmd`-bestanden in de map
`scripts`. Je gebruikt ze in het Windows-opdrachtvenster (`cmd`).

Je hebt twee dingen nodig: de repository-map `VSA-tooling` op je pc, en
dat opdrachtvenster. Plak daarna één blok tegelijk.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
```

De map `scripts` staat op het zoekpad van deze repo. Daarom mag je
`mvsa validate examples\mvsa` schrijven. Hetzelfde commando met het
volledige script is `scripts\mvsa.cmd validate examples\mvsa`.

Elk script zet de Python-omgeving zelf klaar. Een aparte
installatiestap is niet nodig.

## Welk script bij welke bron

Kies het script bij het bestand dat je open hebt. Een `.mvsa` gaat niet
door `mscz`, en een `.mscz` niet door `mvsa`.

| Script     | Bronbestand          | Waarvoor                                                                     |
| ---------- | -------------------- | ---------------------------------------------------------------------------- |
| `mvsa`     | `.mvsa`              | Controleren, standaardproducten, losse export                                |
| `mxl`      | `.mxl` / `.musicxml` | Controleren, normaliseren, omzetten naar `.mvsa` of `.mscz`                  |
| `mscz`     | `.mscz`              | Controleren via import, standaardproducten, losse export                     |
| `markdown` | `.md`                | Pagina-PDF, SVG’s uit de pagina, platte tekst                                |
| `vsa`      | `.vsa`               | Controleren, SVG, standaardproducten, losse `pdf` (geen `scripts\vsa.cmd`)   |

`vsa` is het commando na installatie. Er is geen `scripts\vsa.cmd`.

Man-pagina’s: [`mvsa`](../reference/cli/mvsa.md),
[`mxl`](../reference/cli/mxl.md), [`mscz`](../reference/cli/mscz.md),
[`markdown`](../reference/cli/markdown.md),
[CLI-overzicht](../reference/cli/index.md).

### Voorbeeld: een `.mvsa` controleren

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa validate examples\mvsa
```

Bij succes eindigt het commando zonder fouttekst (exitcode 0). In `cmd`
controleer je dat met `echo %ERRORLEVEL%`.

### Standaardproducten

`mvsa products`, `mscz products` en `vsa products` maken de vaste set
naast de bron: MusicXML, Score-IR, partituur-`.mscz`, een mp3, de
gezongen tekst, een SVG, en een meta-bestand. Vlag `--skip-svg` slaat
de SVG over.

Die commando’s maken **geen** `.mvsa.pdf`, `.mscz.pdf` of `.vsa.pdf`.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa products examples\mvsa\1a-vredeslitanie.mvsa --skip-svg
```

## PDF: twee verschillende bestanden

**Pagina afdrukken of downloaden.** Het bestand heet `index.md.pdf` en
staat naast de Markdown van die pagina. Scherm en navigatie gebruiken
alleen dat bestand. Commando:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
markdown pdf examples\consumer-minimal\content-source\index.md
```

Zonder `-o` wordt de PDF `index.md.pdf` naast `index.md`.
In de bibliotheek heet het script `scripts\pdf.cmd`.

**Losse partituur-PDF van één lied.** Die heb je niet nodig voor de
site, voor download of voor de publicatiecontrole. De controle eist
`.vsa.pdf`, `.mvsa.pdf` en `.mscz.pdf` niet. Wil je zo’n PDF toch:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa pdf examples\minimal\valid-demo.vsa -o generated\demo.pdf
mvsa pdf examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.pdf
mscz pdf generated\alleluia.mscz -o generated\alleluia-uit-mscz.pdf
```

Elk commando leest alleen de eigen bronextensie. MuseScore 4 moet
geïnstalleerd zijn voor `vsa` / `mvsa` / `mscz pdf`.

## De repository bijhouden

Deze scripts zijn voor wie de tool of de documentatie nakijkt, niet voor
het bewerken van een lied.

| Script                   | Wanneer je het gebruikt                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `test`                   | De automatische tests draaien. Extra detail: `test -v`.                                                                                   |
| `check`                  | Tests plus het kleine voorbeeld `consumer-minimal` (zelfde controle als de bouw op GitHub).                                               |
| `serve`                  | De documentatie in de browser, zonder term-uitleg bij hover. Adres: `http://127.0.0.1:8000/`. Stoppen met Ctrl+C.                         |
| `serve-tev2`             | Dezelfde documentatie mét term-uitleg (hover). Eerst een keer `npm install` in deze map.                                                  |
| `build`                  | De documentatiesite bouwen zoals de publicatie dat doet.                                                                                  |
| `build --no-tev2`        | De documentatie bouwen zonder de term-pipeline.                                                                                           |
| `check-docs`             | Controle of documentatie en vaste voorbeeld-SVG’s nog kloppen.                                                                            |
| `clean`                  | Tijdelijke Python-mappen weg (cache, `build`, `dist`). Bronbestanden blijven staan.                                                       |
| `import`                 | Een zip uit je map Downloads uitpakken in de repo. Gebruik: `import bestandsnaam.zip`.                                                    |
| `run-example`            | Eén voorbeeld-`.vsa` door `vsa` halen. Gebruik: `run-example examples\minimal\001_plain_text.vsa`.                                        |
| `migrate-metadata`       | Op `.mvsa`-bestanden `@toon` zetten (en met `--tempo` ook `@tempo 130`). Eerst zonder `--apply`: dan zie je alleen wat er zou veranderen. |
| `install-rendering-deps` | Controleren of het lettertype voor SVG-tekenen aanwezig is.                                                                               |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
check
```

## Oude namen

Deze scripts bestaan nog. Ze schrijven één regel welke naam je nu
gebruikt, en starten daarna het nieuwe script.

| Oude naam         | Gebruik nu                                                      |
| ----------------- | --------------------------------------------------------------- |
| `ci`              | `check`                                                         |
| `docs-serve`      | `serve`                                                         |
| `docs-serve-tev2` | `serve-tev2`                                                    |
| `docs-build`      | `build --no-tev2`                                               |
| `docs-build-tev2` | `build`                                                         |
| `test-verbose`    | `test -v`                                                       |
| `bootstrap`       | niets apart; de scripts hierboven zetten de omgeving zelf klaar |

Er is geen `vsa-products.cmd`, `serve-hugo.cmd` of `retry.cmd` in deze
repo. Standaardproducten: `vsa products` (of `mvsa products` /
`mscz products`).

Python-bestanden in `scripts\` (bijvoorbeeld
`align_markdown_tables.py`) zijn hulpen voor onderhoud, geen
commando’s die je als beheerder nodig hebt.

## Zie ook

- [CLI-taken](../guides/cli-taken.md) — welk commando bij welke taak
- [Starten](../getting-started/README.md) — eerste `vsa validate`
- Zelfde lijst naast de scripts: `scripts/README.md` in de repo
