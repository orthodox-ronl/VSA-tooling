# `mxl` — conversies met MusicXML als bron

Top-level CLI voor bronbestanden `.mxl` / `.musicxml` / `.xml`.
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).
Playback-checklist:
[canonical-checklists — MXL](../../formats/canonical-checklists.md#checklist-mxl-coria--playback).

Alias voor import: [`vsa mvsa import`](mvsa.md#vsa-mvsa-import) (zelfde
SATB-parser, soft-wrap, holds, recite en `--pitch`-gedrag).
**Werkbank-bewerkvorm** — niet ongewijzigd als catalogusbron gebruiken. De
output begint met dezelfde waarschuwingsbanner als `mvsa import`.

## Synopsis

```text
mxl [-h] {import,mscz,validate,normalize} …
mxl import [-h] [-o OUTPUT] --pitch {doremi,a-g,vsa}
           [--octave-style {@oct,marker}] [--section SECTION] [--no-align] path
mxl mscz [-h] [-o OUTPUT] [--musescore PATH] path
mxl validate [-h] [--profile {satb,mono}] path
mxl normalize [-h] [-o OUTPUT] [--apply-timing] path
```

## Subcommando's

| Subcommando  | Doel                                                                                          |
| ------------ | --------------------------------------------------------------------------------------------- |
| `import`     | Importeer naar `.mvsa`: direct SATB P1–P4 (zelfde pad als `vsa mvsa import`).                 |
| `mscz`       | Naar checklist-`.mscz`: eerst partituur-layout (SA/TB), dan MuseScore.                        |
| `validate`   | Lees-gate: M2/M8/M18 (monofone parts), Coria-importer-tags, meta (source ≠ licentie). Profiel `satb` of `mono`. |
| `normalize`  | Schrijf playback-MXL: explode + piano + sanitize; met `--apply-timing` ook recite/pauzes.     |

**Import-opties** (`--pitch`, `--no-align`, soft-wrap ~80, eindankers bij
`vsa`, kuiser-normaalvorm): zie [`vsa mvsa import`](mvsa.md#vsa-mvsa-import).
Bij complexe lyrics soms `--no-align`; sync-telling blijft leidend.

## Voorbeelden

```cmd
mxl import generated\alleluia-schets2.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl import generated\alleluia-schets2.mxl --pitch vsa -o generated\from-mxl.vsa.mvsa
vsa mvsa validate generated\from-mxl.vsa.mvsa
mxl mscz generated\alleluia-schets2.mxl -o generated\from-mxl.mscz
mxl validate content-source\bibliotheek\…\lied.mscz.mxl --profile satb
mxl normalize raw.mxl -o out.mxl --apply-timing
```

Via repo-script (zonder globale install):

```cmd
scripts\mxl.cmd -h
```

## Zie ook

- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mscz`](mscz.md) — bron `.mscz` (`mscz mxl` gebruikt dezelfde normalize-keten)
- [`vsa musicxml`](musicxml.md) — eenstemmig `.vsa` → MusicXML
- [`vsa text`](text.md) — platte gezongen tekst uit `.mxl` / `.musicxml` (zoekindex)
- [`vsa audio`](audio.md) — `.mscz` → mp3 via genormaliseerde playback-MXL
