# `vsa text` — platte gezongen tekst

Haal de **woorden** uit een `.vsa`, zonder notatie (geen EHM/ELM).
Bedoeld als lyrics-product en als **referentie** voor het veld
[`zoektekst`](../../formats/zoektekst.md) — niet voor bewerken van de
notatie.

De woorden komen uit de VSA-body, niet uit het veld `zoektekst`
(YAML-frontmatter wordt gestript). Zie
[zoektekst — tooling](../../formats/zoektekst.md#tooling).
Voor een `.mvsa`: [`mvsa text`](mvsa.md#mvsa-text). Voor een `.mscz`:
[`mscz text`](mscz.md).

## Synopsis

```text
vsa text [-h] [-o OUTPUT] path
```

**Invoer:** één `.vsa` of een map (recursief alle `.vsa`). Standaard
schrijft het commando `{stam}.vsa.lyrics.txt` naast de bron en meldt
`Geschreven:` plus `Meta:`. `-o` alleen bij precies één bestand. Zie
[Invoer bestand of map](input-pad.md).

## Bronnen

`vsa text` leest alleen een `.vsa`. Andere bronnen hebben een eigen
commando. Een verkeerde extensie stopt met een fout en noemt het
commando dat wel past.

| Bron                         | Commando        | Sibling                          |
| ---------------------------- | --------------- | -------------------------------- |
| `.vsa`                       | `vsa text`      | `{stam}.vsa.lyrics.txt`          |
| `.mvsa`                      | `mvsa text`     | `{stam}.mvsa.lyrics.txt`         |
| `.mscz`                      | `mscz text`     | `{stam}.mscz.lyrics.txt`         |
| `.md`                        | `markdown text` | zie [`markdown`](markdown.md)    |

`.mvsa`: de woorden komen uit de L-regels. Een systeembreuk
(`@mscz-newline`) is geen woordbreuk.

`.mscz`: `mscz text` gaat via een tijdelijke MuseScore-MusicXML en
schrijft geen `.mvsa` ernaast. De MusicXML-regels hieronder beschrijven
die keuze. `vsa text lied.mscz` weigert het bestand.

### MusicXML-regel (SATB / partituur)

1. Neem de **eerste part** in documentvolgorde die lyrics met
   `number="1"` heeft (ontbrekend number telt als 1).
2. Negeer andere lyric-nummers (verzen) en chord-noten.
3. Bij meerdere voices in die part: alleen de laagste voice met lyrics
   (bij voorkeur voice 1), zodat lead-tekst niet verdubbelt uit A/T/B.
4. Lettergrepen (`single` / `begin` / `middle` / `end`) worden tot woorden
   samengevoegd; zachte streepjes verdwijnen, hard `=` wordt `-` (zelfde
   als bij `.vsa` / `.mvsa`).
5. Coria-oefenlyric `[PAUZE]` wordt genegeerd (geen zoek-/lyrics-woord).

Lege of lyric-loze scores geven een **lege string** (exitcode 0), net als
`vsa text` op een bron zonder gezongen tekst.

### `.mscz` zonder import-keten

`mscz text lied.mscz` exporteert alleen via MuseScore naar een
tijdelijke MusicXML en leest daaruit. Er ontstaat geen
`{stam}.mscz.mvsa`.

## Opties

| Optie               | Betekenis                                                                      |
| ------------------- | ------------------------------------------------------------------------------ |
| `-o`, `--output`    | Ander pad dan de sibling `{stam}.vsa.lyrics.txt`. Alleen bij één bron.         |

Geen stamp-header (`# vsa-source-sha256:`) in deze tooling.
Editorzoeken in een canonieke `.vsa` of `.mvsa` gebruikt het veld
`zoektekst` in de bron — zie
[`zoektekst`](../../formats/zoektekst.md). Het sibling-bestand
`*.lyrics.txt` schrijft `{straat} text` of `{straat} products`
(standaardproduct, meta-key `lyrics`).

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa text examples\minimal\001_plain_text.vsa
mvsa text examples\mvsa\alleluia-toon-1.mvsa
mscz text lied.mscz -o generated\lied.mscz.lyrics.txt
```

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [Zoektekst in canonieke bron](../../formats/zoektekst.md)
- [`vsa zoektekst`](zoektekst.md) — veld vullen/controleren
- [`mscz`](mscz.md) — MuseScore-bron: import / mxl / text
- [`syllabify`](syllabify.md) — lettergreepstreepjes in `.vsa`
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
