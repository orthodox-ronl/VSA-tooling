# `vsa musicxml` — exporteren naar MusicXML

Exporteer [VSA](@) naar gecomprimeerde MusicXML (`.mxl`, standaard) of platte
MusicXML (`.musicxml`).

## Synopsis

```text
vsa musicxml [-h] [--config CONFIG] [--format {musicxml,mxl}] [--do DO]
             [--mode MODE] [--tempo TEMPO]
             [--musicxml-profile {playback,engraving}] [--syllabify]
             input output
```

## Beschrijving

`vsa musicxml` leest `input` — een `.vsa`-bestand, een Markdownbestand met
[VSA-blokken](@), of een map — en schrijft één of meer MusicXML-bestanden. De
gebruikte [metadata](@) (grondtoon, mode, tempo, exportprofiel, …) komt uit de
YAML-frontmatter van het `.vsa`-bestand (of de [blokmetadata](@) in Markdown); de
CLI-opties `--do`, `--mode`, `--tempo` en `--musicxml-profile` overschrijven
die bestand-metadata.

Gedrag hangt af van het type van `input`:

| `input`-type              | Gedrag van `output`                                                                                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.vsa`-bestand            | `output` is het doelbestand. Zonder herkende extensie wordt `--format` (of default `.mxl`) toegevoegd; met een expliciete extensie (`.mxl`/`.musicxml`) wint die. |
| `.md`/`.markdown`-bestand | `output` is een map; per [VSA-blok](@) komt er één bestand (`<stem>-<n>.<ext>` bij meer dan 1 blok).                                                              |
| Map                       | `output` is een map; alle `.vsa`- en `.md`-bestanden worden recursief verwerkt, met behoud van relatieve mapstructuur.                                            |

Standaard gebruikt `vsa musicxml` het `playback`-profiel (bedoeld voor
afspelen/import in Coria en MuseScore zonder handmatige opschoning). Bij
`playback` volgt na de export een **Coria-finalize** (sanitize + voortekens;
geen DOCTYPE in het MusicXML) — checklist M* in
[canonical-checklists](../../formats/canonical-checklists.md). Kies
`engraving` (via `--musicxml-profile` of frontmatter
`muziek.musicxml-profile: engraving`) als je de partituur verder wilt
bewerken en expliciete maatstrepen of typografie-hints nodig hebt; dan
blijft finalize uit. Zie [musicxml-export.md](../../guides/musicxml-export.md)
voor de volledige uitleg van beide profielen en alle frontmatter-instellingen.

`--syllabify` voegt tijdelijke lettergreepstreepjes toe vóór de export; de
canonieke `.vsa` blijft ongewijzigd. [`vsa products`](products.md) doet die
syllabify altijd voor de MXL-sibling. Losse bron bewerken: [`vsa syllabify`](syllabify.md).

## Argumenten en opties

| Naam                                          | Verplicht | Betekenis                                                                         | Default                                                         | Beperkingen                            |
| --------------------------------------------- | --------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------- |
| `input`                                       | Ja        | VSA-bestand (`.vsa`), Markdown-bestand (`.md`) of map.                            | —                                                               | Moet bestaan; anders `.vsa`/`.md`/map. |
| `output`                                      | Ja        | Doelbestand (enkel invoerbestand) of doelmap (meerdere bestanden).                | —                                                               | Zie tabel hierboven.                   |
| `--config CONFIG`                             | Nee       | Pad naar een alternatief `vsa.toml`.                                              | Auto-detectie van `vsa.toml`                                    | —                                      |
| `--format {musicxml,mxl}`                     | Nee       | Uitvoerformaat wanneer `output` geen expliciete extensie heeft.                   | `mxl`                                                           | Alleen `musicxml` of `mxl`             |
| `--do DO`                                     | Nee       | Grondtoon, bijv. `F4` (overschrijft bestand-metadata `muziek.do`).                | Bestand-metadata, anders `F4`                                   | —                                      |
| `--mode MODE`                                 | Nee       | Modus, `major` of `minor` (overschrijft bestand-metadata `muziek.mode`).          | Bestand-metadata, anders `major`                                | —                                      |
| `--tempo TEMPO`                               | Nee       | Tempo in BPM (overschrijft bestand-metadata `muziek.tempo`).                      | Bestand-metadata; zonder expliciete waarde geen tempo-markering | —                                      |
| `--musicxml-profile {playback,engraving}`     | Nee       | Exportprofiel (overschrijft bestand-metadata `muziek.musicxml-profile`).          | Bestand-metadata, anders `playback`                             | Alleen `playback` of `engraving`       |
| `--syllabify`                                 | Nee       | Tijdelijke lettergreepstreepjes vóór export (bronbestand blijft ongewijzigd).     | Uit                                                             | Alleen zinvol bij `.vsa`-invoer        |
| `-h`, `--help`                                | Nee       | Toon hulp voor dit subcommando.                                                   | —                                                               | —                                      |

## Output

- **stdout (enkel `.vsa`-bestand)**: `MusicXML geschreven naar: <output>`.
- **stdout (map of Markdown met meerdere blokken)**: `<n> MXL-bestand(en) geschreven` of `<n> MusicXML-bestand(en) geschreven`, afhankelijk van `--format`.
- **Bestanden**: `.mxl` (standaard) of `.musicxml`, op de locatie(s) bepaald door de tabel in de beschrijving.
- **stderr**: foutmeldingen (bestand niet gevonden, `@include-vsa`-fout, MusicXML-exportfout, onbekend bestandstype).

## Exit status

| Exitcode | Betekenis                                                               |
| -------- | ----------------------------------------------------------------------- |
| `0`      | Alle gevraagde MusicXML-bestanden succesvol geschreven.                 |
| `1`      | Bestand niet gevonden, parsefout, exportfout, of onbekend bestandstype. |

## Voorbeelden — succes

Enkel bestand, standaard `.mxl`:

```cmd
vsa musicxml examples\minimal\050_svg_demo.vsa tmp\demo.mxl
```

Verwachte output:

```text
MusicXML geschreven naar: tmp\demo.mxl
```

Zonder extensie krijg je ook `.mxl`:

```cmd
vsa musicxml mijn-lied.vsa output\mijn-lied
```

```text
MusicXML geschreven naar: output\mijn-lied.mxl
```

Platte MusicXML, bijvoorbeeld voor bewerking in MuseScore:

```cmd
vsa musicxml mijn-lied.vsa mijn-lied.musicxml
```

Of expliciet via `--format`:

```cmd
vsa musicxml mijn-lied.vsa mijn-lied --format musicxml
```

Map-export (standaard `.mxl` per `.vsa`-bestand):

```cmd
vsa musicxml content-source\praktijk output\mxl
```

```text
<n> MXL-bestand(en) geschreven
```

Met een expliciet exportprofiel:

```cmd
vsa musicxml lied.vsa lied.mxl --musicxml-profile engraving
```

Coria-playback met tijdelijke syllabify (zelfde MXL-keten als `vsa products`,
zonder SVG/meta):

```cmd
vsa musicxml lied.vsa lied.mxl --syllabify
```

## Voorbeelden — falen

Onbekend bestandstype als invoer:

```cmd
vsa musicxml notities.txt output.mxl
```

Verwachte output (stderr):

```text
Onbekend bestandstype: '.txt'. Gebruik .vsa, .md of een map.
```

Exitcode: `1`. Fix: gebruik een `.vsa`- of `.md`-bestand, of een map.

Bij een MusicXML-specifieke exportfout (bijvoorbeeld een VSA-constructie die
niet naar noten kan worden vertaald):

```text
mijn-lied.vsa: fout bij MusicXML-export: <uitleg>
```

Exitcode: `1`. Fix: controleer de gemelde constructie in het `.vsa`-bestand;
draai eventueel eerst `vsa validate` om syntax-/semantiekfouten uit te
sluiten.

## Zie ook

- Volledige workflow, profielen, Coria-integratie en frontmatter-instellingen: [musicxml-export.md](../../guides/musicxml-export.md)
- [`vsa products`](products.md) — MXL + SVG + products-meta (syllabify + finalize)
- [`vsa syllabify`](syllabify.md) — lettergreepstreepjes in de bron zelf
- [`vsa validate`](validate.md) — controleer [VSA-notatie](@bron) vóór export.
- Outputreferentie: [outputs.md](../outputs.md)
- Bron-contract (exporttype mxl/coria): [exporttype-coria](https://orthodox-ronl.github.io/bron/reference/exporttype-coria/)
