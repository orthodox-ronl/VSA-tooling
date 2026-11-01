# `mscz` — conversies met MuseScore als bron

Top-level CLI voor bronbestanden `.mscz`.
Conventie: **`mscz {doeltype}`** (bronextensie → doelextensie).
Zie het conversieplan:
[mvsa-conversions](../../plans/mvsa-conversions.md).

**`mscz mvsa`** maakt een **werkbank-bewerkvorm** — niet ongewijzigd als
catalogusbron gebruiken (woordstreepjes, lege recite, lossy layout). De
output begint met een ASCII-waarschuwingsbanner. Details:
[`.mvsa` — score naar mvsa](../../formats/mvsa.md#score-naar-mvsa).

**Straat-puur:** product-subs accepteren alleen `.mscz`. Andere bronnen:
`vsa …` / `mvsa …`. Universele productcatalogus:
[contract-index](../../formats/contract-index.md#universele-productcatalogus).

**Invoer:** `path` mag één `.mscz` **of** een map zijn (recursief). Bij
meerdere bronnen: sibling-output per bestand; `-o` alleen bij precies één
bron. Zie [Invoer bestand of map](input-pad.md).

## Synopsis

```text
mscz [-h] {mvsa,import,mxl,svg,pdf,mp3,ogg,wav,score-ir,mscz,normalize,text,compare,products} …
mscz mvsa [-h] [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}] [--do PITCH]
          [--octave-style {@oct,marker}] [--section SECTION]
          [--musescore PATH] [--no-align] path
mscz import [-h] [-o OUTPUT] [--layout PROFILE] […] path
mscz mxl|svg|pdf|mp3|ogg|wav|mscz|text [-h] [-o OUTPUT] [--musescore PATH] path
mscz score-ir [-h] [-o OUTPUT] [--musicxml [PATH]] [--musescore PATH] path
mscz normalize [-h] [-o OUTPUT] [--layout PROFILE] [--bibliotheek-id ID]
               [--compact] [Style-opties…] path
mscz compare [-h] [--musescore PATH] [--pitch FORM] [--strict-duration]
             score mvsa
mscz products [-h] [--force] [--dry-run] [--quiet] [--skip-svg] [--musescore PATH] path
```

## Subcommando's

| Subcommando       | Doel                                                                                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mvsa`            | Naar `.mvsa` (werkbank). Default: `<bronnaam>.mvsa`.                                                                                                          |
| `import`          | **Naar `.mscz`** uit `.mvsa`/MusicXML (= `mvsa mscz` / `mxl mscz`).                                                                                           |
| `products`        | **Universele** standaardset + `{stam}.mscz.products-meta.json`. Zie [products-meta](../../formats/products-meta.md).                                          |
| `mxl`             | Coria-`.mxl`; merget key `mxl`.                                                                                                                               |
| `svg`             | Kale tall compacte SVG (key `svg`). Niet via `mvsa svg`.                                                                                                     |
| `pdf`             | Print-PDF; merget `pdf`. Niet via `mvsa pdf`.                                                                                                                 |
| `mp3`/`ogg`/`wav` | Preview-audio; `mp3` merget key `mp3`.                                                                                                                        |
| `score-ir`        | Score-IR (+ `--musicxml` → from-ir); merget `score-ir` / `from-ir`.                                                                                           |
| `mscz`            | Partituur-sibling `*.mscz.mscz` (layout `partituur`); merget key `mscz`.                                                                                      |
| `normalize`       | Layoutprofiel in-place of `-o` (geen meta-product tenzij sibling via `mscz mscz`).                                                                            |
| `text`            | Lyrics-product `*.lyrics.txt`; merget key `lyrics`.                                                                                                           |
| `compare`         | Score (`.mscz` of MusicXML) ↔ `.mvsa`.                                                                                                                        |

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
mscz svg generated\alleluia-schets2.mscz -o generated\alleluia-schets2.svg
mscz pdf generated\alleluia-schets2.mscz -o generated\alleluia-schets2.pdf
mscz text generated\alleluia-schets2.mscz
mscz mp3 generated\alleluia-schets2.mscz --force
mscz score-ir generated\alleluia-schets2.mscz --musicxml
mscz products generated\alleluia-schets2.mscz --force
mscz compare generated\alleluia-schets2.mscz generated\alleluia-schets2.mscz.mvsa
mscz compare generated\from-mscz.mxl generated\from-mscz.mvsa
```

### `mscz svg` / `mscz pdf` / `mscz normalize`

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mscz.cmd svg generated\alleluia-schets2.mscz -o generated\alleluia-schets2.svg
scripts\mscz.cmd pdf generated\alleluia-schets2.mscz -o generated\alleluia-schets2.pdf
scripts\mscz.cmd normalize generated\alleluia-schets2.mscz --layout partituur
scripts\mscz.cmd normalize generated\alleluia-schets2.mscz -o generated\alleluia.partituur.mscz --compact
```

**`normalize`:** past het gekozen layoutprofiel toe op een bestaand `.mscz`
(zelfde nabewerking als na `mvsa mscz` / `mscz import`). Default: overschrijf
de bron; met `-o` schrijf je een kopie. Style-opties (`--compact`,
systeemafstand, fonts, …) gelden niet bij `--layout plain`.

Via repo-script:

```cmd
scripts\mscz.cmd -h
```

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [`text`](text.md) — platte tekst uit `.vsa` / `.mvsa` / MusicXML / `.mscz`
- [`mvsa`](mvsa.md) — bron `.mvsa` (`mvsa svg` / `mvsa pdf` alleen voor `.mvsa`)
- [`mxl`](mxl.md) — bron `.mxl` (`mxl mvsa` voor MusicXML → `.mvsa`)
- MSCZ-export vanuit mvsa: [`mvsa mscz`](mvsa.md#mvsa-mscz)
- Formaat: [`.mscz`](../../formats/mscz.md) · [score naar mvsa](../../formats/mvsa.md#score-naar-mvsa) · [mvsa-svg](../../formats/mvsa-svg.md)
