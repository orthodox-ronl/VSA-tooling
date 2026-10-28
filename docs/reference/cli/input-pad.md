# Invoer: bestand of map

## Afspraak

Een CLI-``path`` (of ``input``) is:

1. **één bronbestand** met de juiste extensie, of
2. **een map** waarvan (standaard **recursief**) alle bestanden met die
   extensie(s) worden meegenomen.

Gedeelde helper: ``vsa.input_paths.collect_input_files`` /
``collect_cli_sources`` (lege map = fout). Unit tests:
``tests/test_input_paths.py``, ``tests/test_cli_batch_sources.py``.

Nieuwe of gewijzigde commando’s met bestandsinvoer gebruiken deze helper
(of een dunne wrapper eromheen). Geen ad-hoc ``rglob`` meer per handler.

**Meerdere bronnen:** sibling-output per bestand (``derived_output_path``).
``-o`` / ``--keep-*`` / vergelijkbare enkelvoudige uitvoerpaden zijn **alleen**
toegestaan bij precies één bronbestand.

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
| `musicxml`            | Deels | map ondersteund in renderer-pad; check man-pagina          |
| `products`            | Ja    | `.vsa` (`collect_cli_sources` / street products)           |
| `audio`               | Ja    | zelfde bronnen; bij map is `output` een uitvoermap         |
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
| `products`        | Ja   | `.mvsa`                                                  |

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
`vsa parse` en overige map-scanners (`musicxml`, `validate`, `process`,
`template`) waar die nog eigen `rglob` hebben.
