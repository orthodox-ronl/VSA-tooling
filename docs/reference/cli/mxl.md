# `mxl` — conversies met MusicXML als bron

Top-level CLI voor bronbestanden `.mxl` / `.musicxml` / `.xml`.
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).

Alias voor import: [`vsa mvsa import`](mvsa.md#vsa-mvsa-import).

## Synopsis

```text
mxl [-h] {import,mscz} …
mxl import [-h] [-o OUTPUT] --pitch {doremi,abc,vsa}
           [--octave-style {@oct,marker}] [--section SECTION] [--no-align] path
mxl mscz [-h] [-o OUTPUT] [--musescore PATH] path
```

## Subcommando's

| Subcommando | Doel |
| ----------- | ---- |
| `import` | Importeer naar `.mvsa` (zelfde pad als `vsa mvsa import`). |
| `mscz` | Converteer naar `.mscz` via MuseScore CLI. |

## Voorbeelden

```cmd
mxl import generated\alleluia-schets2.mxl --pitch doremi -o generated\from-mxl.mvsa
mxl mscz generated\alleluia-schets2.mxl -o generated\from-mxl.mscz
```

Via repo-script (zonder globale install):

```cmd
scripts\mxl.cmd -h
```

## Zie ook

- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mscz`](mscz.md) — bron `.mscz`
- [`vsa musicxml`](musicxml.md) — eenstemmig `.vsa` → MusicXML
