# Invoer: bestand, map of catalogus-id

## Afspraak

Een CLI-``path`` (of ``input``) is:

1. **één bronbestand** met de juiste extensie, of
2. **een map** waarvan (standaard **recursief**) alle bestanden met die
   extensie(s) worden meegenomen, of
3. **een catalogus-id** die onder ``content-source/catalogus/`` wordt
   opgezocht (alleen als het pad **niet** als bestand of map bestaat).

Gedeelde helper: ``vsa.input_paths.collect_input_files`` /
``collect_cli_sources`` (lege map = fout). Unit tests:
``tests/test_input_paths.py``, ``tests/test_cli_batch_sources.py``.

Nieuwe of gewijzigde commando’s met bestandsinvoer gebruiken deze helper
(of een dunne wrapper eromheen). Geen ad-hoc ``rglob`` meer per handler.

**Meerdere bronnen:** sibling-output per bestand (``derived_output_path``).
``-o`` / ``--keep-*`` / vergelijkbare enkelvoudige uitvoerpaden zijn **alleen**
toegestaan bij precies één bronbestand.

### Catalogus-id

Toegestane vormen (zelfde id-conventie als ``bieb id="…"``):

| Vorm                       | Voorbeeld                               | Resolutie                                                   |
| -------------------------- | --------------------------------------- | ----------------------------------------------------------- |
| Slash-pad (leaf)           | `tropaar/transfiguratie-toon-7/hemelum` | Map `catalogus/<id>/` → bestanden met gevraagde extensie(s) |
| Canonieke stam (`/` → `-`) | `tropaar-transfiguratie-toon-7-hemelum` | Zelfde leaf: uniek bestand met die stem (zonder extensie)   |

De stamvorm is de **canonieke bestandsnaam zonder** `.vsa` / `.mvsa`: de drie
id-segmenten met `-` i.p.v. `/`. Beide vormen zijn gelijkwaardig.

Zoekvolgorde voor de catalogus-root:

1. Omgevingsvariabele ``VSA_CATALOGUS`` (pad naar ``…/catalogus``)
2. ``./content-source/catalogus`` t.o.v. de werkmap
3. Sibling ``../bibliotheek/content-source/catalogus`` (naast VSA-tooling)

Geen match → dezelfde foutklasse als een ontbrekend pad
(``InputPathError`` / «Pad niet gevonden» / «Catalogus-id … niet gevonden»).

Voorbeelden:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate tropaar/transfiguratie-toon-7/hemelum
vsa syllabify tropaar-transfiguratie-toon-7-hemelum --dry-run
mvsa validate tropaar/transfiguratie-toon-7/hemelum
```

### Geneste afgeleiden (batch)

Bestandsnamen volgen ``stem.brontype.doeltype`` (bijv. ``lied.mvsa`` →
``lied.mvsa.mscz``). Bij een **map** slaagt de helper bestanden over waarvan
de stam al een brontype-extensie heeft (``.mvsa``, ``.vsa``, ``.mscz``,
``.mxl``, …). Zo maakt ``mscz products catalogus/`` geen
``lied.mvsa.mscz.svg`` of ``lied.mvsa.mscz.products-meta.json`` aan.

**Wel** toegestaan: het bestand expliciet noemen
(``mscz products lied.mvsa.mscz``), als je bewust producten van die
afgeleide wilt.

## Inventaris

### `vsa` (top-level)

| Commando              | Map?  | Extensies / opmerking                                      |
| --------------------- | ----- | ---------------------------------------------------------- |
| `validate`            | Ja    | `.vsa` / `.md` / `.markdown` (`validation_runner`)         |
| `parse`               | Nee   | één `.vsa`                                                 |
| `blocks`              | Nee   | één `.md`                                                  |
| `svg`                 | Ja    | `.vsa`; bij map is `output` een uitvoermap                 |
| `process`             | Ja    | map met Markdown (`markdown_processor`)                    |
| `build-markdown`      | Ja    | invoermap (geen «of bestand»-semantiek)                    |
| `pdf`                 | Nee   | één `.md`                                                  |
| `resolve-catalogus`   | Nee   | één `.md`                                                  |
| `syllabify`           | Ja    | `.vsa` (`iter_vsa_files` → ``collect_input_files``)        |
| `text`                | Ja    | `.vsa` / `.mvsa` / MusicXML / `.mscz`                      |
| `zoektekst`           | Ja    | `.vsa` / `.mvsa` (`iter_vsa_mvsa_files` → helper)          |
| `mxl` (`musicxml`)    | Ja    | alleen `.vsa` (straat-puur; sibling of `-o`)               |
| `products`            | Ja    | `.vsa` (`collect_cli_sources` / street products)           |
| `audio`               | Ja    | alleen `.vsa` in code; help/docs nog inhalen (apart)       |
| `template validate`   | Ja    | `template.yaml` in map                                     |

### `mvsa` (stap 2: exports via helper)

| Commando          | Map? | Extensies                                                |
| ----------------- | ---- | -------------------------------------------------------- |
| `validate`        | Ja   | `.mvsa` (`collect_mvsa_files` → ``collect_input_files``) |
| `mxl`             | Ja   | alleen `.mvsa` (straat-puur; `.mscz` → `mscz mxl`)       |
| `mscz`            | Ja   | `.mvsa`                                                  |
| `pdf` / `svg`     | Ja   | alleen `.mvsa` (`.mscz` → `mscz pdf` / `mscz svg`)       |
| `mp3`/`ogg`/`wav` | Ja   | alleen `.mvsa`                                           |
| `text`            | Ja   | alleen `.mvsa`                                           |
| `score-ir`        | Ja   | `.mvsa`                                                  |
| `normalize`       | Ja   | `.mvsa`                                                  |
| `transpose`       | Ja   | `.mvsa`                                                  |
| `kuiser`          | Ja   | `.mvsa` (via ``collect_cli_sources``)                    |
| `syllabify`       | Ja   | `.mvsa`                                                  |
| `vsa`             | Ja   | `.mvsa` → sibling `.mvsa.vsa` (E1–E6)                    |
| `products`        | Ja   | `.mvsa` (incl. product-key `vsa`)                        |

### `mxl` / `mscz` (top-level)

| Commando              | Map? | Extensies / opmerking                                          |
| --------------------- | ---- | -------------------------------------------------------------- |
| `mxl mvsa`            | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml`` → ``.mvsa``                |
| `mxl mscz`            | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml``                            |
| `mxl validate`        | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml``                            |
| `mxl normalize`       | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml`` (default: in-place)        |
| `mscz …` (producten)  | Ja   | alleen ``.mscz`` (`mxl`/`svg`/`pdf`/`mp3`/`score-ir`/`text`/…) |
| `mscz compare`        | Nee  | SCORE = ``.mscz`` of MusicXML; MVSA = ``.mvsa``                |
| `mscz import`         | Ja   | ``.mvsa`` / MusicXML → ``.mscz``                               |

## Migratie

Gedeelde helper is in gebruik voor `mvsa`-exports, `mxl`/`mscz`-aliases,
top-level `text` / `audio` / `svg`, en de wrappers `collect_mvsa_files` /
`iter_vsa_files` / `iter_vsa_mvsa_files`.

`markdown pdf` / `markdown svg` / `markdown text` ondersteunen bestand-of-map. Optioneel later:
`vsa parse` en overige map-scanners (`validate`, `process`, `template`)
waar die nog eigen `rglob` hebben. `vsa mxl` gebruikt al `collect_cli_sources`.
