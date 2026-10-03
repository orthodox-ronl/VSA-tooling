# `vsa pdf` — Markdown met VSA naar PDF

Render één Markdownbestand naar een A4-PDF: [VSA-blokken](@) worden SVG,
`:::include` wordt opgelost, `:::pagebreak:::` / `{{< pagebreak >}}` worden
paginaeinden, en `:::web-only:::` verdwijnt (print-only blijft).

## Synopsis

```text
vsa pdf [-h] [--config CONFIG] [--content-root CONTENT_ROOT]
         [--bron-root BRON_ROOT] [--max-line-width MAX_LINE_WIDTH]
         [--chrome CHROME] [-o OUTPUT]
         input
```

## Beschrijving

`vsa pdf` gebruikt dezelfde voorbereiding als
[`vsa build-markdown`](build-markdown.md) voor **één** bestand: validatie,
catalogus-`zoek=`, includes, directives, SVG-render. Daarna wordt de
gegenereerde Markdown naar HTML omgezet (Hugo-shortcodes voor print/web
inbegrepen) en via Edge/Chrome/Chromium naar PDF geprint.

**Papierformaat (canoniek P6):** A4 staand (210×297 mm). Dat staat in de
print-CSS (`@page`), niet als aparte Chrome-CLI-flag. Zonder die CSS zou
headless Chrome op US Letter terugvallen — dat is **niet** canoniek. Zie
[canonieke checklists — PDF P6](../../formats/canonical-checklists.md#checklist-pdf-afgeleide-van-mscz).

Coria- en MusicXML-links horen bij de website en komen niet in de PDF.

Partituur-PDF vanuit `.mvsa`/`.mscz` (`mvsa pdf`) valt onder dezelfde
checklist-P6; daar komt A4 uit de MuseScore-Style van het `.mscz` (zie
[MSCZ-leesbaarheid](../../formats/mscz-leesbaarheid.md) en MSCZ S7).

Vóór het renderen geldt dezelfde validatie als [`vsa validate`](validate.md).
Fouten gebruiken hetzelfde formaat: bestand, regel, kolom, code, bronregel.

## Argumenten en opties

| Naam                          | Verplicht | Betekenis                                                                                          | Default                                                           | Beperkingen        |
| ----------------------------- | --------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------ |
| `input`                       | Ja        | Markdownbestand (`.md` / `.markdown`).                                                             | —                                                                 | Moet bestaan.      |
| `-o`, `--output OUTPUT`       | Nee       | Pad van de PDF.                                                                                    | `<stem>.pdf` in de huidige map                                    | Wordt overschreven |
| `--content-root CONTENT_ROOT` | Nee       | Root voor catalogus-includes (`lokaal/`).                                                          | Eerste bovenliggende map met `lokaal/`, anders de map van `input` | —                  |
| `--bron-root BRON_ROOT`       | Nee       | Root van de bron-repo.                                                                             | Auto (`vendor/bron` of `../bron`)                                 | —                  |
| `--config CONFIG`             | Nee       | Pad naar een alternatief `vsa.toml`.                                                               | Auto-detectie                                                     | —                  |
| `--max-line-width N`          | Nee       | Maximale SVG-regelbreedte.                                                                         | `max-line-width` uit `vsa.toml`, anders `800`                     | Getal (float)      |
| `--chrome CHROME`             | Nee       | Pad naar Edge, Chrome of Chromium.                                                                 | `CHROME_PATH` / `EDGE_PATH` / auto-detectie                       | Bestaan            |
| `-h`, `--help`                | Nee       | Toon hulp.                                                                                         | —                                                                 | —                  |

## Output

- **stdout**: `PDF geschreven naar: <pad>`
- **bestand**: de PDF op `--output` (of `<stem>.pdf`)

## Exit status

| Exitcode | Betekenis                                                                 |
| -------- | ------------------------------------------------------------------------- |
| `0`      | PDF geschreven.                                                           |
| `1`      | Validatiefout, include-/directivefout, of geen browser voor PDF-export.   |

## Voorbeelden — succes

```cmd
vsa pdf content-source\praktijk\samenstellingen\20260811-di-liturgie.md -o liturgie.pdf
```

Verwachte output:

```text
PDF geschreven naar: liturgie.pdf
```

## Voorbeelden — falen

Ongeldige VSA in het Markdownbestand:

```text
fout.md:2:8
ERROR: VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT: Modifierteken in gezongen tekst.
[:] {fout/}
       ^
```

Exitcode: `1`. Er wordt geen PDF geschreven.

Geen Edge/Chrome:

```text
ERROR: geen Chromium-browser gevonden voor PDF-export
Installeer Microsoft Edge of Google Chrome, of zet CHROME_PATH naar het .exe-bestand.
```

### Wat doe je bij problemen?

| Probleem                         | Controle                                                                 |
| -------------------------------- | ------------------------------------------------------------------------ |
| Validatiefout                    | Zelfde als `vsa validate`: regel/kolom en hint in de melding.            |
| Include niet gevonden            | `--content-root` naar de map met `lokaal/` (meestal `content-source`).   |
| Geen browser                     | Edge is standaard op Windows; anders `CHROME_PATH`.                      |
| Pagebreak ontbreekt in de PDF    | Gebruik `:::pagebreak:::` of `{{< pagebreak >}}` op een eigen regel.     |

## Zie ook

- [`vsa build-markdown`](build-markdown.md) — dezelfde Markdown/SVG-keten voor een hele site.
- [`vsa validate`](validate.md) — alleen controleren, zonder PDF.
- Consumer-site (Hugo-print-CSS): VSA-demo `static/css/site.css` (`@media print`).
