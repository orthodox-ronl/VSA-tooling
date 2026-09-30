# `mxl` — conversies met MusicXML als bron

Top-level CLI voor bronbestanden `.mxl` / `.musicxml` / `.xml`.
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).
Playback-checklist:
[canonical-checklists — MXL](../../formats/canonical-checklists.md#checklist-mxl-coria--playback).

Alias voor import: [`vsa mvsa import`](mvsa.md#vsa-mvsa-import).

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
| `import`     | Importeer naar `.mvsa` (zelfde pad als `vsa mvsa import`).                                    |
| `mscz`       | Naar checklist-`.mscz`: eerst partituur-layout (SA/TB), dan MuseScore.                        |
| `validate`   | Lees-gate: M2/M8, Coria-importer-tags, meta (source ≠ licentie). Profiel `satb` of `mono`.    |
| `normalize`  | Schrijf playback-MXL: explode + piano + sanitize; met `--apply-timing` ook recite/pauzes.     |

## Voorbeelden

```cmd
mxl import generated\alleluia-schets2.mxl --pitch doremi -o generated\from-mxl.mvsa
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
- [`vsa audio`](audio.md) — `.mscz` → mp3 via genormaliseerde playback-MXL
