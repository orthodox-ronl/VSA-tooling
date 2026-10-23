# SVG exporteren

[`vsa svg`](../reference/cli/svg.md), [`vsa process`](../reference/cli/process.md)
en [`vsa build-markdown`](../reference/cli/build-markdown.md) renderen [VSA-notatie](@bron) naar
**SVG** — een schaalbare vectorafbeelding die je inline toont naast gewone
tekst, op scherm of afdruk. Dit is de meest gebruikte workflow: geen
externe player nodig, werkt zonder JavaScript, en schaalt scherp op elk
scherm.

Voor afspelen/oefenen gebruik je in plaats daarvan
[MusicXML/`.mxl`](musicxml-export.md).

## Wanneer gebruik je SVG?

| Situatie                                             | Gebruik SVG?                                                                         |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Notatie tonen naast liturgische tekst (web of print) | Ja                                                                                   |
| Consistente weergave op elk apparaat                 | Ja                                                                                   |
| Afdrukbaar boek/deel (A4, `@media print`)            | Ja                                                                                   |
| Audio afspelen of oefenen                            | Nee — gebruik [`vsa musicxml`](../reference/cli/musicxml.md)                         |
| Bewerken in MuseScore                                | Nee — gebruik [`vsa musicxml`](../reference/cli/musicxml.md) met profiel `engraving` |

## Drie manieren om SVG te genereren

| Commando                                                   | Wanneer                                                                          |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------- |
| [`vsa svg`](../reference/cli/svg.md)                       | `.vsa` (bestand of map) snel als SVG bekijken.                                   |
| [`vsa process`](../reference/cli/process.md)               | SVG's uit [VSA-blokken](@) in Markdown, zonder de Markdown te herschrijven.      |
| [`vsa build-markdown`](../reference/cli/build-markdown.md) | Hugo-[publicatie](@): Markdown **en** SVG-assets in één stap (inline rendering). |

Voor een losse controle tijdens het schrijven is
[`vsa svg`](../reference/cli/svg.md) het snelst. Voor een echte [publicatie](@)
(Hugo-site) gebruik je [`vsa build-markdown`](../reference/cli/build-markdown.md),
dat de `::: vsa-notatie … :::`-blokken in je Markdown automatisch vervangt door een
verwijzing naar de gegenereerde SVG (zie
["Inline rendering via `build-markdown`"](#inline-rendering-via-build-markdown)
hieronder).

## Snel starten

Eén geldige frase bekijken (`examples\docs-walkthroughs\svg-phrase-kort.vsa`):

```text
[:] {/Hei_}{/lig_} is de Heer. [//:]
```

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa -o generated\vsa\svg-phrase-kort.svg
```

```text
SVG geschreven naar: generated\vsa\svg-phrase-kort.svg
```

Zonder `-o` schrijft het commando een sibling ``….vsa.svg`` naast de bron
(zelfde naamgeving als bibliotheek-producten / [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg)).

![Korte VSA-frase als SVG](assets/walkthroughs/svg-phrase-kort.svg)

### Langere frase + regelbreedte

Zelfde start, langere tekst
(`examples\docs-walkthroughs\svg-phrase-lang.vsa`), met smallere
`--max-line-width` zodat de [renderer](@) afbreekt:

```cmd
vsa svg examples\docs-walkthroughs\svg-phrase-lang.vsa -o generated\vsa\svg-phrase-lang.svg --max-line-width 400
```

![Langere VSA-frase, afgebroken SVG](assets/walkthroughs/svg-phrase-lang.svg)

SVG's uit een map met Markdown, zonder Hugo-Markdown te genereren
(levert o.a. `toon-1-block-1.svg` en `toon-2-block-1.svg`):

```cmd
vsa process examples\site-demo generated\vsa
```

Volledige Hugo-[publicatie](@) (Markdown + SVG-assets):

```cmd
vsa build-markdown examples\consumer-minimal\content-source generated\content generated\static\vsa
```

Zie de man-pagina's voor de volledige argumentenlijst, opties en
foutgevallen: [`cli/svg.md`](../reference/cli/svg.md),
[`cli/process.md`](../reference/cli/process.md),
[`cli/build-markdown.md`](../reference/cli/build-markdown.md).

Preview-SVG's in deze docs regenereren (na wijziging van de bron-`.vsa`):

```cmd
python scripts\sync-docs-walkthrough-svgs.py
```

## Inline rendering via `build-markdown`

[`vsa build-markdown`](../reference/cli/build-markdown.md) vervangt in de gegenereerde Markdown elk [VSA-blok](@) door
een verwijzing naar de gegenereerde SVG. Bron-Markdown:

```markdown
::: vsa-notatie
[:] {/Hei_}{/lig_} is de Heer. [:]
:::
```

wordt, met `--output-mode img` (default), een gewone `<img>`-tag:

```html
<img class="vsa-notation" src="/vsa/smoke-block-1.svg" alt="VSA notatie">
```

of, met `--output-mode shortcode`, een Hugo-shortcode:

```go-html-template
{{< vsa src="/vsa/smoke-block-1.svg" >}}
```

Kies `shortcode` als je in de consumer-site meer controle wilt over hoe de
SVG wordt ingebed (bijv. lazy-loading, wrapper-`<div>`, of print-specifieke
opmaak via `layouts\shortcodes\vsa.html`); kies `img` als je geen
aangepaste Hugo-shortcode wilt onderhouden.

## Bestandspad versus URL-pad: `assets_dir` en `--assets-url-prefix`

Dit onderscheid is de meest voorkomende bron van verwarring bij
`build-markdown`:

| Soort        | Argument/optie                | Voorbeeldwaarde            | Betekenis                                                        |
| ------------ | ----------------------------- | -------------------------- | ---------------------------------------------------------------- |
| Bestandspad  | `assets_dir` (positioneel)    | `generated\static\vsa`     | Waar de tool de SVG's **op schijf** schrijft.                    |
| URL-pad      | `--assets-url-prefix`         | `/vsa`                     | Wat er in de gegenereerde `<img src="…">`/shortcode terechtkomt. |

Deze twee zijn onafhankelijk: `assets_dir` bepaalt alleen waar bestanden
komen te staan, `--assets-url-prefix` bepaalt alleen de tekst die in de
Markdown/HTML verschijnt. Ze moeten wél op elkaar aansluiten zodra Hugo de
site publiceert:

```text
assets_dir:            generated\static\vsa
                                 ↓ (Hugo publiceert static\ als site-root)
publieke URL:           https://mijn-site/vsa/smoke-block-1.svg
--assets-url-prefix:    /vsa
```

Als `--assets-url-prefix` niet overeenkomt met waar Hugo `assets_dir`
publiceert (meestal de `static\vsa`-submap van de Hugo-site), tonen
afbeeldingen niet — de SVG-bestanden bestaan wel, maar de link in de HTML
wijst naar de verkeerde plek.

Default-waarden staan (net als `max-line-width` en `output-mode`) in
[vsa.toml](@); zie [config.md](../reference/config.md) voor de voorrangsregel
(CLI-optie → [vsa.toml](@) → interne default).

## Waar komen de gegenereerde bestanden terecht?

SVG's die je met [`vsa svg`](../reference/cli/svg.md),
[`vsa process`](../reference/cli/process.md) of
[`vsa build-markdown`](../reference/cli/build-markdown.md) genereert,
zijn **[afgeleide](@bron)** bestanden uit de `.vsa`-bron en horen niet gecommit
te worden naast de bron. Gebruik
lokaal een map als `generated\` (of `tmp\`) die in `.gitignore` staat:

```text
mijn-repo/
  content/                   # of content-source/ — VSA-bron (wél in git)
    voorbeeld.md
  generated/                 # SVG- en Markdown-output (niet in git)
    static\vsa\voorbeeld-block-1.svg
    content\voorbeeld.md
```

In een Hugo-consumer-site komt de `assets_dir` overeen met de `static\vsa`-map
van die site (zie [consumer-site.md](../manuals/consumer-site.md) en
[reuse-vsa-tooling.md](reuse-vsa-tooling.md) voor het volledige
build-in-CI-voorbeeld). In de [bron-repository](@bron) zelf worden geen [afgeleide](@bron)
SVG's opgeslagen — daar staat alleen de `.vsa`-bron (zie
[repo-structuur](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/repo-structuur.md)
en het `derived/`-concept daar voor build-output dat nooit in git komt).

## Diagnose bij problemen

| Symptoom                             | Controle                                                                                       |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Commando faalt met validatiefout     | Draai [`vsa validate`](../reference/cli/validate.md) op de invoer voor de exacte foutlocatie.  |
| SVG ziet er raar uit                 | Controleer `--max-line-width`; bewaar het voorbeeld eventueel als regressiecase.               |
| Afbeelding niet zichtbaar in Hugo    | Controleer of `--assets-url-prefix` aansluit op waar Hugo `assets_dir` publiceert (zie boven). |
| Shortcode zichtbaar als tekst        | Controleer of `layouts\shortcodes\vsa.html` bestaat in de consumer-site.                       |
| Oude SVG's blijven zichtbaar         | Verwijder de output-map (`generated\…`) en bouw opnieuw.                                       |

## Zie ook

- Man-pagina's: [`vsa svg`](../reference/cli/svg.md), [`vsa process`](../reference/cli/process.md), [`vsa build-markdown`](../reference/cli/build-markdown.md)
- CLI-overzicht: [CLI-referentie](../reference/cli/index.md)
- MusicXML-workflow (afspelen/oefenen, alternatief voor SVG): [musicxml-export.md](musicxml-export.md)
- [vsa.toml](@)-defaults en voorrang: [config.md](../reference/config.md)
- Consumer-site-structuur: [consumer-site.md](../manuals/consumer-site.md)
- Integratie in andere repo's/CI: [reuse-vsa-tooling.md](reuse-vsa-tooling.md)
- Bron-contracten (normatief): [conversie-vsa-svg](https://orthodox-ronl.github.io/bron/reference/conversie-vsa-svg/), [exporttype-svg](https://orthodox-ronl.github.io/bron/reference/exporttype-svg/) ([exporttype](@bron) `svg`)
