# `vsa mvsa` — meerstemmige .mvsa (draft)

Draft-tooling voor **mvsa**: meerstemmige tekstbronnen (`.mvsa`) met
lyrics-regels en stemregels. Normatieve draft-spec:
[specification-mvsa](../../specification-mvsa/README.md).

Dit is **niet** hetzelfde als [`vsa validate`](validate.md) /
[`vsa musicxml`](musicxml.md) voor eenstemmige `.vsa`.

## Synopsis

```text
vsa mvsa [-h] {validate,musicxml,normalize} …
vsa mvsa validate [-h] path
vsa mvsa musicxml [-h] [-o OUTPUT] [--section SECTION] path
vsa mvsa normalize [-h] [-o OUTPUT] --pitch {doremi,abc,vsa}
                   [--octave-style {@oct,marker}] [--no-align] path
```

## Subcommando's

| Subcommando                          | Doel                                              |
| ------------------------------------ | ------------------------------------------------- |
| [`validate`](#vsa-mvsa-validate)     | Structuur + sync-telling van `.mvsa` controleren. |
| [`musicxml`](#vsa-mvsa-musicxml)     | Exporteer `.mvsa` naar SATB MusicXML.             |
| [`normalize`](#vsa-mvsa-normalize)   | Herschrijf stemhoogten naar canonieke spelling.   |

Hulp op de commandoregel:

```cmd
vsa mvsa -h
vsa mvsa validate -h
vsa mvsa musicxml -h
vsa mvsa normalize -h
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

- **stdout**: per geldig bestand `<pad>: OK`; warnings naar stdout.
- **stderr**: errors (`ERROR: …`) en samenvatting bij falen.
- Geen bestanden aangemaakt.

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

## `vsa mvsa normalize`

### Synopsis

```text
vsa mvsa normalize [-h] [-o OUTPUT] --pitch {doremi,abc,vsa}
                   [--octave-style {@oct,marker}] [--no-align] path
```

### Beschrijving

Herschrijft **stemregels** (S/A/T/B) naar één gekozen hoogte-spelling. De
L-regel (lyrics, ELM, recite, melisma) blijft semantisch gelijk. Sticky
`@do` / `@mode` / `@oct` blijven staan (`--octave-style @oct`).

| `--pitch` | Output op stemregels                                      |
| --------- | --------------------------------------------------------- |
| `doremi`  | Laddergraden t.o.v. `@do` / `@oct`                        |
| `abc`     | Toonnamen met wetenschappelijk cijfer (`bb4`, `c5`, …)    |
| `vsa`     | Eerste toon absoluut (doremi), daarna EHM (`/`, `\2`, …) |

Kolom- en maatstreep-uitlijning gebeurt standaard (zelfde regels als
`scripts/align_mvsa_columns.py`); zet `--no-align` om dat over te slaan.

Werkplan: [mvsa-conversions](../../plans/mvsa-conversions.md).

### Argumenten en opties

| Naam                    | Verplicht | Betekenis                                      | Default                         |
| ----------------------- | --------- | ---------------------------------------------- | ------------------------------- |
| `path`                  | Ja        | Bron-`.mvsa`-bestand.                          | —                               |
| `--pitch`               | Ja        | Doel-spelling: `doremi`, `abc`, of `vsa`.      | —                               |
| `-o`, `--output`        | Nee       | Uitvoerpad.                                    | `<stem>.normalized.mvsa`        |
| `--octave-style`        | Nee       | `@oct` (canoniek) of `marker` (nog niet klaar) | `@oct`                          |
| `--no-align`            | Nee       | Geen kolomuitlijning na herschrijven.          | uit (wel alignen)               |

### Output

- **stdout**: `Geschreven: <pad>` bij succes.
- **bestand**: genormaliseerde `.mvsa`.

### Exit status

| Exitcode | Betekenis                                    |
| -------- | -------------------------------------------- |
| `0`      | Normalisatie geschreven.                     |
| `1`      | Pad ontbreekt, validatiefout, of normalisatiefout. |

### Voorbeelden

```cmd
vsa mvsa normalize examples\mvsa\alleluia-toon-8.canonieke.mvsa --pitch abc -o generated\alleluia.abc.mvsa
vsa mvsa normalize lied.mvsa --pitch doremi --octave-style @oct
```

## Zie ook

- Draft-spec: [specification-mvsa](../../specification-mvsa/README.md)
- Conversieplan: [mvsa-conversions](../../plans/mvsa-conversions.md)
- Voorbeelden: [examples/mvsa](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa)
- Eenstemmig: [`vsa validate`](validate.md), [`vsa musicxml`](musicxml.md)
