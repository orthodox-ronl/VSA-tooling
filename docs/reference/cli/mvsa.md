# `mvsa` — meerstemmige .mvsa (draft)

Draft-tooling voor **mvsa**: meerstemmige tekstbronnen (`.mvsa`) met
lyrics-regels en stemregels. Normatieve draft-spec:
[specification-mvsa](../../specification-mvsa/README.md).

Dit is **niet** hetzelfde als [`vsa validate`](validate.md) /
[`vsa musicxml`](musicxml.md) voor eenstemmige `.vsa`.

**Commando:** `mvsa …` (console-script of `scripts\mvsa.cmd`).
Bron-commands voor andere formaten: [`mxl`](mxl.md), [`mscz`](mscz.md).

Subcommando’s zijn genoemd naar de **uitvoer** (zoals `mscz` / `pdf` /
`mp3` / `ogg` / `wav`). Oude namen `musicxml` en `audio` blijven als alias
werken (`audio` ≡ `mp3`).

**Invoer:** bij de meeste subcommando’s mag `path` één bronbestand **of**
een map zijn (recursief alle passende extensies). Bij meerdere bronnen
komt de uitvoer als sibling naast elk bronbestand; `-o` en vergelijkbare
enkelvoudige paden (`--keep-mxl`, …) zijn alleen toegestaan bij precies
één bronbestand. Overzicht: [Invoer bestand of map](input-pad.md).

## Synopsis

```text
mvsa [-h] {validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,normalize,transpose,kuiser,import,products} …
mvsa validate [-h] path
mvsa mxl [-h] [-o OUTPUT] [--section SECTION] [--hulptekst]
              [--hulptekst-as-parts] [--bibliotheek-id ID]
              [--musescore PATH] path
mvsa score-ir [-h] [-o OUTPUT] [--section SECTION] [--bibliotheek-id ID]
              [--musicxml [PATH]] path
mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
          [--keep-mxl PATH] [--layout PROFILE] [--bibliotheek-id ID]
          [--hulptekst] [--compact]
          [--min-system-distance SP] [--max-system-distance SP]
          [--staff-distance SP]
          [--page-margin-top MM] [--page-margin-bottom MM]
          [--lyrics-font FACE] [--lyrics-font-size PT]
          [--cue-font FACE] [--cue-font-size PT] path
mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
         [--keep-mscz PATH] [--keep-mxl PATH]
         [--layout PROFILE] [--bibliotheek-id ID] [--compact]
         [--min-system-distance SP] [--max-system-distance SP]
         [--staff-distance SP]
         [--page-margin-top MM] [--page-margin-bottom MM]
         [--lyrics-font FACE] [--lyrics-font-size PT]
         [--cue-font FACE] [--cue-font-size PT] path
mvsa svg [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
         [--keep-mscz PATH] [--keep-mxl PATH] [--no-trim] [--transparent]
         [--engine {musescore,osmd}] [--compact]
         [--min-system-distance SP] [--max-system-distance SP]
         [--staff-distance SP]
         [--page-margin-top MM] [--page-margin-bottom MM]
         [--lyrics-font FACE] [--lyrics-font-size PT]
         [--cue-font FACE] [--cue-font-size PT] path   # path: .mvsa
mvsa mp3 [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
           [--keep-mxl PATH] path
mvsa ogg [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
           [--keep-mxl PATH] path
mvsa wav [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
           [--keep-mxl PATH] path
mvsa normalize [-h] [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa,ag-vsa}] …
mvsa transpose [-h] --to TONIC [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}] …
mvsa kuiser [-h] [-o OUTPUT] [--check] [--pitch {preserve,doremi,a-g,vsa,ag-vsa}] …
```

## Subcommando's

| Subcommando                            | Doel                                                                                                              |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| [`validate`](#mvsa-validate)           | Structuur + sync-telling van `.mvsa` controleren.                                                                 |
| [`mxl`](#mvsa-mxl)                     | Exporteer `.mvsa` / `.mscz` / `.mxl` naar playback-``.mxl``. Bij bron `.mvsa`: merget key `mxl` in products-meta. |
| [`score-ir`](#mvsa-score-ir)           | Exporteer `.mvsa` naar Score-IR JSON (partituur; scherm/CoriB). Merget `score-ir` (+ `from-ir` bij `--musicxml`). |
| [`mscz`](#mvsa-mscz)                   | Exporteer `.mvsa` naar MuseScore (`.mscz`).                                                                       |
| [`pdf`](#mvsa-pdf)                     | Exporteer `.mvsa` naar print-PDF (zangers). Merget key `pdf`. Bron `.mscz`: [`mscz pdf`](mscz.md).                |
| [`svg`](#mvsa-svg)                     | Exporteer `.mvsa` naar muziek-only partituur-SVG (koormap). Merget `svg` / `svg-N`.                               |
| [`mp3`](#mvsa-mp3) / `ogg` / `wav`     | Exporteer naar preview-audio (``.mp3`` / ``.ogg`` / ``.wav``).                                                    |
| [`normalize`](#mvsa-normalize)         | Canoniseer `.mvsa` (default: behoud noteernamen).                                                                 |
| [`transpose`](#mvsa-transpose)         | Transponeer naar een andere tonica (`@do`); `@mode` blijft.                                                       |
| [`kuiser`](#mvsa-kuiser)               | Authoring-kuiser: strepen syncen, woordstreep, align.                                                             |
| [`import`](#mvsa-import)               | Score/MusicXML → werkbank-`.mvsa` (catalogus-vrij; = `mscz`/`mxl mvsa`).                                          |
| [`products`](#mvsa-products)           | Standaardproducten + `*.products-meta.json` (versheid).                                                           |

Hulp op de commandoregel:

```cmd
mvsa -h
mvsa validate -h
mvsa mxl -h
mvsa score-ir -h
mvsa mscz -h
mvsa pdf -h
mvsa svg -h
mvsa mp3 -h
mvsa ogg -h
mvsa wav -h
mvsa normalize -h
mvsa transpose -h
mvsa kuiser -h
```

---

## `mvsa validate`

### Synopsis

```text
mvsa validate [-h] [--require-zoektekst] path
```

### Beschrijving

Controleert `.mvsa`-bestanden op LSATB-structuur, maatstrepen en de
[sync-telling](../../specification-mvsa/semantics.md#sync-contract-lengte-posities)
tussen lyrics-regels en stemregels. Draft-validatie: zie
[specification-mvsa/validation.md](../../specification-mvsa/validation.md).

| `path`-type     | Gedrag                                               |
| --------------- | ---------------------------------------------------- |
| `.mvsa`-bestand | Valideert dat ene bestand.                           |
| Map             | Zoekt recursief naar alle `.mvsa`-bestanden eronder. |

### Argumenten en opties

| Naam                   | Verplicht | Betekenis                                                                        | Default | Beperkingen   |
| ---------------------- | --------- | -------------------------------------------------------------------------------- | ------- | ------------- |
| `path`                 | Ja        | `.mvsa`-bestand of map met `.mvsa`-bestanden.                                    | —       | Moet bestaan. |
| `--require-zoektekst`  | Nee       | Eis YAML-`zoektekst` gelijk aan body (catalogus); zie [zoektekst](zoektekst.md). | Uit     | —             |
| `-h`, `--help`         | Nee       | Toon hulp voor dit subcommando.                                                  | —       | —             |

### Output

- **stdout**: bij succes zonder warnings de tekst `OK` (één keer, ook bij
  een map); warnings naar stdout.
- **stderr**: errors (`ERROR: …`) en samenvatting bij falen.
- Geen bestanden aangemaakt.
- Geen per-bestand `…: OK`-regels (zelfde stijl als [`vsa validate`](validate.md)).

### Exit status

| Exitcode | Betekenis                                      |
| -------- | ---------------------------------------------- |
| `0`      | Alle gevonden `.mvsa`-bestanden geldig.        |
| `1`      | Pad ontbreekt, geen `.mvsa`, of validatiefout. |

### Voorbeelden

```cmd
mvsa validate examples\mvsa
mvsa validate examples\mvsa\alleluia-toon-8.mvsa
mvsa validate examples\mvsa\alleluia-toon-8.mvsa --require-zoektekst
```

Voor alleen vullen/checken van `zoektekst` zonder overige validate:
[`vsa zoektekst`](zoektekst.md).

---

## `mvsa mxl`

### Synopsis

```text
mvsa mxl [-h] [-o OUTPUT] [--section SECTION] [--hulptekst]
                  [--hulptekst-as-parts] [--bibliotheek-id ID]
                  [--musescore PATH] path
```

### Beschrijving

Schrijft een **Coria-playback-``.mxl``** (of `.musicxml`/`.xml`). Bron:

| Bron                          | Gedrag                                                                      |
| ----------------------------- | --------------------------------------------------------------------------- |
| `.mvsa`                       | SATB-export (vier parts). Optioneel `--section` / hulptekst-vlaggen.        |
| `.mscz`                       | MuseScore → playback-normalisatie (zelfde keten als [`mscz mxl`](mscz.md)). |
| `.mxl` / `.musicxml` / `.xml` | Normaliseer naar playback (SATB-explode, Coria-sanitize).                   |

Bij `.mvsa`: zonder `--section` gaan alle `@sectie`-blokken achter elkaar in
één partituur; met `--section` alleen die sectie-id.

Kale `-` op een stemregel aan het begin van een nieuw LSATB-systeem houdt de
lopende toon van het vorige systeem (soft-wrap); een beginanker of expliciete
`@start`-toewijzing reset die toon. Bij `@speelplan` volgt die keten de
klinkende vorm. Zie
[lopende toon over systeemovergangen](../../specification-mvsa/semantics.md#lopende-toon-over-systeemovergangen).
Lege recite met ELM-keten (`()~&~&.…`, lyric-loos melisma uit import) wordt
als gewoon melisma geëxporteerd (alle slots/duur), niet als één noot.

Playback (Coria): standaard vier parts S/A/T/B met **piano** op elke partij
([checklist M8](../../formats/canonical-checklists.md#checklist-mxl-coria-playback)).
Stemidentifiers in het `.mvsa`-bestand (`Sop:`, `cantus:`, …) worden op dit
pad als part-namen gebruikt (SATB-letters → Soprano/Alto/Tenor/Bass).

**Hulptekst** (kerkslavisch ↔ Latijn / Nederlands ↔ Cyrillisch, parochieschema):

| Vlag                   | Wie               | Effect                                                                                                                                                                                                                   |
| ---------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--hulptekst`          | Blad én Coria-MXL | Lyric number 2 onder dezelfde noten (transliteratie). Handmatige `L1` wint als lyric 2 al bestaat.                                                                                                                       |
| `--hulptekst-as-parts` | Alleen Coria-MXL  | Extra parts: zelfde pitches, lyrics van laag 2; part-namen `{stem} ({label})`. Labels uit `@taal` (zie [keywords — @taal](../../specification-mvsa/keywords.md#taal)). Volume 0 op hulp-parts. Impliceert `--hulptekst`. |

Richting en Coria-labels sturen met sticky `@taal` (`nl` / `ksl` / `auto`, of
`Lap=aap Lus=noot` op lyrics-ids). Zie
[kerkslavisch-transliteratie](../../plans/kerkslavisch-transliteratie.md).

Dit is een **aparte** exporter dan [`vsa musicxml`](musicxml.md) (eenstemmig
VSA).

### Argumenten en opties

| Naam                   | Verplicht | Betekenis                                                                 | Default                                      | Beperkingen                           |
| ---------------------- | --------- | ------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------- |
| `path`                 | Ja        | Bron: `.mvsa`, `.mscz` of `.mxl`/`.musicxml`, of map met zulke bestanden. | —                                            | Moet bestaan.                         |
| `-o`, `--output`       | Nee       | Uitvoerpad (`.mxl`, `.musicxml` of `.xml`).                               | `<bronnaam>.mxl` (bijv. `lied.mvsa.mxl`)     | Alleen bij één bron; anders → `.mxl`. |
| `--section SECTION`    | Nee       | Alleen bij `.mvsa`: deze `@sectie`-id.                                    | Alle secties                                 | Id moet in het bestand voorkomen.     |
| `--bibliotheek-id ID`  | Nee       | Alleen bij `.mvsa`: bibliotheek-id in identification/rights.              | pad-sniff onder `content-source/bibliotheek` | Optioneel.                            |
| `--hulptekst`          | Nee       | Alleen bij `.mvsa`: tweede lyric-laag (number=2).                         | uit                                          | Zie beschrijving hierboven.           |
| `--hulptekst-as-parts` | Nee       | Alleen bij `.mvsa`: Coria-extra parts met hulptekst (volume 0).           | uit                                          | Impliceert `--hulptekst`.             |
| `--musescore PATH`     | Nee       | Alleen bij `.mscz`: pad naar MuseScore.                                   | auto-detectie                                | —                                     |
| `-h`, `--help`         | Nee       | Toon hulp voor dit subcommando.                                           | —                                            | —                                     |

### Output

- **stdout**: `Geschreven: <pad>` bij succes.
- **stderr**: validatie- of exportfouten.
- **bestand**: `.mxl` (standaard) of het pad uit `-o`.

### Exit status

| Exitcode | Betekenis                                              |
| -------- | ------------------------------------------------------ |
| `0`      | MusicXML succesvol geschreven.                         |
| `1`      | Bestand ontbreekt, validatiefout, of exportfout.       |

### Voorbeelden — succes

Standaard naast het bronbestand (`….mvsa.mxl`):

```cmd
mvsa mxl examples\mvsa\kleine-intocht-zondag-hemelum.mvsa
```

Met expliciet uitvoerpad en één sectie:

```cmd
mvsa mxl examples\mvsa\kleine-intocht-zondag-hemelum.mvsa --section schets-a-bladcijfer -o generated\intocht-a.mxl
```

Coria met keuze tussen lyrics-lagen (trisagion, kerkslavische sectie):

```cmd
mvsa mxl examples\mvsa\trisagion-8a-slav-hemelum.mvsa --section ksl --hulptekst-as-parts -o generated\trisagion-ksl-coria.mxl
```

Vanuit MuseScore-partituur (zelfde resultaat als `mscz mxl`):

```cmd
mvsa mxl examples\bug-cases\cherubijnenhymne-15c-kastorski-hemelum.mscz -o generated\bug-cases\cherubijnen.mxl
```

Blad/MSCZ: lyric 2 op partituur-MXL (keten via `mscz --hulptekst`):

```cmd
mvsa mscz examples\mvsa\hulptekst-ksl-mini.mvsa --hulptekst -o generated\hulptekst-ksl.mscz
```

### Voorbeelden — falen

Onbekende sectie-id of sync-fout in het `.mvsa`-bestand levert exitcode `1`
en diagnostiek op stderr. Controleer eerst met `mvsa validate`.

---

## `mvsa score-ir`

Exporteer `.mvsa` naar **Score-IR** JSON (`format: score-ir`, `profile: partituur`):
maten met SA/TB-voices, lyrics en `@tekst`-cues. Bedoeld voor gedeelde
schermweergave (koormap-SVG / CoriB). Contract:
[partituur-ir](../../plans/partituur-ir.md). Alias: `ir`.

Optioneel ``--musicxml``: schrijf partituur-MusicXML **uit** die Score-IR
(OSMD-brug; module `vsa.score_ir_musicxml`). Zonder pad: sibling
``lied.mvsa.from-ir.musicxml`` (ook bij een map). Met pad: alleen bij één
bron. Spike: `examples/spikes/partituur-browser/`. Brugcontract:
[partituur-ir §7](../../plans/partituur-ir.md).

S8-recite in from-ir: spacers krijgen ``<notehead>none</notehead>`` als
**marker** voor de scherm-OSMD-adapter (contract A1). OSMD verbergt die kop
niet uit XML alleen — zie
[osmd-s8-recite](../../plans/osmd-s8-recite.md) en
[score-ir](../../formats/score-ir.md).

Het eerste ``@tempo`` in het ``.mvsa``-bestand komt in Score-IR als
``meta.tempo`` en in from-ir MusicXML als ``<sound tempo="…"/>`` (standaard
130 BPM als er geen ``@tempo`` staat).

### Synopsis

```text
mvsa score-ir [-h] [-o OUTPUT] [--section SECTION] [--bibliotheek-id ID]
                  [--musicxml [PATH]] path
```

### Argumenten

| Argument / optie       | Betekenis                                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| `path`                 | Bron-``.mvsa`` of map met ``.mvsa``-bestanden.                                                     |
| `-o` / `--output`      | Uitvoer-``.json``. Default: sibling ``lied.mvsa.score-ir.json``. Alleen bij één bron.              |
| `--section SECTION`    | Alleen deze ``@sectie``-id.                                                                        |
| `--bibliotheek-id ID`  | Zet ``meta.bibliotheekId``.                                                                        |
| `--musicxml [PATH]`    | Extra: MusicXML uit Score-IR. Zonder ``PATH``: sibling ``lied.mvsa.from-ir.musicxml`` (ook map).   |

### Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa --musicxml
mvsa score-ir examples\mvsa --musicxml
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a-vredeslitanie.score-ir.json
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o examples\spikes\partituur-browser\score.score-ir.json --musicxml examples\spikes\partituur-browser\score.musicxml
```

### Exit status

| Exitcode | Betekenis                                        |
| -------- | ------------------------------------------------ |
| `0`      | JSON succesvol geschreven.                       |
| `1`      | Bestand ontbreekt, validatiefout, of exportfout. |

---

## `mvsa mscz`

### Synopsis

```text
mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
              [--keep-mxl PATH] [--layout PROFILE] [--bibliotheek-id ID]
              [--hulptekst] [--compact] [--min-system-distance SP]
              [--max-system-distance SP] [--staff-distance SP]
              [--page-margin-top MM] [--page-margin-bottom MM]
              [--lyrics-font FACE] [--lyrics-font-size PT]
              [--cue-font FACE] [--cue-font-size PT] path
```

### Beschrijving

Exporteert **één** `.mvsa`-bestand naar MuseScore (`.mscz`) via de keten:

```text
.mvsa  →  .mxl (partituur: SA/TB, lege part-namen)  →  MuseScore CLI  →  .mscz
       →  layoutprofiel (default: partituur)
```

Layoutprofielen (na MuseScore-conversie):

| Profiel      | Gedrag                                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------------------------- |
| `partituur`  | **Default.** A4, leesbaarheid, lege partijnamen, colofon — [MSCZ-leesbaarheid](../../formats/mscz-leesbaarheid.md). |
| `muziek`     | Zelfde leesbaarheid **zonder** titel/footer/colofon — voor [`mvsa svg`](#mvsa-svg) / koormap-embed.                 |
| `plain`      | Geen nabewerking door VSA-tooling (ruwe MuseScore-output van de partituur-MXL).                                     |

`--bibliotheek-id` zet de id in het colofon (**alleen** bij `partituur`).
Zonder die optie mag tooling de id uit het pad afleiden als
`…/bibliotheek/<zangstuk>/<variant>/<uitvoeringsvorm>/…` — consumers horen
de id **expliciet** te geven. Zie
[ownership](../../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

Dit voldoet bij `partituur` aan de [MSCZ-checklist](../../formats/canonical-checklists.md#checklist-mscz-partituur-musescore)
(twee balken, geen S/Soprano-labels). Voor Coria-playback (vier parts)
blijft [`mvsa mxl`](#mvsa-mxl) het primaire pad.

Vereist MuseScore 4 (of 3): op `PATH` als `MuseScore4` / `mscore`, of het
standaard Windows-pad
`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`. Override met
`--musescore`.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                         | Verplicht | Betekenis                                                                                                                       | Default                                    |
| ---------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `path`                       | Ja        | Bron-`.mvsa`-bestand of map met `.mvsa`-bestanden.                                                                              | —                                          |
| `-o`, `--output`             | Nee       | Uitvoer-`.mscz` (alleen bij precies één bronbestand).                                                                           | `<bronnaam>.mscz` (bijv. `lied.mvsa.mscz`) |
| `--section SECTION`          | Nee       | Alleen deze `@sectie`-id.                                                                                                       | Alle secties                               |
| `--musescore PATH`           | Nee       | Pad naar MuseScore-executable.                                                                                                  | Auto-detectie                              |
| `--keep-mxl PATH`            | Nee       | Bewaar ook het tussenliggende `.mxl`.                                                                                           | temp (wordt verwijderd)                    |
| `--layout PROFILE`           | Nee       | `partituur`, `muziek` of `plain`.                                                                                               | `partituur`                                |
| `--bibliotheek-id ID`        | Nee       | Colofon-id (profiel `partituur`); anders pad-fallback.                                                                          | pad-sniff / geen                           |
| `--hulptekst`                | Nee       | Tweede lyric-laag in tussen-MXL (blad «tweede regel»).                                                                          | uit                                        |
| `--compact`                  | Nee       | Dichtste Style-baseline (systeem 7/7, lyric 0.1, marge 5 mm, maat-spreiding 1.6); andere Style-opties winnen; niet bij `plain`. | uit                                        |
| `--min-system-distance SP`   | Nee       | Min. afstand tussen systemen (Style spatium); niet bij `plain`.                                                                 | `8` (bij `--compact`: `7`)                 |
| `--max-system-distance SP`   | Nee       | Max. afstand tussen systemen (Style spatium); niet bij `plain`.                                                                 | `14` (bij `--compact`: `7`)                |
| `--staff-distance SP`        | Nee       | Afstand tussen balken in één systeem (+ accolade); niet bij `plain`.                                                            | MuseScore + lyrics                         |
| `--page-margin-top MM`       | Nee       | Bovenmarge in mm (Style); niet bij `plain`.                                                                                     | `15`                                       |
| `--page-margin-bottom MM`    | Nee       | Ondermarge in mm (Style); niet bij `plain`.                                                                                     | `15`                                       |
| `--lyrics-font FACE`         | Nee       | Lettertype zangtekst; niet bij `plain`.                                                                                         | `Source Sans 3`                            |
| `--lyrics-font-size PT`      | Nee       | Puntgrootte zangtekst; niet bij `plain`.                                                                                        | `13`                                       |
| `--cue-font FACE`            | Nee       | Lettertype cues (`@tekst`); niet bij `plain`.                                                                                   | `Source Sans 3`                            |
| `--cue-font-size PT`         | Nee       | Puntgrootte cues; niet bij `plain`.                                                                                             | `12`                                       |
| `--measure-spacing F`        | Nee       | Horizontale maat-spreiding (Style); niet bij `plain`.                                                                           | `1.2` (bij `--compact`: `1.6`)             |

### Output

- **stdout**: `Geschreven: <pad>` (en `MXL: …` bij `--keep-mxl`).
- **bestand**: `.mscz` (zip met `.mscx`).

### Exit status

| Exitcode | Betekenis                                                            |
| -------- | -------------------------------------------------------------------- |
| `0`      | MSCZ geschreven.                                                     |
| `1`      | Pad ontbreekt, validatiefout, MuseScore ontbreekt, of conversiefout. |

### Voorbeelden

```cmd
mvsa mscz examples\mvsa\alleluia-toon-8.canonieke.mvsa
mvsa mscz lied.mvsa -o generated\lied.mscz --section schets2-oct-doremi
mvsa mscz lied.mvsa -o out.mscz --keep-mxl generated\lied.mxl
mvsa mscz lied.mvsa -o out.mscz --layout partituur --bibliotheek-id zangstuk/var/uv
mvsa mscz lied.mvsa -o raw.mscz --layout plain
mvsa mscz lied.mvsa -o out.mscz --min-system-distance 10 --max-system-distance 18
mvsa mscz lied.mvsa -o out.mscz --compact
mvsa mscz lied.mvsa -o out.mscz --compact --min-system-distance 9 --max-system-distance 9
mvsa mscz lied.mvsa -o out.mscz --staff-distance 4.5
mvsa mscz lied.mvsa -o out.mscz --page-margin-top 5 --page-margin-bottom 5
mvsa mscz lied.mvsa -o out.mscz --lyrics-font-size 14 --cue-font-size 11
mvsa mscz lied.mvsa -o out.mscz --measure-spacing 1.8
```

Style-overrides (incl. `--compact`) worden naar `.mscx` **én** `score_style.mss`
geschreven (MuseScore 4). Details: [`.mscz`](../../formats/mscz.md).


---

## `mvsa pdf`

### Synopsis

```text
mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
             [--keep-mscz PATH] [--keep-mxl PATH]
             [--layout PROFILE] [--bibliotheek-id ID] [--compact]
             [--min-system-distance SP] [--max-system-distance SP]
             [--staff-distance SP]
             [--page-margin-top MM] [--page-margin-bottom MM]
             [--lyrics-font FACE] [--lyrics-font-size PT]
             [--cue-font FACE] [--cue-font-size PT] path
```

### Beschrijving

Maakt een **print-PDF** van de partituur (voor zangers), via MuseScore CLI.
Alleen bron **`.mvsa`**. Voor een bestaand `.mscz`: [`mscz pdf`](mscz.md).

| Bron    | Pad                                                                      |
| ------- | ------------------------------------------------------------------------ |
| `.mvsa` | Keten: partituur-`.mxl` → `.mscz` (`--layout`) → `.pdf`                  |

`--layout` / `--bibliotheek-id` / Style-opties (`--compact`, systeem-/stafafstand,
pagina-marges, fonts) hebben dezelfde betekenis als bij
[`mscz`](#mvsa-mscz); andere Style-vlaggen winnen van `--compact`.

**Canoniek:** A4 staand (checklist
[PDF P6](../../formats/canonical-checklists.md#checklist-pdf-afgeleide-van-mscz));
via MuseScore-Style van het `.mscz` (MSCZ S7). US Letter is niet canoniek.

Dit is **niet** [`markdown pdf`](markdown.md#markdown-pdf) (Markdown + VSA-SVG via browser; wél
dezelfde A4-eis P6).

### Argumenten en opties

| Naam                         | Verplicht | Betekenis                                                                      | Default                                  |
| ---------------------------- | --------- | ------------------------------------------------------------------------------ | ---------------------------------------- |
| `path`                       | Ja        | `.mvsa`, of map met `.mvsa`-bestanden.                                         | —                                        |
| `-o`, `--output`             | Nee       | Uitvoer-`.pdf` (alleen bij precies één bronbestand).                           | `<bronnaam>.pdf` (bijv. `lied.mvsa.pdf`) |
| `--section`                  | Nee       | Eén `@sectie`-id.                                                              | alle secties                             |
| `--musescore`                | Nee       | MuseScore-executable.                                                          | auto-detectie                            |
| `--keep-mscz`                | Nee       | Bewaar tussenliggende `.mscz`.                                                 | temp (wordt verwijderd)                  |
| `--keep-mxl`                 | Nee       | Bewaar tussenliggende `.mxl`.                                                  | niet                                     |
| `--layout PROFILE`           | Nee       | `partituur` of `plain`.                                                        | `partituur`                              |
| `--bibliotheek-id ID`        | Nee       | Bij `partituur`: colofon-id.                                                   | pad-sniff / geen                         |
| `--compact`                  | Nee       | Dichtste Style-baseline; andere Style-opties winnen (zie `mscz`).              | uit                                      |
| `--min-system-distance SP`   | Nee       | Min. systeemafstand (zie `mscz`).                                              | `8`                                      |
| `--max-system-distance SP`   | Nee       | Max. systeemafstand (zie `mscz`).                                              | `14`                                     |
| `--staff-distance SP`        | Nee       | Stafafstand in één systeem (zie `mscz`).                                       | MuseScore + lyrics                       |
| `--page-margin-top MM`       | Nee       | Bovenmarge in mm (zie `mscz`).                                                 | `15`                                     |
| `--page-margin-bottom MM`    | Nee       | Ondermarge in mm (zie `mscz`).                                                 | `15`                                     |
| `--lyrics-font FACE`         | Nee       | Lettertype zangtekst (zie `mscz`).                                             | `Source Sans 3`                          |
| `--lyrics-font-size PT`      | Nee       | Puntgrootte zangtekst (zie `mscz`).                                            | `13`                                     |
| `--cue-font FACE`            | Nee       | Lettertype cues (zie `mscz`).                                                  | `Source Sans 3`                          |
| `--cue-font-size PT`         | Nee       | Puntgrootte cues (zie `mscz`).                                                 | `12`                                     |
| `--measure-spacing F`        | Nee       | Maat-spreiding (zie `mscz`).                                                   | `1.2` (compact: `1.6`)                   |

### Voorbeelden

```cmd
mvsa pdf examples\mvsa\alleluia-toon-1.mvsa
mvsa pdf lied.mvsa -o generated\lied.pdf --keep-mscz generated\lied.mscz
mvsa pdf lied.mvsa --layout partituur --bibliotheek-id zangstuk/var/uv
mvsa pdf lied.mvsa -o generated\lied.pdf --page-margin-top 5 --page-margin-bottom 5
mvsa pdf lied.mvsa --compact
mvsa pdf lied.mvsa --compact --min-system-distance 9 --max-system-distance 9
mscz pdf lied.mscz -o lied.pdf
```

---

## `mvsa svg`

Exporteer **`.mvsa`** naar partituur-SVG voor koormap-pagina’s. Voor bron
`.mscz`: [`mscz svg`](mscz.md). Default: MuseScore tall-SVG (print/fallback).
Optioneel `--engine osmd`: Score-IR → from-ir MusicXML → headless OSMD
([`scripts/osmd-svg`](../../../scripts/osmd-svg/)). Formaatpagina:
[mvsa-svg](../../formats/mvsa-svg.md).

### Synopsis

```text
mvsa svg [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
             [--keep-mscz PATH] [--keep-mxl PATH] [--no-trim]
             [--transparent] [--engine {musescore,osmd}]
             [--bibliotheek-id ID] [--compact]
             [--min-system-distance SP] [--max-system-distance SP]
             [--staff-distance SP]
             [--page-margin-top MM] [--page-margin-bottom MM]
             [--lyrics-font FACE] [--lyrics-font-size PT]
             [--cue-font FACE] [--cue-font-size PT] path
```

### Keten

| Engine       | Pad                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------- |
| `musescore`  | partituur-MXL → MSCZ (layout ``muziek``) → MuseScore SVG → trim (**default**)               |
| `osmd`       | Score-IR → from-ir MusicXML → headless OSMD (Node; geen MuseScore/Style-CLI)                |

Bij `musescore`: **één tall-SVG** (compact Style) — scherm-fallback én
bouwsteen voor `index.md.pdf`. Zie
[kale-muziek-svg-en-uitgaven](../../plans/kale-muziek-svg-en-uitgaven.md).
Bij `osmd`: optioneel bestand voor inspectie/scherm; site-embed blijft
Score-IR/OSMD in de browser.

### Argumenten

| Naam                         | Betekenis                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------------------- |
| `path`                       | Bron-``.mvsa``, of map met ``.mvsa``-bestanden.                                           |
| `-o` / `--output`            | Uitvoer-``.svg``. Default: sibling ``lied.mvsa.svg``. Alleen bij één bron.                |
| `--section`                  | Deze ``@sectie``-id.                                                                      |
| `--engine`                   | `musescore` (default) of `osmd`.                                                          |
| `--musescore`                | MuseScore-executable (alleen `musescore`-engine).                                         |
| `--keep-mscz`                | Bewaar tussenliggende ``.mscz`` (alleen `musescore`).                                     |
| `--keep-mxl`                 | `musescore`: partituur-``.mxl``; `osmd`: from-ir ``.musicxml``.                           |
| `--no-trim`                  | Sla viewBox-trim over (alleen `musescore`).                                               |
| `--transparent`              | Geen witte achtergrond na trim (alleen `musescore`).                                      |
| `--bibliotheek-id`           | Genegeerd voor layout ``muziek`` / OSMD-chrome.                                           |
| `--compact`                  | Compact-baseline (alleen `musescore`; default voor die engine).                           |
| `--min-system-distance SP`   | Min. systeemafstand (alleen `musescore`).                                                 |
| `--max-system-distance SP`   | Max. systeemafstand (alleen `musescore`).                                                 |
| `--staff-distance SP`        | Stafafstand in één systeem (alleen `musescore`).                                          |
| `--page-margin-top MM`       | Bovenmarge in mm (alleen `musescore`).                                                    |
| `--page-margin-bottom MM`    | Ondermarge in mm (alleen `musescore`).                                                    |
| `--lyrics-font FACE`         | Lettertype zangtekst (alleen `musescore`).                                                |
| `--lyrics-font-size PT`      | Puntgrootte zangtekst (alleen `musescore`).                                               |
| `--cue-font FACE`            | Lettertype cues/`@tekst` (alleen `musescore`).                                            |
| `--cue-font-size PT`         | Puntgrootte cues (alleen `musescore`).                                                    |
| `--measure-spacing F`        | Maat-spreiding (alleen `musescore`).                                                      |

### Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek.svg
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --lyrics-font-size 14 --cue-font-size 11
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --measure-spacing 1.8
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --compact
cd scripts\osmd-svg && npm install && npx puppeteer browsers install chrome
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-osmd.svg --engine osmd
mscz svg generated\spike-mscz\1a.mscz -o generated\spike-svg\1a-from-mscz.svg
```

### Exit status

| Exitcode | Betekenis                                                              |
| -------- | ---------------------------------------------------------------------- |
| `0`      | SVG succesvol geschreven.                                              |
| `1`      | Bestand ontbreekt, validatie-, MuseScore-/OSMD- of trimfout.           |

---

## `mvsa mp3` / `ogg` / `wav`

### Synopsis

```text
mvsa mp3 [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
               [--keep-mxl PATH] path
mvsa ogg [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
               [--keep-mxl PATH] path
mvsa wav [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
               [--keep-mxl PATH] path
```

### Beschrijving

Maakt een **preview-audiobestand** via MuseScore: eerst playback-``.mxl``
(vier parts), daarna audio. Het **subcommando is het formaat**: `mp3`, `ogg`
of `wav`. Alias `audio` ≡ `mp3`. Bron mag ``.mvsa``, ``.mxl``, ``.vsa`` of
``.mscz`` (fallback) zijn. Alleen het artefact; de consumer-site zet de
afspeelknop. Sleepstilte aan het eind wordt weggeknipt (checklist A5;
vereist **ffmpeg**). Zie [`vsa audio`](audio.md) en
[formats/audio.md](../../formats/audio.md).

### Argumenten en opties

| Naam             | Verplicht | Betekenis                                            | Default                                            |
| ---------------- | --------- | ---------------------------------------------------- | -------------------------------------------------- |
| `path`           | Ja        | ``.mvsa`` / ``.mxl`` / ``.vsa`` / ``.mscz``, of map. | —                                                  |
| `-o`, `--output` | Nee       | Uitvoer-audio (alleen bij precies één bron).         | ``<bronnaam>.<formaat>`` (bijv. ``lied.mvsa.ogg``) |
| `--section`      | Nee       | Alleen bij ``.mvsa``: één ``@sectie``-id.            | alle secties                                       |
| `--musescore`    | Nee       | MuseScore-executable.                                | auto-detectie                                      |
| `--keep-mxl`     | Nee       | Bewaar tussenliggende playback-``.mxl``.             | temp (wordt verwijderd)                            |

### Voorbeelden

```cmd
mvsa mp3 examples\mvsa\test-alleluia-toon-8.mvsa --section schets3-oct-doremi
mvsa mp3 lied.mvsa -o generated\lied.mp3
mvsa ogg lied.mvsa
mvsa wav lied.mxl -o generated\lied.wav
```

---

Score → `.mvsa` (werkbank): [`mxl mvsa`](mxl.md) / [`mscz mvsa`](mscz.md) — details in [formats/mvsa — Score naar mvsa](../../formats/mvsa.md#score-naar-mvsa).

---

## `mvsa normalize`

### Synopsis

```text
mvsa normalize [-h] [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa,ag-vsa}]
                   [--octave-style {@oct,marker}] [--no-align] path
```

### Beschrijving

Canoniseert een **bestaand** `.mvsa`-bestand (uitlijning; optioneel
hoogte-spelling). De L-regel (lyrics, ELM, recite, melisma) blijft
semantisch gelijk. Sticky `@do` / `@mode` / `@oct` blijven staan.

**Default bij bron `.mvsa`:** `--pitch preserve` — de **namen/notaties van
noten blijven zoals in de bron** (bladcijfer, do-re-mi, a–g, EHM, …). Alleen
kolom- en maatstreep-uitlijning gebeurt standaard. Zo blijf je
meerdere schetsen met verschillende spellingen in één bestand intact.

Wil je wél herschrijven naar één vorm, geef dan expliciet `--pitch doremi`,
`a-g`, `vsa` of `ag-vsa`. (`abc` is een alias van `a-g`.)

**Score → `.mvsa`** (`.mxl` / `.mscz` via `mxl mvsa` / `mscz mvsa`): daar is de default **`ag-vsa`** — er is dan geen “bronnotatie” om
te bewaren.

| `--pitch`   | Gedrag                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------- |
| `preserve`  | **Default** voor `.mvsa` → `.mvsa`: stemtokens ongewijzigd; wel align                           |
| `doremi`    | Laddergraden t.o.v. `@do` / `@oct`                                                              |
| `a-g`       | Toonnamen met wetenschappelijk cijfer (`bb4`, `c5`, …); alias: `abc`                            |
| `vsa`       | Eerste toon absoluut (doremi), daarna EHM (`/`, `\2`, …)                                        |
| `ag-vsa`    | Per LSATB-systeem: eerste noot absolute a–g, daarna EHM; a–g-eindanker op de laatste maatstreep |

Kolom- en maatstreep-uitlijning gebeurt standaard (zelfde regels als
`scripts/align_mvsa_columns.py`); zet `--no-align` om dat over te slaan.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                    | Verplicht | Betekenis                                                            | Default                         |
| ----------------------- | --------- | -------------------------------------------------------------------- | ------------------------------- |
| `path`                  | Ja        | Bron-`.mvsa`-bestand of map met `.mvsa`-bestanden.                   | —                               |
| `--pitch`               | Nee       | `preserve` (default), of `doremi` / `a-g` / `vsa` / `ag-vsa`         | `preserve` bij `.mvsa`-bron     |
| `-o`, `--output`        | Nee       | Uitvoerpad (alleen bij precies één bronbestand).                     | `<stem>.normalized.mvsa`        |
| `--octave-style`        | Nee       | `@oct` (canoniek) of `marker` (nog niet klaar)                       | `@oct`                          |
| `--no-align`            | Nee       | Geen kolomuitlijning.                                                | uit (wel alignen)               |

### Output

- **stdout**: `Geschreven: <pad>` bij succes.
- **bestand**: genormaliseerde `.mvsa`.

### Exit status

| Exitcode | Betekenis                                          |
| -------- | -------------------------------------------------- |
| `0`      | Normalisatie geschreven.                           |
| `1`      | Pad ontbreekt, validatiefout, of normalisatiefout. |

### Voorbeelden

```cmd
mvsa normalize examples\mvsa\alleluia-toon-8.canonieke.mvsa -o generated\alleluia.normalized.mvsa
mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
mvsa normalize lied.mvsa --pitch doremi --octave-style @oct
```

**Zie ook:** [`transpose`](#mvsa-transpose) (andere tonica),
[`kuiser`](#mvsa-kuiser) (authoring in-place).

---

## `mvsa transpose`

### Synopsis

```text
mvsa transpose [-h] --to TONIC [-o OUTPUT]
                   [--pitch {doremi,a-g,vsa,ag-vsa}]
                   [--octave-style {@oct,marker}] [--no-align] path
```

### Beschrijving

Transponeert een **bestaand** `.mvsa`-bestand naar een andere
[do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
(tonica). Je geeft de **doeltonica** met `--to` (zelfde vorm als
[`@do`](../../specification-mvsa/keywords.md#do): `F4`, `Bb3`, of `F`
zonder octaafcijfer — dan geldt het octaaf van de bron-`@do`).

**Wat meeschuift**

- elke sticky `@do`-regel (ook mid-bestand-wissels), met hetzelfde interval;
- alle klinkende stemtonen (absolute a–g én via EHM/doremi opgeloste tonen).

**Wat gelijk blijft**

- `@mode` (majeur blijft majeur; mineur blijft mineur);
- `@oct`, L-regel (lyrics, ELM, recite), titels/metadata, commentaren.

Default `--pitch ag-vsa`: na de shift worden stemregels herschreven zoals bij
import (eerste noot absolute a–g, daarna EHM, absolute eindanker). Andere
vormen: `doremi`, `a-g`, `vsa` (`abc` is alias van `a-g`).

`normalize` wijzigt **geen** toonsoort (alleen spelling/uitlijning).
`transpose` is het pad voor “Es majeur → F majeur”. Daarna mag je
`normalize` of `kuiser` draaien.

Commentaren die de oude toonsoort noemen (bijv. `# drie mollen`) worden
**niet** automatisch herschreven.

### Argumenten en opties

| Naam                    | Verplicht | Betekenis                                                            | Default                         |
| ----------------------- | --------- | -------------------------------------------------------------------- | ------------------------------- |
| `path`                  | Ja        | Bron-`.mvsa`-bestand of map met `.mvsa`-bestanden.                   | —                               |
| `--to`                  | Ja        | Doeltonica (`F4`, `Bb3`, of `F` = octaaf van bron-`@do`).            | —                               |
| `-o`, `--output`        | Nee       | Uitvoerpad (alleen bij precies één bronbestand).                     | `<stem>.transposed.mvsa`        |
| `--pitch`               | Nee       | `doremi` / `a-g` / `vsa` / `ag-vsa` (geen `preserve`)                | `ag-vsa`                        |
| `--octave-style`        | Nee       | `@oct` (canoniek) of `marker` (nog niet klaar)                       | `@oct`                          |
| `--no-align`            | Nee       | Geen kolomuitlijning.                                                | uit (wel alignen)               |

### Output

- **stdout**: `Geschreven: <pad>` bij succes.
- **bestand**: getransponeerde `.mvsa` (sibling of `-o`).

### Exit status

| Exitcode | Betekenis                                          |
| -------- | -------------------------------------------------- |
| `0`      | Transpositie geschreven.                           |
| `1`      | Pad ontbreekt, validatiefout, of transpositiefout. |

### Voorbeelden

```cmd
mvsa transpose examples\bug-cases\alleluia-9b-toon-3-vokn.mvsa --to F4
mvsa transpose examples\bug-cases\alleluia-9b-toon-3-vokn.mvsa --to F -o generated\alleluia.in-F.mvsa
mvsa transpose examples\bug-cases --to F4
mvsa transpose lied.mvsa --to Bb3 --pitch doremi -o generated\lied.in-Bb.mvsa
```

**Zie ook:** [`normalize`](#mvsa-normalize),
[`@do` / `@mode`](../../specification-mvsa/keywords.md#do),
[mvsa schrijven 101 — toonsoort](../../guides/mvsa-schrijven-101.md#toonsoort-verzetten-transpose).

---

## `mvsa kuiser`

### Synopsis

```text
mvsa kuiser [-h] [-o OUTPUT] [--check] [--pitch {preserve,doremi,a-g,vsa,ag-vsa}]
                [--octave-style {@oct,marker}] [--no-align] path [path …]
```

### Beschrijving

Authoring-pad naar de **canonieke schrijfvorm** uit de draft-spec
([syntax](../../specification-mvsa/syntax.md),
[semantiek — layout](../../specification-mvsa/semantics.md#canonieke-layout-vs-tolerantie)):

1. woordstreep-spatie op L (`hei- li` → `hei-li`; `le-  lu` blijft);
2. maatstrepen syncen waar eenduidig (maximale unieke bar-reeks;
   herpartitioneren via positietelling);
3. daarna hetzelfde als `normalize` (default `--pitch preserve` + kolomalign).

Default schrijft **in-place**. Gebruik `--check` als dry-run (exit 1 als er
iets zou wijzigen). Na afloop moet validate geen errors meer geven; bij
conflicterende strepen faalt de kuiser met een duidelijke fout.

Gedrag t.o.v. `-` / `~` op L (draft-spec):

- **Canoniek:** lone standaard-lengte zonder `~` (impliciet); `~` wél bij
  `&`-melisma (`ziel~&~`) en na recite-`)` bij niet-breve duur. Woordstreepje
  direct vóór de lettergreep (`-li`), met spaties *ervóór* bij extra breedte
  (`…_&_  -li`).
- **Invoer:** kale ELM-`-` mag (o.a. melisma); kuiser herschrijft eenduidige
  gevallen naar `~` en laat daarna lone `~` weg.
- **Ambigu** (`hei- li`, `li-&--ge`): waarschuwing op stderr met
  `bestand:regel:kolom` — geen stille collapse naar `hei-li`.
- **Pyphen** (ontbrekende / verdachte woordstreepjes): advies-warnings;
  geen validate-fout. Sync-telling blijft leidend; bij complexe
  MuseScore-importlyrics soms `--no-align`.

`normalize` blijft het conversiepad (pitch-herschrijf naar een apart
uitvoerbestand). `transpose` verandert de tonica (`@do`). `kuiser` is het
dagelijkse authoring-commando.

### Argumenten en opties

| Optie                   | Verplicht | Beschrijving                                                         | Default              |
| ----------------------- | --------- | -------------------------------------------------------------------- | -------------------- |
| `path`                  | Ja        | `.mvsa`-bestand(en) of map(pen).                                     | —                    |
| `-o`, `--output`        | Nee       | Uitvoerpad (alleen bij precies één bronbestand).                     | in-place             |
| `--check`               | Nee       | Geen schrijfactie; exit 1 bij wijziging.                             | uit                  |
| `--pitch`               | Nee       | Zelfde als `normalize` (default preserve).                           | `preserve`           |
| `--octave-style`        | Nee       | Schrijfoctaaf-stijl.                                                 | `@oct`               |
| `--no-align`            | Nee       | Sla kolomuitlijning over.                                            | uit                  |

### Exit status

| Exitcode | Betekenis                                                      |
| -------- | -------------------------------------------------------------- |
| `0`      | Klaar (of `--check` zonder wijziging).                         |
| `1`      | Pad ontbreekt, kuiser-/validatiefout, of `--check` met diff.   |

### Voorbeelden

```cmd
mvsa kuiser examples\mvsa\alleluia-toon-8.mvsa
mvsa kuiser examples\mvsa --check
mvsa kuiser lied.mvsa -o generated\lied.kuiser.mvsa
mvsa kuiser lied.mvsa --pitch a-g
```

---

## `mvsa import`

### Synopsis

```text
mvsa import [-h] [-o OUTPUT] [--pitch …] [--musescore PATH] path
```

### Beschrijving

Zet een **`.mscz`** of MusicXML (`.mxl` / `.musicxml` / `.xml`) om naar
werkbank-`.mvsa`. **Catalogus-vrij** (geen plaatsing in de bibliotheek).

| Bronextensie                  | Zelfde als             |
| ----------------------------- | ---------------------- |
| `.mscz`                       | [`mscz mvsa`](mscz.md) |
| `.mxl` / `.musicxml` / `.xml` | [`mxl mvsa`](mxl.md)   |

Andere extensies → exit 1 met duidelijke fout. Contract-navigatie:
[contract-index](../../formats/contract-index.md).

### Voorbeelden

```cmd
mvsa import lied.mscz
mvsa import examples\importer\tweede-antifoon-zondag-hemelum.mxl -o generated\from-mxl.mvsa
mscz mvsa lied.mscz
```

---

## `mvsa products`

### Synopsis

```text
mvsa products [-h] [--force] [--dry-run] [--quiet] [--skip-svg] [--musescore PATH] path
```

### Beschrijving

Schrijft voor elke `.mvsa` onder `path`:

| Product                   | Bestand                                                                 |
| ------------------------- | ----------------------------------------------------------------------- |
| Coria-`.mxl`              | `{stam}.mvsa.mxl`                                                       |
| Score-IR                  | `{stam}.mvsa.score-ir.json`                                             |
| from-ir MusicXML          | `{stam}.mvsa.from-ir.musicxml`                                          |
| SVG (tenzij `--skip-svg`) | `{stam}.mvsa.svg` (tall, compact)                                       |
| Meta                      | `{stam}.mvsa.products-meta.json` (key `svg`; zie products-meta)         |

Slaat over als meta zegt dat de bron-hash nog klopt en de bestanden er zijn
(`--force` regenereert). `--quiet` onderdrukt voortgangsregels op stdout
(fouten blijven op stderr). Kaal: geen bibliotheek-stamps.
[contract-index](../../formats/contract-index.md) ·
[products-meta](../../formats/products-meta.md).

### Voorbeelden

```cmd
mvsa products examples\mvsa\1a-vredeslitanie.mvsa --skip-svg
mvsa products examples\mvsa --dry-run --skip-svg
```

## Zie ook

- Draft-spec: [specification-mvsa](../../specification-mvsa/README.md)
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
- Straat-CLIs: [straat-clis](../../plans/straat-clis.md)
- Contract-index: [contract-index](../../formats/contract-index.md)
- Invoer bestand of map: [input-pad.md](input-pad.md)
- Voorbeelden: [examples/mvsa](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa)
- Eenstemmig: [`vsa validate`](validate.md), [`vsa musicxml`](musicxml.md)
- Platte gezongen tekst: [`vsa text`](text.md) (ook op `.mvsa` / MusicXML / `.mscz`)
