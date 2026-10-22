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
| `audio`               | Ja    | zelfde bronnen; bij map is `output` een uitvoermap         |
| `template validate`   | Ja    | `template.yaml` in map                                     |

### `vsa mvsa` / `mvsa` (stap 2: exports via helper)

| Commando          | Map? | Extensies                                                |
| ----------------- | ---- | -------------------------------------------------------- |
| `validate`        | Ja   | `.mvsa` (`collect_mvsa_files` → ``collect_input_files``) |
| `mxl`             | Ja   | `.mvsa` / `.mscz` / `.mxl` / `.musicxml` / `.xml`        |
| `mscz`            | Ja   | `.mvsa`                                                  |
| `pdf`             | Ja   | `.mvsa` / `.mscz`                                        |
| `svg`             | Ja   | `.mvsa` / `.mscz`                                        |
| `mp3`/`ogg`/`wav` | Ja   | `.mvsa` / `.mxl` / `.musicxml` / `.vsa` / `.mscz`        |
| `score-ir`        | Ja   | `.mvsa`                                                  |
| `import`          | Ja   | `.mxl` / `.musicxml` / `.xml` / `.mscz`                  |
| `normalize`       | Ja   | `.mvsa`                                                  |
| `kuiser`          | Ja   | `.mvsa` (via ``collect_cli_sources``)                    |

### `mxl` / `mscz` (top-level aliases)

| Commando        | Map? | Extensies / opmerking                                       |
| --------------- | ---- | ----------------------------------------------------------- |
| `mxl import`    | Ja   | via ``mvsa import`` (``.mxl`` / ``.musicxml`` / ``.xml``)   |
| `mxl mscz`      | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml``                         |
| `mxl validate`  | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml``                         |
| `mxl normalize` | Ja   | ``.mxl`` / ``.musicxml`` / ``.xml`` (default: in-place)     |
| `mscz import`   | Ja   | via ``mvsa import`` (``.mscz``)                             |
| `mscz mxl`      | Ja   | ``.mscz``                                                   |
| `mscz text`     | Ja   | ``.mscz`` (per bestand → ``vsa text``; ``-o`` alleen bij 1) |

## Migratie

Gedeelde helper is in gebruik voor `mvsa`-exports, `mxl`/`mscz`-aliases,
top-level `text` / `audio` / `svg`, en de wrappers `collect_mvsa_files` /
`iter_vsa_files` / `iter_vsa_mvsa_files`.

Optioneel later: top-level `vsa pdf` / `parse` alleen als bestand-of-map
zinvol is; overige map-scanners (`musicxml`, `validate`, `process`,
`template`) waar die nog eigen `rglob` hebben.
