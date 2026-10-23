# `mxl` — conversies met MusicXML als bron

Top-level CLI voor bronbestanden `.mxl` / `.musicxml` / `.xml`.
Conventie: **`mxl {doeltype}`** (bronextensie → doelextensie).
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).
Playback-checklist:
[canonical-checklists — MXL](../../formats/canonical-checklists.md#checklist-mxl-coria--playback).

**`mxl mvsa`** maakt een **werkbank-bewerkvorm** — niet ongewijzigd als
catalogusbron gebruiken. De output begint met een ASCII-waarschuwingsbanner.
Details: [`.mvsa` — score naar mvsa](../../formats/mvsa.md#score-naar-mvsa).

**Invoer:** `path` mag één bronbestand **of** een map zijn (recursief). Bij
meerdere bronnen: sibling- of in-place-output per bestand; `-o` alleen bij
precies één bron. Zie [Invoer bestand of map](input-pad.md).

## Synopsis

```text
mxl [-h] {mvsa,mscz,validate,normalize} …
mxl mvsa [-h] [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}] [--do PITCH]
         [--octave-style {@oct,marker}] [--section SECTION] [--no-align] path
mxl mscz [-h] [-o OUTPUT] [--musescore PATH] path
mxl validate [-h] [--profile {satb,mono}] path
mxl normalize [-h] [-o OUTPUT] [--apply-timing] path
```

## Subcommando's

| Subcommando | Doel                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `mvsa`      | Naar `.mvsa`: direct SATB P1–P4. Default: `<bronnaam>.mvsa` (bijv. `lied.mxl.mvsa`).                                                     |
| `mscz`      | Naar checklist-`.mscz`: eerst partituur-layout (SA/TB), dan MuseScore. Default: `<bronnaam>.mscz` (bijv. `lied.mxl.mscz`).               |
| `validate`  | Lees-gate: M2/M8/M18 (monofone parts), M20 (note-kindvolgorde), Coria-importer-tags, meta (source ≠ licentie). Profiel `satb` of `mono`. |
| `normalize` | Schrijf playback-MXL: explode + piano + sanitize (incl. canonieke note-volgorde M20); met `--apply-timing` ook recite/pauzes.            |

**`mvsa`-opties** (`--pitch` default `ag-vsa`, `--no-align`, soft-wrap ~80,
eindankers bij `ag-vsa`/`vsa`, kuiser-normaalvorm): zie
[score naar mvsa](../../formats/mvsa.md#score-naar-mvsa). Bij complexe lyrics
soms `--no-align`; sync-telling blijft leidend. Default `--section schets`.

## Voorbeelden

```cmd
mxl mvsa generated\alleluia-schets2.mxl
mxl mvsa generated\alleluia-schets2.mxl -o generated\from-mxl.mvsa
mxl mvsa generated\alleluia-schets2.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl mvsa generated\alleluia-schets2.mxl --pitch vsa -o generated\from-mxl.vsa.mvsa
mvsa validate generated\from-mxl.mvsa
mxl mscz generated\alleluia-schets2.mxl -o generated\from-mxl.mscz
mxl validate content-source\bibliotheek\…\lied.mscz.mxl --profile satb
mxl normalize raw.mxl -o out.mxl --apply-timing
```

Via repo-script (zonder globale install):

```cmd
scripts\mxl.cmd -h
```

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mscz`](mscz.md) — bron `.mscz` (`mscz mvsa` / `mscz mxl`)
- [`vsa musicxml`](musicxml.md) — eenstemmig `.vsa` → MusicXML
- [`vsa text`](text.md) — platte gezongen tekst uit `.mxl` / `.musicxml` (zoekindex)
- [`vsa audio`](audio.md) — `.mscz` → mp3 via genormaliseerde playback-MXL
