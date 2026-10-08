# `mscz` — conversies met MuseScore als bron

Top-level CLI voor bronbestanden `.mscz`.
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).

Alias voor import: [`vsa mvsa import`](mvsa.md#vsa-mvsa-import) (zelfde
MSCZ→mxl→mvsa-keten).

Alias voor platte tekst: [`vsa text`](text.md) (zelfde extractie; ook
`.mxl` / `.vsa` / `.mvsa`).

## Synopsis

```text
mscz [-h] {import,mxl,text} …
mscz import [-h] [-o OUTPUT] --pitch {doremi,a-g,vsa}
            [--octave-style {@oct,marker}] [--section SECTION]
            [--musescore PATH] [--no-align] path
mscz mxl [-h] [-o OUTPUT] [--musescore PATH] path
mscz text [-h] [-o OUTPUT] [--musescore PATH] path
```

## Subcommando's

| Subcommando | Doel                                                                              |
| ----------- | --------------------------------------------------------------------------------- |
| `import`    | Importeer naar `.mvsa` (MuseScore → temp `.mxl` → SATB-explode → parser).         |
| `mxl`       | Naar Coria-`.mxl`: MuseScore-export, daarna explode naar vier parts.              |
| `text`      | Platte gezongen tekst via temp-`.mxl` (geen `.mvsa`; zie [`vsa text`](text.md)).  |

## Voorbeelden

```cmd
mscz import generated\alleluia-schets2.mscz --pitch a-g -o generated\from-mscz.mvsa
mscz mxl generated\alleluia-schets2.mscz -o generated\from-mscz.mxl
mscz text generated\alleluia-schets2.mscz -o generated\alleluia.lyrics.txt
```

Via repo-script:

```cmd
scripts\mscz.cmd -h
```

## Zie ook

- [`text`](text.md) — platte tekst uit `.vsa` / `.mvsa` / MusicXML / `.mscz`
- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mxl`](mxl.md) — bron `.mxl`
- MSCZ-export vanuit mvsa: [`vsa mvsa mscz`](mvsa.md#vsa-mvsa-mscz)
