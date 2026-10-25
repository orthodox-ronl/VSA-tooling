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
mscz [-h] {mvsa,import,mxl,text,compare,products} …
mscz mvsa [-h] [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}] [--do PITCH]
          [--octave-style {@oct,marker}] [--section SECTION]
          [--musescore PATH] [--no-align] path
mscz import [-h] [-o OUTPUT] [--layout PROFILE] […] path
mscz mxl [-h] [-o OUTPUT] [--musescore PATH] path
mscz text [-h] [-o OUTPUT] [--musescore PATH] path
mscz compare [-h] [--musescore PATH] [--pitch FORM] [--strict-duration]
             score mvsa
```

## Subcommando's

| Subcommando | Doel                                                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `mvsa`      | Naar `.mvsa` (MuseScore → temp `.mxl` → SATB-explode → parser). Default: `<bronnaam>.mvsa` (bijv. `lied.mscz.mvsa`).         |
| `import`    | **Naar `.mscz`** uit `.mvsa` of MusicXML (catalogus-vrij). Zelfde als [`mvsa mscz`](mvsa.md#mvsa-mscz) / `mxl mscz`. Toegestaan: `.mvsa`, `.mxl`, `.musicxml`, `.xml`. Contract: [contract-index](../../formats/contract-index.md), [MSCZ-leesbaarheid](../../formats/mscz-leesbaarheid.md). |
| `products`  | Coria-`.mxl` (+ SVG tenzij `--skip-svg`) + `{stam}.mscz.products-meta.json`. Flags: `--force`, `--dry-run`. |
| `mxl`       | Naar Coria-`.mxl`: MuseScore-export, daarna explode naar vier parts. Default: `<bronnaam>.mxl` (bijv. `lied.mscz.mxl`).      |
| `text`      | Platte gezongen tekst via temp-`.mxl` (geen `.mvsa`; zie [`vsa text`](text.md)).                                             |
| `compare`   | Controleer of een `.mvsa` nog overeenkomt met verse `mscz`/`mxl mvsa`-import (lyrics, toonhoogte, duur-info, import-gaten). |

**`mvsa`-opties** (`--pitch` default `ag-vsa`, `--do`, `--no-align`, soft-wrap,
eindankers bij `ag-vsa`/`vsa`, kuiser-normaalvorm): zie
[score naar mvsa](../../formats/mvsa.md#score-naar-mvsa). `@do` komt uit de
MuseScore-voortekening (`KeySig` / `concertKey`) tenzij je `--do` meegeeft.
De MSCZ-stap gebruikt dezelfde SATB-explode als `mscz mxl`. Default
`--section schets`.

### `mscz compare`

Controleert of een **`.mvsa`** (vaak `lied.mscz.mvsa`) nog overeenkomt met
wat **`mscz mvsa` / `mxl mvsa` nu** uit de score zou maken. Zo vermijd je
vals alarm door ruwe MusicXML-lettergrepen of asymmetrische duur-export.

Rapport:

1. **Lyrics** — platte tekst van een verse referentie-import versus de
   gegeven `.mvsa` (inhoud; rand-leestekens genegeerd).
2. **Melodie — toonhoogte** — per stem S/A/T/B (beide kanten via dezelfde
   `.mvsa`→MusicXML-export). Bepaalt samen met lyrics de exitcode.
3. **Melodie — duur** — pitch+duur (standaard informatief; met
   `--strict-duration` ook in de exitcode).
4. **Import-gaten** — `@tempo`, `@tekst`, `@speelplan`/`@blok`, `@composer`,
   `@title`, … in de score maar niet in dit `.mvsa`.

**Argumenten:** `score` (`.mscz`, of `.mxl` / `.musicxml` / `.xml`) en
`mvsa`. Optioneel `--musescore` (bij `.mscz`), `--pitch` (referentie-import;
default zoals `mscz mvsa`), `--strict-duration`.

Coria-playback-`.mxl` met `[PAUZE]`: waarschuwing; pauzematen worden voor
de vergelijking weggelaten. Liever `.mscz` als score.

**Exitcode:** `0` als lyrics-inhoud én toonhoogte kloppen; `1` bij verschil
of fout. Import-gaten veranderen de exitcode niet.

## Voorbeelden

```cmd
mscz mvsa generated\alleluia-schets2.mscz
mscz mvsa generated\alleluia-schets2.mscz -o generated\from-mscz.mvsa
mscz import examples\mvsa\1a-vredeslitanie.mvsa -o generated\from-mvsa.mscz
mscz mvsa generated\alleluia-schets2.mscz --pitch a-g --do F4 -o generated\from-mscz.mvsa
mscz mvsa generated\alleluia-schets2.mscz --pitch vsa -o generated\from-mscz.vsa.mvsa
mvsa validate generated\from-mscz.mvsa
mscz mxl generated\alleluia-schets2.mscz -o generated\from-mscz.mxl
mscz text generated\alleluia-schets2.mscz -o generated\alleluia.lyrics.txt
mscz compare generated\alleluia-schets2.mscz generated\alleluia-schets2.mscz.mvsa
mscz compare generated\from-mscz.mxl generated\from-mscz.mvsa
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
- Formaat: [`.mscz`](../../formats/mscz.md) · [score naar mvsa](../../formats/mvsa.md#score-naar-mvsa)
