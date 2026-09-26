# `mscz` — conversies met MuseScore als bron

Top-level CLI voor bronbestanden `.mscz`.
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).

Alias voor import: [`vsa mvsa import`](mvsa.md#vsa-mvsa-import) (zelfde
MSCZ→mxl→mvsa-keten).

## Synopsis

```text
mscz [-h] {import,mxl} …
mscz import [-h] [-o OUTPUT] --pitch {doremi,abc,vsa}
            [--octave-style {@oct,marker}] [--section SECTION]
            [--musescore PATH] [--no-align] path
mscz mxl [-h] [-o OUTPUT] [--musescore PATH] path
```

## Subcommando's

| Subcommando | Doel |
| ----------- | ---- |
| `import` | Importeer naar `.mvsa` (via MuseScore → temp `.mxl`). |
| `mxl` | Exporteer naar `.mxl` via MuseScore CLI. |

## Voorbeelden

```cmd
mscz import generated\alleluia-schets2.mscz --pitch abc -o generated\from-mscz.mvsa
mscz mxl generated\alleluia-schets2.mscz -o generated\from-mscz.mxl
```

Via repo-script:

```cmd
scripts\mscz.cmd -h
```

## Zie ook

- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mxl`](mxl.md) — bron `.mxl`
- MSCZ-export vanuit mvsa: [`vsa mvsa mscz`](mvsa.md#vsa-mvsa-mscz)
