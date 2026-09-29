# `vsa build-markdown` — Hugo-Markdown en SVG-assets genereren

Genereer Hugo-geschikte Markdown en de bijbehorende SVG-assets uit
handgeschreven content-source.

## Synopsis

```text
vsa build-markdown [-h] [--config CONFIG] [--assets-url-prefix ASSETS_URL_PREFIX]
                    [--max-line-width MAX_LINE_WIDTH] [--output-mode {img,shortcode}]
                    input_dir output_dir assets_dir
```

## Beschrijving

`vsa build-markdown` is het belangrijkste commando voor een Hugo-publicatie.
Het leest recursief alle Markdown in `input_dir`, en schrijft voor elk
bestand:

1. gegenereerde Markdown in `output_dir` (met dezelfde relatieve
   mapstructuur als `input_dir`), waarin elk [VSA-blok](@) is vervangen door een
   `<img>`-tag of Hugo-shortcode die naar de bijbehorende SVG verwijst;
2. één SVG-bestand per [VSA-blok](@) in `assets_dir`.

Publishbare bestanden met open `:::include … zoek="…"` includes worden
automatisch opgelost via dezelfde stap als
[`vsa resolve-catalogus`](resolve-catalogus.md); voor sjablonen en sessies
buiten de publishbare structuur draai je die stap zelf vooraf.

Vóór het renderen valideert dit commando dezelfde controles als
[`vsa validate`](validate.md) op de gevonden [VSA-blokken](@).

## Argumenten en opties

| Naam                                     | Verplicht | Betekenis                                                                                                            | Default                                           | Beperkingen                   |
| ---------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------- |
| `input_dir`                              | Ja        | Bronmap met handgeschreven Markdown.                                                                                 | —                                                 | Moet bestaan.                 |
| `output_dir`                             | Ja        | Doelmap voor gegenereerde Markdown.                                                                                  | —                                                 | Wordt automatisch aangemaakt. |
| `assets_dir`                             | Ja        | Doelmap voor gegenereerde SVG-bestanden.                                                                             | —                                                 | Wordt automatisch aangemaakt. |
| `--config CONFIG`                        | Nee       | Pad naar een alternatief `vsa.toml`.                                                                                 | Auto-detectie van `vsa.toml`                      | —                             |
| `--assets-url-prefix ASSETS_URL_PREFIX`  | Nee       | URL-prefix die in de gegenereerde Markdown wordt gebruikt (bestandspad `assets_dir` blijft ongewijzigd — zie onder). | `assets-url-prefix` uit `vsa.toml`, anders `/vsa` | —                             |
| `--max-line-width MAX_LINE_WIDTH`        | Nee       | Maximale SVG-regelbreedte.                                                                                           | `max-line-width` uit `vsa.toml`, anders `800`     | Getal (float)                 |
| `--output-mode {img,shortcode}`          | Nee       | Vorm van de gegenereerde referentie naar de SVG (`img` = `<img>`-tag, `shortcode` = Hugo-shortcode).                 | `output-mode` uit `vsa.toml`, anders `img`        | Alleen `img` of `shortcode`   |
| `-h`, `--help`                           | Nee       | Toon hulp voor dit subcommando.                                                                                      | —                                                 | —                             |

## Output

- **stdout**: twee regels, `<n> Markdownbestand(en) geschreven` en
  `<n> SVG-bestand(en) geschreven`.
- **Bestanden**:
  - Markdown in `output_dir`, met dezelfde relatieve structuur als `input_dir`.
  - SVG in `assets_dir`, benoemd als `<stem>-block-<n>.svg`.
  - `.coria.html`-siblings naar `assets_dir/../coria/` (site-URL `/coria/…`).
  - Native `.mxl` / `.musicxml` naar `assets_dir/../mxl/` (site-URL `/mxl/…`).
    Afgeleide MXL uit een vsa-bestand blijft onder `static/vsa/mxl/` (via
    [`vsa musicxml`](musicxml.md)).

### Bestandspad versus URL-pad

`assets_dir` is een **bestandspad** (waar SVG's op schijf komen);
`--assets-url-prefix` is een **URL-pad** (wat in de gegenereerde HTML/Markdown
terechtkomt). Bijvoorbeeld:

| Soort        | Waarde                     | Betekenis                                     |
| ------------ | -------------------------- | --------------------------------------------- |
| Bestandspad  | `generated\static\vsa`     | Waar SVG's op schijf worden opgeslagen.       |
| URL-pad      | `/vsa`                     | Wat in de HTML/Markdown wordt gezet.          |

Als Hugo later `static\vsa` publiceert, wordt dat op de site bereikbaar als
`/vsa/naam.svg`.

### Wat verandert er in de Markdown?

Bron-Markdown:

```markdown
::: vsa-notatie
[:] {/Hei_}{/lig_} is de Heer. [:]
:::
```

Gegenereerde Markdown met `--output-mode img` (default):

```html
<img class="vsa-notation" src="/vsa/smoke-block-1.svg" alt="VSA notatie">
```

Gegenereerde Markdown met `--output-mode shortcode`:

```go-html-template
{{< vsa src="/vsa/smoke-block-1.svg" >}}
```

### Mvsa-blokken

Canonieke fence: `::: mvsa-notatie` … `:::`. Alias: `::: mvsa` (zelfde
gedrag). Alias voor eenstemmig: `::: vsa` ≡ `::: vsa-notatie`.

Bron:

```markdown
::: mvsa
@do F4
@mode major
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
:::
```

Na `build-markdown`: playback-``.mxl`` in `assets_dir` plus Hugo-shortcodes
`coria` en `mxl-download` (mvsa heeft geen SVG-renderer). Optionele
blok-metadata alleen als `key="waarde"` (niet `# key:` — dat is mvsa-commentaar).

`:::include lied.mvsa:::` wrapt het bestand als `::: mvsa-notatie`.

## Exit status

| Exitcode | Betekenis                                               |
| -------- | ------------------------------------------------------- |
| `0`      | Alle Markdown en SVG's succesvol geschreven.            |
| `1`      | Validatiefout in een [VSA-blok](@), of een andere fout. |

## Voorbeelden — succes

```cmd
vsa build-markdown examples\consumer-minimal\content-source generated\content generated\static\vsa
```

Voorbeeldinvoer (`examples\consumer-minimal\content-source\smoke.md`):

```markdown
# Smoke

::: vsa-notatie
[:] {/Hei_}{/lig_} is de Heer. [//:]
:::
```

Verwachte output:

```text
1 Markdownbestand(en) geschreven
1 SVG-bestand(en) geschreven
```

Resultaat op schijf:

```text
generated\content\smoke.md
generated\static\vsa\smoke-block-1.svg
```

## Voorbeelden — falen

```cmd
vsa build-markdown examples\minimal generated\content generated\static\vsa
```

`examples\minimal` bevat bewust ongeldige demo-bestanden (zie de notitie bij
[`vsa svg`](svg.md)), dus dit faalt met een validatiemelding, bijvoorbeeld:

```text
021_hugo_block_with_metadata.md:2:32
ERROR: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH: computed = marker + 2
do="F4"
                               ^
```

Exitcode: `1`. Er wordt geen Markdown of SVG geschreven.

### Wat doe je bij problemen?

| Probleem                           | Controle                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------ |
| Build stopt met validatiefout      | Draai `vsa validate <input_dir>`.                                        |
| Afbeelding niet zichtbaar in Hugo  | Controleer `--assets-url-prefix` tegen de Hugo `static`-configuratie.    |
| Shortcode zichtbaar als tekst      | Controleer of `layouts\shortcodes\vsa.html` bestaat in de consumer-site. |
| Oude output blijft zichtbaar       | Verwijder de output-map en bouw opnieuw.                                 |

## Zie ook

- [`vsa validate`](validate.md), [`vsa process`](process.md) — losse stappen die `build-markdown` combineert.
- [`vsa resolve-catalogus`](resolve-catalogus.md) — vereiste stap vóór build bij open `zoek=`-includes op niet-publishbare paden.
- Workflow-uitleg: [svg-export.md](../../guides/svg-export.md), [musicxml-export.md](../../guides/musicxml-export.md) (voor `:::coria`/`:::include mxl` in dezelfde build)
- `vsa.toml`-defaults: [config.md](../config.md)
