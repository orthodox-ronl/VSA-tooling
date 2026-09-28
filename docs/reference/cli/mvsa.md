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
mvsa [-h] {validate,musicxml,mscz,pdf,import,normalize} …
vsa mvsa [-h] {validate,musicxml,mscz,pdf,import,normalize} …
mvsa validate [-h] path
mvsa musicxml [-h] [-o OUTPUT] [--section SECTION] path
mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
          [--keep-mxl PATH] path
mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
         [--keep-mscz PATH] [--keep-mxl PATH] path
mvsa import [-h] [-o OUTPUT] --pitch {doremi,a-g,vsa} …
mvsa normalize [-h] [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa}] …
```

## Subcommando's

| Subcommando                          | Doel                                                         |
| ------------------------------------ | ------------------------------------------------------------ |
| [`validate`](#vsa-mvsa-validate)     | Structuur + sync-telling van `.mvsa` controleren.            |
| [`musicxml`](#vsa-mvsa-musicxml)     | Exporteer `.mvsa` naar SATB MusicXML.                        |
| [`mscz`](#vsa-mvsa-mscz)             | Exporteer `.mvsa` naar MuseScore (`.mscz`).                  |
| [`pdf`](#vsa-mvsa-pdf)               | Exporteer `.mvsa` of `.mscz` naar print-PDF (zangers).       |
| [`import`](#vsa-mvsa-import)         | Importeer `.mxl` / `.mscz` naar `.mvsa`.                     |
| [`normalize`](#vsa-mvsa-normalize)   | Canoniseer `.mvsa` (default: behoud noteernamen).            |

Hulp op de commandoregel:

```cmd
mvsa -h
vsa mvsa -h
mvsa validate -h
mvsa musicxml -h
mvsa mscz -h
mvsa pdf -h
mvsa import -h
mvsa normalize -h
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
vsa mvsa musicxml [-h] [-o OUTPUT] [--section SECTION] path
```

### Beschrijving

Exporteert **één** `.mvsa`-bestand naar SATB MusicXML (`.mxl` of
`.musicxml`/`.xml`). Zonder `--section` gaan alle `@sectie`-blokken achter
elkaar in één partituur; met `--section` alleen die sectie-id.

Dit is een **aparte** exporter dan [`vsa musicxml`](musicxml.md) (eenstemmig
VSA).

### Argumenten en opties

| Naam                 | Verplicht | Betekenis                                                                 | Default                                      | Beperkingen                          |
| -------------------- | --------- | ------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------ |
| `path`               | Ja        | Bron-`.mvsa`-bestand.                                                     | —                                            | Moet een bestaand bestand zijn.      |
| `-o`, `--output`     | Nee       | Uitvoerpad (`.mxl`, `.musicxml` of `.xml`).                               | `<stem>.mxl` naast het bronbestand           | Andere extensie → wordt `.mxl`.      |
| `--section SECTION`  | Nee       | Alleen deze `@sectie`-id exporteren (bijv. `schets-a-bladcijfer`).        | Alle secties                                 | Id moet in het bestand voorkomen.    |
| `-h`, `--help`       | Nee       | Toon hulp voor dit subcommando (inclusief `-o` en `--section`).           | —                                            | —                                    |

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

### Voorbeelden — falen

Onbekende sectie-id of sync-fout in het `.mvsa`-bestand levert exitcode `1`
en diagnostiek op stderr. Controleer eerst met `vsa mvsa validate`.

---

## `vsa mvsa mscz`

### Synopsis

```text
vsa mvsa mscz [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
              [--keep-mxl PATH] path
```

### Beschrijving

Exporteert **één** `.mvsa`-bestand naar MuseScore (`.mscz`) via de keten:

```text
.mvsa  →  .mxl (partituur: SA/TB, lege part-namen)  →  MuseScore CLI  →  .mscz
       →  stem-indicaties uit (Style + lege namen)
```

Dit voldoet aan de [MSCZ-checklist](../../formats/canonical-checklists.md#checklist-mscz-partituur-musescore)
(twee balken, geen S/Soprano-labels). Voor Coria-playback (vier parts)
blijft [`vsa mvsa musicxml`](#vsa-mvsa-musicxml) het primaire pad.

Vereist MuseScore 4 (of 3): op `PATH` als `MuseScore4` / `mscore`, of het
standaard Windows-pad
`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`. Override met
`--musescore`.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                 | Verplicht | Betekenis                                              | Default                             |
| -------------------- | --------- | ------------------------------------------------------ | ----------------------------------- |
| `path`               | Ja        | Bron-`.mvsa`-bestand.                                  | —                                   |
| `-o`, `--output`     | Nee       | Uitvoer-`.mscz`.                                       | `<stem>.mscz` naast het bronbestand |
| `--section SECTION`  | Nee       | Alleen deze `@sectie`-id.                              | Alle secties                        |
| `--musescore PATH`   | Nee       | Pad naar MuseScore-executable.                         | Auto-detectie                       |
| `--keep-mxl PATH`    | Nee       | Bewaar ook het tussenliggende `.mxl`.                  | temp (wordt verwijderd)             |

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
```

---

## `vsa mvsa pdf`

### Synopsis

```text
vsa mvsa pdf [-h] [-o OUTPUT] [--section SECTION] [--musescore PATH]
             [--keep-mscz PATH] [--keep-mxl PATH] path
```

### Beschrijving

Maakt een **print-PDF** van de partituur (voor zangers), via MuseScore CLI.

| Bron    | Pad                                                                      |
| ------- | ------------------------------------------------------------------------ |
| `.mvsa` | Keten: partituur-`.mxl` → `.mscz` (layout-conventies) → `.pdf`           |
| `.mscz` | Alleen MuseScore-conversie naar `.pdf` (geen her-export uit `.mvsa`)     |

Dit is **niet** [`vsa pdf`](pdf.md) (Markdown + VSA-SVG naar A4 via browser).

### Argumenten en opties

| Naam              | Verplicht | Betekenis                                      | Default                    |
| ----------------- | --------- | ---------------------------------------------- | -------------------------- |
| `path`            | Ja        | `.mvsa` of `.mscz`.                            | —                          |
| `-o`, `--output`  | Nee       | Uitvoer-`.pdf`.                                | `<stem>.pdf` naast bron    |
| `--section`       | Nee       | Alleen bij `.mvsa`: één `@sectie`-id.          | alle secties               |
| `--musescore`     | Nee       | MuseScore-executable.                          | auto-detectie              |
| `--keep-mscz`     | Nee       | Bij `.mvsa`: bewaar tussenliggende `.mscz`.    | temp (wordt verwijderd)    |
| `--keep-mxl`      | Nee       | Bij `.mvsa`: bewaar tussenliggende `.mxl`.     | niet                       |

### Voorbeelden

```cmd
vsa mvsa pdf examples\mvsa\alleluia-toon-1.mvsa
vsa mvsa pdf lied.mvsa -o generated\lied.pdf --keep-mscz generated\lied.mscz
vsa mvsa pdf lied.mscz -o lied.pdf
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

| Bron                          | Pad                                                     |
| ----------------------------- | ------------------------------------------------------- |
| `.mxl` / `.musicxml` / `.xml` | Direct geparst (SATB P1–P4)                             |
| `.mscz`                       | Eerst MuseScore CLI → temp `.mxl`, daarna zelfde parser |

Stemhoogten worden in de gekozen `--pitch`-vorm geschreven; `@do` / `@mode`
komen uit de toonsoort (majeur-aanname); `@oct` wordt per stem afgeleid.
Lossy t.o.v. MuseScore-layout — succes = pitch/duur/lyrics-equivalentie.

### Argumenten en opties

| Naam                 | Verplicht | Betekenis                                   | Default              |
| -------------------- | --------- | ------------------------------------------- | -------------------- |
| `path`               | Ja        | `.mxl`, `.musicxml` of `.mscz`.             | —                    |
| `--pitch`            | Ja        | `doremi`, `a-g` (of alias `abc`), of `vsa`. | —                    |
| `-o`, `--output`     | Nee       | Uitvoer-`.mvsa`.                            | `<stem>.import.mvsa` |
| `--octave-style`     | Nee       | `@oct` of `marker` (nog niet)               | `@oct`               |
| `--section`          | Nee       | `@sectie`-id in de output                   | `import`             |
| `--musescore`        | Nee       | MuseScore-pad (bij `.mscz`)                 | auto                 |
| `--no-align`         | Nee       | Geen kolomuitlijning                        | uit                  |

### Voorbeelden

```cmd
vsa mvsa import generated\alleluia-schets2.mxl -o generated\alleluia.import.mvsa --pitch doremi
vsa mvsa import lied.mscz -o lied.mvsa --pitch a-g
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

## Zie ook

- Draft-spec: [specification-mvsa](../../specification-mvsa/README.md)
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
- Voorbeelden: [examples/mvsa](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa)
- Eenstemmig: [`vsa validate`](validate.md), [`vsa musicxml`](musicxml.md)
