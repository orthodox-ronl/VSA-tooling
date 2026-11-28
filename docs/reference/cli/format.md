# `vsa format` — strofe-layout in `.vsa`

**Contract:** [vsa-format.md](../../formats/vsa-format.md).

Herschrijft hoe **strofen/frasen** in de VSA-body begrensd en op regels
gezet worden. YAML-frontmatter blijft onaangeroerd. Geen syllabify, geen
zoektekst, geen kuiser.

**Invoer:** bestand, map of catalogus-id — zie
[input-pad](input-pad.md). `-o` alleen bij precies één bronbestand.

## Synopsis

```text
vsa format [-h] [-o OUTPUT] [--check] [--dry-run]
           [--boundary {star,slash,newline}]
           [--layout {lines,flow}]
           [--wrap N]
           path [path …]
```

## Beschrijving

- **`--boundary star`** (default): gewone grens `*`; sterke grens blijft
  `**` waar die in de bron gold.
- **`--boundary slash`**: gewone `/`, sterke `//`.
- **`--boundary newline`**: geen `*`/`/` tussen strofen; regeleinde = grens
  (alleen met `--layout lines`).
- **`--layout lines`** (default): één strofe per regel.
- **`--layout flow`**: doorlopende tekst met `*` of `/` tussen strofen
  (niet combineerbaar met `newline`).
- **`--wrap N`**: soft-wrap per strofe op zichtbare-tekst-budget `N`
  (zie contract). Voortzetting begint met **4 spaties**; die indent **telt
  mee** in `N` (inhoud op voortzetting: `N − 4`). Strofe-delimiter
  (`*`/`/`/`**`/`//`) wordt nooit alleen op een nieuwe regel gezet.
  Weglaten of `0` = geen wrap; `N` moet `0` of ≥ `4` zijn.

Ingesprongen vervolgregels horen bij de vorige strofe (print-wrap).

### Schrijfmodi

Default schrijft **in-place**. `--dry-run` en `--check` schrijven nooit.

| Modus       | Gedrag                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------- |
| (geen flag) | Schrijf het resultaat naar elk bronbestand (of naar `-o` bij één bron).                        |
| `--dry-run` | Toon het geformatteerde resultaat; schrijf niets.                                              |
| `--check`   | Alleen rapporteren (`would change:` / `ok:`); exit 1 als er iets zou wijzigen; schrijf niets.  |

`--dry-run` en `--check` mag je niet combineren. `--dry-run` mag je niet
combineren met `-o` (er wordt toch niets geschreven).

### Output bij `--dry-run`

- **Eén bestand:** geformatteerde brontekst op **stdout**; op **stderr** een
  regel `(dry-run — gewijzigd|ongewijzigd; bestand niet geschreven)`.
- **Meerdere bestanden:** per bestand een kop `=== pad ===`, daarna de
  geformatteerde tekst, en een statusregel `(dry-run — …)` — alles op
  **stdout**.

## Argumenten

| Optie        | Verplicht | Beschrijving                                                                              | Default  |
| ------------ | --------- | ----------------------------------------------------------------------------------------- | -------- |
| `path`       | Ja        | `.vsa`-bestand, map, of catalogus-id ([input-pad](input-pad.md))                          | —        |
| `-o`         | Nee       | Uitvoer (alleen bij één bronbestand); niet met `--dry-run`                                | in-place |
| `--check`    | Nee       | Geen schrijven; exit 1 als er iets zou wijzigen; niet met `--dry-run`                     | uit      |
| `--dry-run`  | Nee       | Toon resultaat op het scherm; schrijf niets; niet met `--check` of `-o`                   | uit      |
| `--boundary` | Nee       | `star` / `slash` / `newline`                                                              | `star`   |
| `--layout`   | Nee       | `lines` / `flow`                                                                          | `lines`  |
| `--wrap`     | Nee       | Max. zichtbare-tekst-budget per regel (`0`/weg = uit; anders ≥ 4; indent telt mee)        | uit      |

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa format examples\minimal\001_plain_text.vsa --dry-run
vsa format communievers/kruisverheffing/hemelum --wrap 20 --dry-run
vsa format examples\minimal\001_plain_text.vsa --check
vsa format lied.vsa --boundary slash --layout flow
vsa format lied.vsa --wrap 40 --dry-run
vsa format lied.vsa -o generated\lied.fmt.vsa
```

## Zie ook

- [vsa-format.md](../../formats/vsa-format.md) · [kuiser](../../formats/kuiser.md#vsa-v)
- [Invoer bestand/map/catalogus-id](input-pad.md)
- [`vsa syllabify`](syllabify.md) · [`vsa zoektekst`](zoektekst.md)
