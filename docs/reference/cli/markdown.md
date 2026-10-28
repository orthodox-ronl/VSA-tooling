# `markdown` — producten uit Markdown (`.md`)

De **markdown**-straat leest Markdown (`.md` / `.markdown`) en maakt
pagina-producten: A4-PDF, SVG’s uit [VSA-blokken](@), en platte tekst.
CLI en repo-wrapper: `markdown` / `scripts\markdown.cmd`.

Er is **geen** `md`-commando of `md.cmd`: op Windows is `md` het
ingebouwde *makedir*.

Dit is **niet** de notatie-PDF uit `.mvsa` / `.mscz`
([`mvsa pdf`](mvsa.md#mvsa-pdf) / [`mscz pdf`](mscz.md)). Die volgt
checklist P* via MuseScore. `markdown pdf` is de **site-Markdown-PDF**
(browser/Chrome; print-CSS A4). Contract:
[contract-index — site-Markdown-PDF](../../formats/contract-index.md).

Er is geen `markdown validate`, `markdown kuiser` of `markdown normalize`.

## Synopsis

```text
markdown {pdf,svg,text} …
scripts\markdown.cmd {pdf,svg,text} …
```

## `markdown pdf`

Render één Markdownbestand (of een map met `.md`) naar A4-PDF: VSA-blokken
worden SVG, `:::include` wordt opgelost, pagebreaks worden paginaeinden,
`:::web-only:::` verdwijnt (print-only blijft).

```text
markdown pdf [-h] [--config CONFIG] [--content-root CONTENT_ROOT]
       [--bron-root BRON_ROOT] [--max-line-width MAX_LINE_WIDTH]
       [--chrome CHROME] [-o OUTPUT]
       path
```

| Naam                          | Verplicht | Betekenis                                                                 | Default                                                            |
| ----------------------------- | --------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `path`                        | Ja        | `.md`-bestand of map (recursief).                                         | —                                                                  |
| `-o`, `--output OUTPUT`       | Nee       | Pad van de PDF. Alleen bij precies één bronbestand.                       | Sibling `<bronnaam>.pdf` (bijv. `index.md.pdf`)                    |
| `--content-root CONTENT_ROOT` | Nee       | Root voor catalogus-includes (`lokaal/`).                                 | Eerste bovenliggende map met `lokaal/`, anders map van het bestand |
| `--bron-root BRON_ROOT`       | Nee       | Root van de bron-repo.                                                    | Auto (`vendor/bron` of `../bron`)                                  |
| `--config CONFIG`             | Nee       | Alternatief `vsa.toml`.                                                   | Auto-detectie                                                      |
| `--max-line-width N`          | Nee       | Maximale SVG-regelbreedte.                                                | Uit `vsa.toml`, anders `800`                                       |
| `--chrome CHROME`             | Nee       | Pad naar Edge, Chrome of Chromium.                                        | `CHROME_PATH` / auto-detectie                                      |

**Papierformaat:** A4 staand (210×297 mm) via print-CSS (`@page`), niet als
Chrome-flag. Zie [canonieke checklists — PDF P6](../../formats/canonical-checklists.md#checklist-pdf-afgeleide-van-mscz).

Vóór het renderen geldt dezelfde validatie als [`vsa validate`](validate.md)
op het Markdownbestand.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\markdown.cmd pdf examples\consumer-minimal\content-source\index.md
scripts\markdown.cmd pdf index.md -o index.md.pdf
```

Stdout bij succes: `PDF geschreven naar: <pad>`.

**Verouderd alias:** [`vsa pdf`](pdf.md) roept dezelfde keten aan en schrijft
een waarschuwing naar stderr. Gebruik voortaan `markdown pdf`.

## `markdown svg`

Schrijf SVG’s voor alle `:::vsa-notatie`-blokken in het Markdownbestand
(zelfde voorbereiding als [`vsa build-markdown`](build-markdown.md) /
[`vsa process`](process.md) voor één bestand).

```text
markdown svg [-h] [--config CONFIG] [--content-root CONTENT_ROOT]
       [--bron-root BRON_ROOT] [--max-line-width N] [-o DIR]
       path
```

| Naam                 | Verplicht | Betekenis                                | Default                      |
| -------------------- | --------- | ---------------------------------------- | ---------------------------- |
| `path`               | Ja        | `.md`-bestand of map.                    | —                            |
| `-o`, `--output DIR` | Nee       | Uitvoermap voor SVG’s (één bronbestand). | Sibling `<bronnaam>.assets/` |

```cmd
scripts\markdown.cmd svg liturgie.md
scripts\markdown.cmd svg liturgie.md -o generated\svg
```

## `markdown text`

Platte tekst uit het Markdownbestand: frontmatter weg, VSA-blokken via
dezelfde platte-tekstexport als [`vsa text`](text.md) op notatie, lichte
Markdown-opmaak (koppen, links, nadruk) weggehaald.

```text
markdown text [-h] [-o OUTPUT] path
```

| Naam                 | Verplicht | Betekenis                         | Default                  |
| -------------------- | --------- | --------------------------------- | ------------------------ |
| `path`               | Ja        | `.md`-bestand of map.             | —                        |
| `-o`, `--output OUT` | Nee       | Uitvoerbestand (één bronbestand). | Sibling `<bronnaam>.txt` |

```cmd
scripts\markdown.cmd text liturgie.md
```

Stdout: `Geschreven: <pad>`.

## Exit status

| Exitcode | Betekenis                                                                        |
| -------- | -------------------------------------------------------------------------------- |
| `0`      | Product(en) geschreven (of geen VSA-blokken bij `markdown svg`).                 |
| `1`      | Validatiefout, include-/directivefout, of geen browser (alleen `markdown pdf`).  |

## Zie ook

- [`vsa pdf`](pdf.md) — verouderd alias naar `markdown pdf`
- [`vsa build-markdown`](build-markdown.md) — hele site-Markdown + SVG-assets
- [`mvsa pdf`](mvsa.md#mvsa-pdf) / [`mscz pdf`](mscz.md) — partituur-PDF (P*)
- [CLI-overzicht](index.md) · [Straat-CLIs](../../plans/straat-clis.md)
