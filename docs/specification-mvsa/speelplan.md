# Speelplan en speelblokken (draft)

**Status:** draft v0 — fase 1 (syntax, validatie, MXL-expansie, MSCZ-speeltekst).
Fase 2 (herhaal-/volta-notatie op het blad) staat in
[Open punten](open-points.md).

**Voor wie:** wie een vast SATB-antwoord (alleluia, litanie-antwoord) één keer
wil opschrijven en de uitvoeringsvolgorde apart wil vastleggen.

## Idee in het kort

In de `.mvsa` schrijf je elk **speelblok** één keer (`@blok`).
`@speelplan` zegt in welke volgorde die blokken **klinken**.

| Export               | Vorm                                                              |
| -------------------- | ----------------------------------------------------------------- |
| **MXL** (playback)   | **Klinkende vorm:** speelplan volledig uitgeschreven              |
| **MSCZ** (partituur) | **Bladvorm:** elk blok één keer + zichtbare speeltekst (fase 1)   |

Zonder `@speelplan` blijft het huidige gedrag: documentvolgorde = klinkende
volgorde.

Dit is **niet** hetzelfde als VSA-templates `cycle`/`final` (tekstregels →
formule-frasen). Speelplan is voor vaste SATB-blokken in één `.mvsa`.

## Termen

| Term               | Betekenis                                                                 |
| ------------------ | ------------------------------------------------------------------------- |
| **Speelblok**      | Genoemd LSATB-segment (`@blok` *id*); staat één keer in de bron           |
| **Speelplan**      | Niet-lege lijst speelblok-ids = canonieke klinkende volgorde              |
| **Bladvorm**       | Wat op papier staat: elk speelblok één keer, bronvolgorde                 |
| **Klinkende vorm** | Tijdlijn na expansie van het speelplan                                    |
| **Speeltekst**     | Zichtbare markering op het blad (fase 1: `Speel: …` + bloknummers)        |

## Syntax

### `@speelplan`

```text
@speelplan 1, 2, 1, 2, 1, 3
```

- Hoogstens **één** `@speelplan` per bestand.
- Argument: komma-gescheiden speelblok-ids (spaties mogen rond komma’s).
- Staat bij de document-metadata (bij `@do` / `@title`), vóór het eerste
  speelblok.
- Elk id moet voorkomen als `@blok` *id* in hetzelfde bestand.

### `@blok`

```text
@blok 1
L: … |
S: … |
…
@blok 2
L: … ||
…
```

- Opent een nieuwe sectie met dat id (zelfde structurele rol als `@sectie`).
- Id: cijferreeks `[1-9][0-9]*` **of** dezelfde vorm als `@sectie`:
  `[a-z][a-z0-9_-]*`.
- Elk speelblok-id komt hoogstens één keer voor.

`@sectie` blijft beschikbaar buiten speelplannen. In een bestand **met**
`@speelplan` moeten alle muzikale segmenten via `@blok` gelabeld zijn (geen
anonieme sectie, geen `@sectie` als speelblok).

## Herhaalstrepen en speelplan

In een speelblok dat in `@speelplan` voorkomt zijn **`|:`** en **`:|`**
(en **`:||`**) **verboden**. Canonieke volgorde komt uit het speelplan, niet uit
bladherhaling.

Buiten een speelplan-bestand (geen `@speelplan`) blijven `|:` / `:|` / `:||`
gewoon toegestaan.

Toegestaan in speelblokken: `|` (frase) en `||` (sectie-einde).

## Semantiek

1. Expansie: concateneer de maten van de speelblokken in planvolgorde →
   klinkende vorm.
2. Bladvorm wijzigt de bronvolgorde niet: blokken blijven in documentvolgorde,
   elk één keer.
3. Zonder `@speelplan`: geen expansie; labels `@blok` mogen redactioneel zijn
   (ongebruikte ids: geen error).

## Validatie (fase 1)

| Code                         | Ernst   | Wanneer                                                |
| ---------------------------- | ------- | ------------------------------------------------------ |
| `MVSA-SPEELPLAN-SYNTAX`      | error   | Lege lijst, leeg id, ongeldig id-teken                 |
| `MVSA-SPEELPLAN-MULTI`       | error   | Meer dan één `@speelplan`                              |
| `MVSA-SPEELPLAN-UNKNOWN-ID`  | error   | Id in plan zonder `@blok`                              |
| `MVSA-BLOK-ID`               | error   | Ongeldige `@blok`-id                                   |
| `MVSA-BLOK-DUP`              | error   | Twee `@blok` met hetzelfde id                          |
| `MVSA-SPEELPLAN-ANON`        | error   | Anonieme sectie of `@sectie` terwijl speelplan bestaat |
| `MVSA-SPEELPLAN-REPEAT-BAR`  | error   | `\|:` / `:\|` / `:\|\|` in een speelplan-blok          |
| `MVSA-SPEELPLAN-UNUSED`      | warning | `@blok` niet genoemd in het speelplan                  |

## Export

### MXL (`layout=playback`)

Bij aanwezig speelplan: exporteer de **klinkende vorm** (maten herhaald volgens
het plan). Geen afhankelijkheid van MusicXML-`<repeat>` voor de speelduur.

### MSCZ (`layout=partituur`, fase 1)

- Bladvorm: elk `@blok` één keer, bronvolgorde.
- Op de eerste maat: speeltekst `Speel: 1-2-1-2-1-3` (ids met `-` gekoppeld).
- Bij de eerste maat van elk speelblok: zichtbaar bloknummer (bijv. `1`).

Fase 2 mag die speeltekst aanvullen of vervangen door herhaal-/volta-notatie,
zolang de uitvoeringsvolgorde van het blad afleesbaar blijft.

## Voorbeeld

```text
@title "Alleluia - Toon 1"
@do F4
@mode major
@speelplan 1, 2, 1, 2, 1, 3

@oct S=0 A=0 T=-1 B=-1

@blok 1
L:   Al le.&. lu_ i_  a_   … |
S-:  -    -&/  /   \   … |
…

@mscz-newline

@blok 2
L:  Al-&-&-&.&.&-  … |
…

@blok 3
L:  Al-&-&-&.&.&-  … ||
…
```

- Blad (MSCZ): blokken 1, 2, 3 + `Speel: 1-2-1-2-1-3`.
- Coria (MXL): 1+2+1+2+1+3 achter elkaar.

## Bewust later (fase 2)

- Automatische of halfautomatische volta-/herhaalnotatie op MSCZ/PDF.
- CLI-vlag voor compacte MXL (alleen als de consumer herhalingen begrijpt).
- Speelplan over meerdere bestanden; geneste plannen; `until: final` zoals
  templates.
