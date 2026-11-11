# `vsa mxl` — exporteren naar MusicXML

Exporteer eenstemmige [VSA](@) (`.vsa`) naar Coria-playback MusicXML:
gecomprimeerd **`.mxl`** (standaard) of platte **`.musicxml`**.

Zelfde CLI-vorm als [`mvsa mxl`](mvsa.md#mvsa-mxl) en [`mscz mxl`](mscz.md):
`PATH [-o OUTPUT]`. Alias: `vsa musicxml` (zelfde argumenten).

## Synopsis

```text
vsa mxl [-h] [-o OUTPUT] [--config CONFIG] [--format {musicxml,mxl}]
        [--do DO] [--mode MODE] [--tempo TEMPO]
        [--musicxml-profile {playback,engraving}] [--syllabify]
        path
```

## Beschrijving

`vsa mxl` leest **alleen** `.vsa` (straat-puur; bestand of map, recursief).
Andere bronnen: [`mvsa mxl`](mvsa.md#mvsa-mxl) / [`mscz mxl`](mscz.md).

Zonder `-o` komt de uitvoer als sibling naast elke bron
(`lied.vsa` → `lied.vsa.mxl`). `-o` mag alleen bij precies één bronbestand.
Zie [Invoer bestand of map](input-pad.md).

Metadata (grondtoon, mode, tempo, exportprofiel, …) komt uit de
YAML-frontmatter van het `.vsa`-bestand; de CLI-opties `--do`, `--mode`,
`--tempo` en `--musicxml-profile` overschrijven die bestand-metadata.

Standaard gebruikt `vsa mxl` het `playback`-profiel (afspelen/import in
Coria en MuseScore zonder handmatige opschoning). Bij `playback` volgt na
de export een **Coria-finalize** (sanitize + voortekens; geen DOCTYPE) —
checklist M* in
[canonical-checklists](../../formats/canonical-checklists.md). Kies
`engraving` (via `--musicxml-profile` of frontmatter
`muziek.musicxml-profile: engraving`) als je de partituur verder wilt
bewerken; dan blijft finalize uit. Zie
[musicxml-export.md](../../guides/musicxml-export.md) voor beide
profielen en frontmatter-instellingen.

`--syllabify` voegt tijdelijke lettergreepstreepjes toe vóór de export; de
canonieke `.vsa` blijft ongewijzigd. [`vsa products`](products.md) doet die
syllabify altijd voor de MXL-sibling. Losse bron bewerken:
[`vsa syllabify`](syllabify.md).

Bij sibling- of expliciete output merget `vsa mxl` product-key `mxl` in
`{stam}.vsa.products-meta.json` — zie
[products-meta](../../formats/products-meta.md).

## Argumenten en opties

| Naam                                      | Verplicht | Betekenis                                                                     | Default                                                         | Beperkingen                      |
| ----------------------------------------- | --------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------- |
| `path`                                    | Ja        | `.vsa`-bestand of map met `.vsa`-bestanden (recursief).                       | —                                                               | Alleen `.vsa` (straat-puur).     |
| `-o`, `--output`                          | Nee       | Uitvoerpad (`.mxl` / `.musicxml` / `.xml`).                                   | Sibling `<bronnaam>.vsa.mxl` (of `.musicxml` via `--format`)    | Alleen bij precies één bron.     |
| `--config CONFIG`                         | Nee       | Pad naar een alternatief `vsa.toml`.                                          | Auto-detectie van `vsa.toml`                                    | —                                |
| `--format {musicxml,mxl}`                 | Nee       | Uitvoerformaat wanneer `-o` geen expliciete extensie heeft, of bij sibling.   | `mxl`                                                           | Alleen `musicxml` of `mxl`       |
| `--do DO`                                 | Nee       | Grondtoon, bijv. `F4` (overschrijft bestand-metadata `muziek.do`).            | Bestand-metadata, anders `F4`                                   | —                                |
| `--mode MODE`                             | Nee       | Modus, `major` of `minor` (overschrijft bestand-metadata `muziek.mode`).      | Bestand-metadata, anders `major`                                | —                                |
| `--tempo TEMPO`                           | Nee       | Tempo in BPM (overschrijft bestand-metadata `muziek.tempo`).                  | Bestand-metadata; zonder expliciete waarde geen tempo-markering | —                                |
| `--musicxml-profile {playback,engraving}` | Nee       | Exportprofiel (overschrijft bestand-metadata `muziek.musicxml-profile`).      | Bestand-metadata, anders `playback`                             | Alleen `playback` of `engraving` |
| `--syllabify`                             | Nee       | Tijdelijke lettergreepstreepjes vóór export (bron blijft ongewijzigd).        | Uit                                                             | —                                |
| `-h`, `--help`                            | Nee       | Toon hulp voor dit subcommando.                                               | —                                                               | —                                |

## Output

- **stdout (één bron):** `Geschreven: <pad>`; eventueel `Meta: …`.
- **stdout (meerdere bronnen):** per bestand `Geschreven: …`, daarna
  `<n> MXL-bestand(en) geschreven` (of MusicXML, afhankelijk van `--format`).
- **Bestanden:** `.mxl` (standaard) of `.musicxml`.
- **stderr:** foutmeldingen (verkeerde extensie, parsefout, exportfout).

## Exit status

| Exitcode | Betekenis                                                    |
| -------- | ------------------------------------------------------------ |
| `0`      | Alle gevraagde MusicXML-bestanden succesvol geschreven.      |
| `1`      | Padfout, verkeerde bronextensie, parsefout, of exportfout.   |

## Voorbeelden — succes

Sibling-default (naast de bron):

```cmd
vsa mxl examples\minimal\050_svg_demo.vsa
```

Verwachte output (pad kan afwijken):

```text
Geschreven: examples\minimal\050_svg_demo.vsa.mxl
```

Expliciet uitvoerpad:

```cmd
vsa mxl examples\minimal\050_svg_demo.vsa -o tmp\demo.mxl
```

Zonder extensie op `-o` krijg je ook `.mxl`:

```cmd
vsa mxl mijn-lied.vsa -o output\mijn-lied
```

```text
Geschreven: output\mijn-lied.mxl
```

Platte MusicXML:

```cmd
vsa mxl mijn-lied.vsa -o mijn-lied.musicxml
```

Of via `--format` bij sibling-default:

```cmd
vsa mxl mijn-lied.vsa --format musicxml
```

Map-export (sibling `.mxl` per `.vsa`):

```cmd
vsa mxl content-source\praktijk
```

```text
Geschreven: …
<n> MXL-bestand(en) geschreven
```

Expliciet exportprofiel:

```cmd
vsa mxl lied.vsa -o lied.mxl --musicxml-profile engraving
```

Coria-playback met tijdelijke syllabify (zelfde MXL-keten als `vsa products`,
zonder SVG):

```cmd
vsa mxl lied.vsa --syllabify
```

Alias (zelfde vorm):

```cmd
vsa musicxml lied.vsa -o lied.mxl
```

## Voorbeelden — falen

Verkeerde bronextensie:

```cmd
vsa mxl lied.mvsa
```

Verwachte output (stderr):

```text
vsa mxl weigert .mvsa; gebruik: mvsa mxl …
```

Exitcode: `1`. Fix: gebruik `mvsa mxl` voor `.mvsa`, of geef een `.vsa`.

Bij een MusicXML-exportfout:

```text
mijn-lied.vsa: fout bij MusicXML-export: <uitleg>
```

Exitcode: `1`. Fix: controleer de gemelde constructie; draai eventueel eerst
`vsa validate`.

## Zie ook

- Workflow, profielen, Coria, frontmatter: [musicxml-export.md](../../guides/musicxml-export.md)
- [`mvsa mxl`](mvsa.md#mvsa-mxl) · [`mscz mxl`](mscz.md) — andere bronstraten
- [`vsa products`](products.md) — standaardproducten + products-meta
- [`vsa syllabify`](syllabify.md) — lettergreepstreepjes in de bron zelf
- [`vsa validate`](validate.md) — controle vóór export
- [Invoer bestand of map](input-pad.md)
- Outputreferentie: [outputs.md](../outputs.md)
- Bron-contract (exporttype mxl/coria): [exporttype-coria](https://orthodox-ronl.github.io/bron/reference/exporttype-coria/)
