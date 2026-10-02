# `vsa text` — platte gezongen tekst

Haal de **woorden** uit een bronbestand, zonder notatie (geen EHM/ELM,
geen stempartijen). Bedoeld voor zoekindex en lyrics-producten — niet voor
bewerken.

## Synopsis

```text
vsa text [-h] [-o OUTPUT] [--musescore PATH] path
```

## Bronnen

| Extensie                         | Gedrag                                                                 |
| -------------------------------- | ---------------------------------------------------------------------- |
| `.vsa`                           | Directe extractie uit VSA-body.                                        |
| `.mvsa`                          | Directe extractie uit L-regel(s).                                      |
| `.mxl` / `.musicxml` / `.xml`    | Lyrics uit MusicXML (geen MuseScore nodig).                            |
| `.mscz`                          | Via tijdelijke MuseScore-`.mxl`; schrijft **geen** `.mvsa`-sibling.    |

Bestandsnamen zoals `{stam}.mscz.mxl` horen bij `.mxl` (laatste suffix).

### MusicXML-regel (SATB / partituur)

1. Neem de **eerste part** in documentvolgorde die lyrics met
   `number="1"` heeft (ontbrekend number telt als 1).
2. Negeer andere lyric-nummers (verzen) en chord-noten.
3. Bij meerdere voices in die part: alleen de laagste voice met lyrics
   (bij voorkeur voice 1), zodat lead-tekst niet verdubbelt uit A/T/B.
4. Lettergrepen (`single` / `begin` / `middle` / `end`) worden tot woorden
   samengevoegd; zachte streepjes verdwijnen, hard `=` wordt `-` (zelfde
   als bij `.vsa` / `.mvsa`).

Lege of lyric-loze scores geven een **lege string** (exitcode 0), net als
`vsa text` op een bron zonder gezongen tekst.

### `.mscz` zonder import-keten

`vsa text lied.mscz` (of `mscz text lied.mscz`) exporteert alleen via
MuseScore naar een temp-`.mxl` en leest daaruit. Er ontstaat geen
`{stam}.mscz.mvsa`. Voor catalogus-zoeken is een bestaande
`{stam}.mscz.mxl` vaak voldoende: `vsa text lied.mscz.mxl`.

## Opties

| Optie               | Betekenis                                                |
| ------------------- | -------------------------------------------------------- |
| `-o`, `--output`    | Schrijf naar bestand i.p.v. stdout (`Geschreven: …`).    |
| `--musescore PATH`  | MuseScore-executable (alleen bij `.mscz`; default auto). |

Geen stamp-header (`# vsa-source-sha256:`) in deze tooling — dat hoort bij
consumer lyrics-products.

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa text examples\minimal\001_plain_text.vsa
vsa text docs\specification-vsa-templates\library\tropaar-toon-4\examples\corpus\T4-01-johannes-voorloper.mxl
vsa text lied.mscz.mxl -o generated\lied.lyrics.txt
vsa text lied.mscz -o generated\lied.lyrics.txt
```

Alias voor alleen `.mscz`: [`mscz text`](mscz.md).

## Zie ook

- [`mscz`](mscz.md) — MuseScore-bron: import / mxl / text
- [`syllabify`](syllabify.md) — lettergreepstreepjes in `.vsa`
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
