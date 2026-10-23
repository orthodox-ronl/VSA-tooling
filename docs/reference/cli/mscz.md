# `mscz` — conversies met MuseScore als bron

Top-level CLI voor bronbestanden `.mscz`.
Conventie: **`mscz {doeltype}`** (bronextensie → doelextensie).
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).

**`mscz mvsa`** maakt een **werkbank-bewerkvorm** — niet ongewijzigd als
catalogusbron gebruiken (woordstreepjes, lege recite, lossy layout). De
output begint met een ASCII-waarschuwingsbanner. Details:
[`.mvsa` — score naar mvsa](../../formats/mvsa.md#score-naar-mvsa).

Alias voor platte tekst: [`vsa text`](text.md) (zelfde extractie; ook
`.mxl` / `.vsa` / `.mvsa`).

**Invoer:** `path` mag één `.mscz` **of** een map zijn (recursief). Bij
meerdere bronnen: sibling-output per bestand; `-o` alleen bij precies één
bron. Zie [Invoer bestand of map](input-pad.md).

## Synopsis

```text
mscz [-h] {mvsa,mxl,text} …
mscz mvsa [-h] [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}] [--do PITCH]
          [--octave-style {@oct,marker}] [--section SECTION]
          [--musescore PATH] [--no-align] path
mscz mxl [-h] [-o OUTPUT] [--musescore PATH] path
mscz text [-h] [-o OUTPUT] [--musescore PATH] path
```

## Subcommando's

| Subcommando | Doel                                                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `mvsa`      | Naar `.mvsa` (MuseScore → temp `.mxl` → SATB-explode → parser). Default: `<bronnaam>.mvsa` (bijv. `lied.mscz.mvsa`).         |
| `mxl`       | Naar Coria-`.mxl`: MuseScore-export, daarna explode naar vier parts. Default: `<bronnaam>.mxl` (bijv. `lied.mscz.mxl`).      |
| `text`      | Platte gezongen tekst via temp-`.mxl` (geen `.mvsa`; zie [`vsa text`](text.md)).                                             |

**`mvsa`-opties** (`--pitch` default `ag-vsa`, `--do`, `--no-align`, soft-wrap,
eindankers bij `ag-vsa`/`vsa`, kuiser-normaalvorm): zie
[score naar mvsa](../../formats/mvsa.md#score-naar-mvsa). `@do` komt uit de
MuseScore-voortekening (`KeySig` / `concertKey`) tenzij je `--do` meegeeft.
De MSCZ-stap gebruikt dezelfde SATB-explode als `mscz mxl`. Default
`--section schets`.

## Voorbeelden

```cmd
mscz mvsa generated\alleluia-schets2.mscz
mscz mvsa generated\alleluia-schets2.mscz -o generated\from-mscz.mvsa
mscz mvsa generated\alleluia-schets2.mscz --pitch a-g --do F4 -o generated\from-mscz.mvsa
mscz mvsa generated\alleluia-schets2.mscz --pitch vsa -o generated\from-mscz.vsa.mvsa
mvsa validate generated\from-mscz.mvsa
mscz mxl generated\alleluia-schets2.mscz -o generated\from-mscz.mxl
mscz text generated\alleluia-schets2.mscz -o generated\alleluia.lyrics.txt
```

Via repo-script:

```cmd
scripts\mscz.cmd -h
```

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [`text`](text.md) — platte tekst uit `.vsa` / `.mvsa` / MusicXML / `.mscz`
- [`mvsa`](mvsa.md) — bron `.mvsa`
- [`mxl`](mxl.md) — bron `.mxl` (`mxl mvsa` voor MusicXML → `.mvsa`)
- MSCZ-export vanuit mvsa: [`mvsa mscz`](mvsa.md#mvsa-mscz)
