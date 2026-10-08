# `vsa mvsa` / `mvsa` — meerstemmige .mvsa (draft)

Draft-tooling voor **mvsa**: meerstemmige tekstbronnen (`.mvsa`) met
lyrics-regels en stemregels. Normatieve draft-spec:
[specification-mvsa](../../specification-mvsa/README.md).

Dit is **niet** hetzelfde als [`vsa validate`](validate.md) /
[`vsa musicxml`](musicxml.md) voor eenstemmige `.vsa`.

**Top-level alias:** `mvsa …` is gelijk aan `vsa mvsa …` (console-script of
`scripts\mvsa.cmd`). Bron-commands voor andere formaten: [`mxl`](mxl.md),
[`mscz`](mscz.md).

## Synopsis

```text
mvsa [-h] {validate,musicxml,mscz,pdf,audio,import,normalize,kuiser} …
vsa mvsa [-h] {validate,musicxml,mscz,pdf,audio,import,normalize,kuiser} …
mvsa validate [-h] path
mvsa musicxml [-h] [-o OUTPUT] [--section SECTION] [--hulptekst]
              [--hulptekst-as-parts] [--bibliotheek-id ID] path
mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
          [--keep-mxl PATH] [--layout PROFILE] [--bibliotheek-id ID]
          [--hulptekst] path
mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
         [--keep-mscz PATH] [--keep-mxl PATH]
         [--layout PROFILE] [--bibliotheek-id ID] path
mvsa audio [-h] [-o OUTPUT] [--format {mp3,ogg,wav}] [--section SECTION]
           [--musescore PATH] [--keep-mxl PATH] [--config CONFIG] path
mvsa import [-h] [-o OUTPUT] --pitch {doremi,a-g,vsa} …
mvsa normalize [-h] [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa}] …
mvsa kuiser [-h] [-o OUTPUT] [--check] [--pitch {preserve,doremi,a-g,vsa}] …
```

## Subcommando's

| Subcommando                          | Doel                                                         |
| ------------------------------------ | ------------------------------------------------------------ |
| [`validate`](#vsa-mvsa-validate)     | Structuur + sync-telling van `.mvsa` controleren.            |
| [`musicxml`](#vsa-mvsa-musicxml)     | Exporteer `.mvsa` naar SATB MusicXML.                        |
| [`mscz`](#vsa-mvsa-mscz)             | Exporteer `.mvsa` naar MuseScore (`.mscz`).                  |
| [`pdf`](#vsa-mvsa-pdf)               | Exporteer `.mvsa` of `.mscz` naar print-PDF (zangers).       |
| [`audio`](#vsa-mvsa-audio)           | Exporteer naar audio (``.mp3``) voor preview-luisteren.      |
| [`import`](#vsa-mvsa-import)         | Importeer `.mxl` / `.mscz` naar `.mvsa`.                     |
| [`normalize`](#vsa-mvsa-normalize)   | Canoniseer `.mvsa` (default: behoud noteernamen).            |
| [`kuiser`](#vsa-mvsa-kuiser)         | Authoring-kuiser: strepen syncen, woordstreep, align.        |

Hulp op de commandoregel:

```cmd
mvsa -h
vsa mvsa -h
mvsa validate -h
mvsa musicxml -h
mvsa mscz -h
mvsa pdf -h
mvsa audio -h
mvsa import -h
mvsa normalize -h
mvsa kuiser -h
```

---

## `vsa mvsa validate`

### Synopsis

```text
vsa mvsa validate [-h] path
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

| Naam           | Verplicht | Betekenis                                      | Default | Beperkingen   |
| -------------- | --------- | ---------------------------------------------- | ------- | ------------- |
| `path`         | Ja        | `.mvsa`-bestand of map met `.mvsa`-bestanden.  | —       | Moet bestaan. |
| `-h`, `--help` | Nee       | Toon hulp voor dit subcommando.                | —       | —             |

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
vsa mvsa validate examples\mvsa
vsa mvsa validate examples\mvsa\alleluia-toon-8.mvsa
```

---

## `vsa mvsa musicxml`

### Synopsis

```text
vsa mvsa musicxml [-h] [-o OUTPUT] [--section SECTION] [--hulptekst]
                  [--hulptekst-as-parts] [--bibliotheek-id ID] path
```

### Beschrijving

Exporteert **één** `.mvsa`-bestand naar SATB MusicXML (`.mxl` of
`.musicxml`/`.xml`). Zonder `--section` gaan alle `@sectie`-blokken achter
elkaar in één partituur; met `--section` alleen die sectie-id.

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

| Naam                   | Verplicht | Betekenis                                                                 | Default                                      | Beperkingen                          |
| ---------------------- | --------- | ------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------ |
| `path`                 | Ja        | Bron-`.mvsa`-bestand.                                                     | —                                            | Moet een bestaand bestand zijn.      |
| `-o`, `--output`       | Nee       | Uitvoerpad (`.mxl`, `.musicxml` of `.xml`).                               | `<stem>.mxl` naast het bronbestand           | Andere extensie → wordt `.mxl`.      |
| `--section SECTION`    | Nee       | Alleen deze `@sectie`-id exporteren (bijv. `schets-a-bladcijfer`).        | Alle secties                                 | Id moet in het bestand voorkomen.    |
| `--bibliotheek-id ID`  | Nee       | Zet bibliotheek-id in identification/rights; anders pad-sniff.            | pad-sniff onder `content-source/bibliotheek` | Optioneel.                           |
| `--hulptekst`          | Nee       | Tweede lyric-laag (number=2) via transliterator.                          | uit                                          | Zie beschrijving hierboven.          |
| `--hulptekst-as-parts` | Nee       | Coria: extra parts met hulptekst (volume 0).                              | uit                                          | Impliceert `--hulptekst`.            |
| `-h`, `--help`         | Nee       | Toon hulp voor dit subcommando.                                           | —                                            | —                                    |

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

Standaard naast het bronbestand (`….mxl`):

```cmd
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa
```

Met expliciet uitvoerpad en één sectie:

```cmd
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa --section schets-a-bladcijfer -o generated\intocht-a.mxl
```

Coria met keuze tussen lyrics-lagen (trisagion, kerkslavische sectie):

```cmd
vsa mvsa musicxml examples\mvsa\trisagion-8a-slav-hemelum.mvsa --section ksl --hulptekst-as-parts -o generated\trisagion-ksl-coria.mxl
```

Blad/MSCZ: lyric 2 op partituur-MXL (keten via `mscz --hulptekst`):

```cmd
vsa mvsa mscz examples\mvsa\hulptekst-ksl-mini.mvsa --hulptekst -o generated\hulptekst-ksl.mscz
```

### Voorbeelden — falen

Onbekende sectie-id of sync-fout in het `.mvsa`-bestand levert exitcode `1`
en diagnostiek op stderr. Controleer eerst met `vsa mvsa validate`.

---

## `vsa mvsa mscz`

### Synopsis

```text
vsa mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
              [--keep-mxl PATH] [--layout PROFILE] [--bibliotheek-id ID] path
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
| `plain`      | Geen nabewerking door VSA-tooling (ruwe MuseScore-output van de partituur-MXL).                                     |

`--bibliotheek-id` zet de id in het colofon (**alleen** bij `partituur`).
Zonder die optie mag tooling de id uit het pad afleiden als
`…/bibliotheek/<zangstuk>/<variant>/<uitvoeringsvorm>/…` — consumers horen
de id **expliciet** te geven. Zie
[ownership](../../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

Dit voldoet bij `partituur` aan de [MSCZ-checklist](../../formats/canonical-checklists.md#checklist-mscz-partituur-musescore)
(twee balken, geen S/Soprano-labels). Voor Coria-playback (vier parts)
blijft [`vsa mvsa musicxml`](#vsa-mvsa-musicxml) het primaire pad.

Vereist MuseScore 4 (of 3): op `PATH` als `MuseScore4` / `mscore`, of het
standaard Windows-pad
`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`. Override met
`--musescore`.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                   | Verplicht | Betekenis                                              | Default                             |
| ---------------------- | --------- | ------------------------------------------------------ | ----------------------------------- |
| `path`                 | Ja        | Bron-`.mvsa`-bestand.                                  | —                                   |
| `-o`, `--output`       | Nee       | Uitvoer-`.mscz`.                                       | `<stem>.mscz` naast het bronbestand |
| `--section SECTION`    | Nee       | Alleen deze `@sectie`-id.                              | Alle secties                        |
| `--musescore PATH`     | Nee       | Pad naar MuseScore-executable.                         | Auto-detectie                       |
| `--keep-mxl PATH`      | Nee       | Bewaar ook het tussenliggende `.mxl`.                  | temp (wordt verwijderd)             |
| `--layout PROFILE`     | Nee       | `partituur` of `plain`.                                | `partituur`                         |
| `--bibliotheek-id ID`  | Nee       | Colofon-id (profiel `partituur`); anders pad-fallback. | pad-sniff / geen                    |
| `--hulptekst`          | Nee       | Tweede lyric-laag in tussen-MXL (blad «tweede regel»). | uit                                 |

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
vsa mvsa mscz examples\mvsa\alleluia-toon-8.canonieke.mvsa
vsa mvsa mscz lied.mvsa -o generated\lied.mscz --section schets2-oct-doremi
vsa mvsa mscz lied.mvsa -o out.mscz --keep-mxl generated\lied.mxl
vsa mvsa mscz lied.mvsa -o out.mscz --layout partituur --bibliotheek-id zangstuk/var/uv
vsa mvsa mscz lied.mvsa -o raw.mscz --layout plain
```

---

## `vsa mvsa pdf`

### Synopsis

```text
vsa mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
             [--keep-mscz PATH] [--keep-mxl PATH]
             [--layout PROFILE] [--bibliotheek-id ID] path
```

### Beschrijving

Maakt een **print-PDF** van de partituur (voor zangers), via MuseScore CLI.

| Bron    | Pad                                                                      |
| ------- | ------------------------------------------------------------------------ |
| `.mvsa` | Keten: partituur-`.mxl` → `.mscz` (`--layout`) → `.pdf`                  |
| `.mscz` | Alleen MuseScore-conversie naar `.pdf` (geen her-export uit `.mvsa`)     |

`--layout` / `--bibliotheek-id` gelden alleen bij bron `.mvsa` (zelfde
betekenis als bij [`mscz`](#vsa-mvsa-mscz)).

**Canoniek:** A4 staand (checklist
[PDF P6](../../formats/canonical-checklists.md#checklist-pdf-afgeleide-van-mscz));
via MuseScore-Style van het `.mscz` (MSCZ S7). US Letter is niet canoniek.

Dit is **niet** [`vsa pdf`](pdf.md) (Markdown + VSA-SVG via browser; wél
dezelfde A4-eis P6).

### Argumenten en opties

| Naam                   | Verplicht | Betekenis                                      | Default                    |
| ---------------------- | --------- | ---------------------------------------------- | -------------------------- |
| `path`                 | Ja        | `.mvsa` of `.mscz`.                            | —                          |
| `-o`, `--output`       | Nee       | Uitvoer-`.pdf`.                                | `<stem>.pdf` naast bron    |
| `--section`            | Nee       | Alleen bij `.mvsa`: één `@sectie`-id.          | alle secties               |
| `--musescore`          | Nee       | MuseScore-executable.                          | auto-detectie              |
| `--keep-mscz`          | Nee       | Bij `.mvsa`: bewaar tussenliggende `.mscz`.    | temp (wordt verwijderd)    |
| `--keep-mxl`           | Nee       | Bij `.mvsa`: bewaar tussenliggende `.mxl`.     | niet                       |
| `--layout PROFILE`     | Nee       | Bij `.mvsa`: `partituur` of `plain`.           | `partituur`                |
| `--bibliotheek-id ID`  | Nee       | Bij `.mvsa` + `partituur`: colofon-id.         | pad-sniff / geen           |

### Voorbeelden

```cmd
vsa mvsa pdf examples\mvsa\alleluia-toon-1.mvsa
vsa mvsa pdf lied.mvsa -o generated\lied.pdf --keep-mscz generated\lied.mscz
vsa mvsa pdf lied.mvsa --layout partituur --bibliotheek-id zangstuk/var/uv
vsa mvsa pdf lied.mscz -o lied.pdf
```

---

## `vsa mvsa audio`

### Synopsis

```text
vsa mvsa audio [-h] [-o OUTPUT] [--format {mp3,ogg,wav}] [--section SECTION]
               [--musescore PATH] [--keep-mxl PATH] [--config CONFIG] path
```

### Beschrijving

Maakt een **preview-audiobestand** (default ``.mp3``) via MuseScore: eerst
playback-``.mxl`` (vier parts), daarna audio. Bron mag ``.mvsa``, ``.mxl``,
``.vsa`` of ``.mscz`` (fallback) zijn. Alleen het artefact; de consumer-site
zet de afspeelknop. Zie [`vsa audio`](audio.md) en [formats/audio.md](../../formats/audio.md).

### Argumenten en opties

| Naam                     | Verplicht | Betekenis                                         | Default                         |
| ------------------------ | --------- | ------------------------------------------------- | ------------------------------- |
| `path`                   | Ja        | ``.mvsa`` / ``.mxl`` / ``.vsa`` / ``.mscz``.      | —                               |
| `-o`, `--output`         | Nee       | Uitvoer-audio.                                    | ``<stem>.mp3`` naast bron       |
| `--format`               | Nee       | ``mp3`` / ``ogg`` / ``wav`` zonder extensie.      | ``mp3`` of ``[audio].format``   |
| `--section`              | Nee       | Alleen bij ``.mvsa``: één ``@sectie``-id.         | alle secties                    |
| `--musescore`            | Nee       | MuseScore-executable.                             | auto-detectie                   |
| `--keep-mxl`             | Nee       | Bewaar tussenliggende playback-``.mxl``.          | temp (wordt verwijderd)         |
| `--config`               | Nee       | Pad naar ``vsa.toml``.                            | auto-detectie                   |

### Voorbeelden

```cmd
vsa mvsa audio examples\mvsa\test-alleluia-toon-8.mvsa --section schets3-oct-doremi
vsa mvsa audio lied.mvsa -o generated\lied.mp3
vsa mvsa audio lied.mxl -o lied.ogg --format ogg
```

---

## `vsa mvsa import`

### Synopsis

```text
vsa mvsa import [-h] [-o OUTPUT] --pitch {doremi,a-g,vsa}
                [--octave-style {@oct,marker}] [--section SECTION]
                [--musescore PATH] [--no-align] path
```

### Beschrijving

Importeert een partituur naar `.mvsa`:

| Bron                          | Pad                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| `.mxl` / `.musicxml` / `.xml` | Direct geparst (SATB P1–P4)                                                                             |
| `.mscz`                       | MuseScore CLI → temp `.mxl` → **SATB-normalisatie** (zelfde explode als [`mscz mxl`](mscz.md)) → parser |

Stemhoogten worden in de gekozen `--pitch`-vorm geschreven; `@do` / `@mode`
komen uit de toonsoort (majeur-aanname); `@oct` wordt per stem afgeleid.
Lossy t.o.v. MuseScore-layout — succes = pitch/duur/lyrics-equivalentie.

**Leesbaarheid van de uitvoer**

- Soft-wrap: LSATB-systemen van ongeveer 80 tekens
  (`DEFAULT_SYSTEM_SOFT_WIDTH`). Eén maat die alleen al langer is blijft één
  systeem.
- Same-pitch holds: opeenvolgende dezelfde toonhoogte (ook over maatgrenzen)
  wordt op de stemregels als `-` geschreven.
- Multi-lettergreep lyrics op één noot (spaties, `-`, of soft hyphen) worden
  recite `( … )` i.p.v. één geplakte lettergreep. Een lone extender `-` wordt
  lege recite `()~`. Trailing `.` op lyric-tekst wordt weggestript.
- **Normaalvorm:** standaard schrijft import daarna de canonieke vorm via
  [`mvsa kuiser`](#vsa-mvsa-kuiser) (standaard-lengte op L als `~`, maatstrepen
  sync, kolomuitlijning) — zie
  [syntax — canonieke schrijfvorm](../../specification-mvsa/syntax.md) en
  [semantiek — canonieke layout](../../specification-mvsa/semantics.md#canonieke-layout-vs-tolerantie).

Bij complexe MuseScore-lyrics is soms `--no-align` nodig (sla kuiser/align
over) — de sync-telling blijft leidend. Pyphen-woordstreep-warnings van
`kuiser` zijn advies, geen import-fout.

Bij `--pitch vsa` plakt de import op elke stemregel een **eindanker** met
absolute toonhoogte (a–g met wetenschappelijk cijfer) direct achter de
**laatste maatstreep** van elk systeem, bijvoorbeeld `|g4` of `||a4`. Dat zijn
check-only ankers: na wijzigingen in het `.mvsa` vangt `mvsa validate` een
mismatch op (`MVSA-BAR-ANKER`). Op de lyrics-regel (`L:`) blijven de strepen
kaal. Bij `--pitch doremi` en `--pitch a-g` komen die eindankers niet.

Syntax van eindankers:
[specification-mvsa — eindanker](../../specification-mvsa/syntax.md#eindanker-aan-de-maatstreep).

### Argumenten en opties

| Naam                 | Verplicht | Betekenis                                   | Default              |
| -------------------- | --------- | ------------------------------------------- | -------------------- |
| `path`               | Ja        | `.mxl`, `.musicxml` of `.mscz`.             | —                    |
| `--pitch`            | Ja        | `doremi`, `a-g` (of alias `abc`), of `vsa`. | —                    |
| `-o`, `--output`     | Nee       | Uitvoer-`.mvsa`.                            | `<stem>.import.mvsa` |
| `--octave-style`     | Nee       | `@oct` of `marker` (nog niet)               | `@oct`               |
| `--section`          | Nee       | `@sectie`-id in de output                   | `import`             |
| `--musescore`        | Nee       | MuseScore-pad (bij `.mscz`)                 | auto                 |
| `--no-align`         | Nee       | Geen kuiser-normaalvorm (geen align)        | uit                  |

### Voorbeelden

```cmd
vsa mvsa import generated\alleluia-schets2.mxl -o generated\alleluia.import.mvsa --pitch doremi
vsa mvsa import lied.mscz -o lied.mvsa --pitch a-g
vsa mvsa import lied.mxl -o lied.mvsa --pitch vsa
vsa mvsa validate lied.mvsa
```

---

## `vsa mvsa normalize`

### Synopsis

```text
vsa mvsa normalize [-h] [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa}]
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
`a-g` of `vsa`. (`abc` is een alias van `a-g`.)

**Import uit een ander formaat** (`.mxl` / `.mscz` via `mvsa import` / `mxl
import`): daar is `--pitch` verplicht of default **`doremi`** — er is dan
geen “bronnotatie” om te bewaren.

| `--pitch`   | Gedrag                                                                |
| ----------- | --------------------------------------------------------------------- |
| `preserve`  | **Default** voor `.mvsa` → `.mvsa`: stemtokens ongewijzigd; wel align |
| `doremi`    | Laddergraden t.o.v. `@do` / `@oct`                                    |
| `a-g`       | Toonnamen met wetenschappelijk cijfer (`bb4`, `c5`, …); alias: `abc`  |
| `vsa`       | Eerste toon absoluut (doremi), daarna EHM (`/`, `\2`, …)              |

Kolom- en maatstreep-uitlijning gebeurt standaard (zelfde regels als
`scripts/align_mvsa_columns.py`); zet `--no-align` om dat over te slaan.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                    | Verplicht | Betekenis                                                            | Default                         |
| ----------------------- | --------- | -------------------------------------------------------------------- | ------------------------------- |
| `path`                  | Ja        | Bron-`.mvsa`-bestand.                                                | —                               |
| `--pitch`               | Nee       | `preserve` (default), of `doremi` / `a-g` / `vsa` om te herschrijven | `preserve` bij `.mvsa`-bron     |
| `-o`, `--output`        | Nee       | Uitvoerpad.                                                          | `<stem>.normalized.mvsa`        |
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
vsa mvsa normalize examples\mvsa\alleluia-toon-8.canonieke.mvsa -o generated\alleluia.normalized.mvsa
vsa mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
vsa mvsa normalize lied.mvsa --pitch doremi --octave-style @oct
```

---

## `vsa mvsa kuiser`

### Synopsis

```text
vsa mvsa kuiser [-h] [-o OUTPUT] [--check] [--pitch {preserve,doremi,a-g,vsa}]
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

Gedrag t.o.v. `-` op L (draft-spec):

- **Canoniek:** standaard-lengte als `~`; woordstreepje direct vóór de
  lettergreep (`-li`), met spaties *ervóór* bij extra breedte (`…_&_  -li`).
- **Invoer:** kale ELM-`-` mag (o.a. melisma); kuiser herschrijft eenduidige
  gevallen naar `~`.
- **Ambigu** (`hei- li`, `li-&--ge`): waarschuwing op stderr met
  `bestand:regel:kolom` — geen stille collapse naar `hei-li`.
- **Pyphen** (ontbrekende / verdachte woordstreepjes): advies-warnings;
  geen validate-fout. Sync-telling blijft leidend; bij complexe
  MuseScore-importlyrics soms `--no-align`.

`normalize` blijft het conversiepad (pitch-herschrijf naar een apart
uitvoerbestand). `kuiser` is het dagelijkse authoring-commando.

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
vsa mvsa kuiser examples\mvsa\alleluia-toon-8.mvsa
vsa mvsa kuiser examples\mvsa --check
vsa mvsa kuiser lied.mvsa -o generated\lied.kuiser.mvsa
vsa mvsa kuiser lied.mvsa --pitch a-g
```

## Zie ook

- Draft-spec: [specification-mvsa](../../specification-mvsa/README.md)
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
- Voorbeelden: [examples/mvsa](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa)
- Eenstemmig: [`vsa validate`](validate.md), [`vsa musicxml`](musicxml.md)
- Platte gezongen tekst: [`vsa text`](text.md) (ook op `.mvsa` / MusicXML / `.mscz`)
