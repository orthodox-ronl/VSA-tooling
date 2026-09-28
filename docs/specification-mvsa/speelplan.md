# Speelplan en speelblokken (draft)

**Status:** draft v0 — fase 1 (syntax, validatie, MXL-expansie) + fase 2a
(volta voor patroon `(a,b)×n+(a,c)` op partituur). Verdere volta-patronen
staan in [Open punten](open-points.md).

**Voor wie:** wie een vast SATB-antwoord (alleluia, litanie-antwoord) één keer
wil opschrijven en de uitvoeringsvolgorde apart wil vastleggen.

## Idee in het kort

In de `.mvsa` schrijf je elk **speelblok** één keer (`@blok`).
`@speelplan` zegt in welke volgorde die blokken **klinken**.

| Export               | Vorm                                                              |
| -------------------- | ----------------------------------------------------------------- |
| **MXL** (playback)   | **Klinkende vorm:** speelplan volledig uitgeschreven              |
| **MSCZ** (partituur) | **Bladvorm:** elk blok één keer + zichtbare speeltekst (fase 1)   |

**Besluit bladvorm (“als vanzelf”):** optie **A** — compact blad met
conventionele herhaal-/volta-/D.S.-notatie. Niet standaard: speelplan ook op
papier uitschrijven (dat is alleen het vangnet als geen navigatiepatroon past).

**Bestandsgrens:** één `.mvsa` ↔ hoogstens **één** `@speelplan`. Geen nesten
van speelplan in `@sectie`. Meerdere stukken met eigen plan → aparte bestanden.
`@sectie` blijft voor bestanden **zonder** speelplan (schetsen, `--section`).

Zonder `@speelplan` blijft het huidige gedrag: documentvolgorde = klinkende
volgorde. Open herhalingen (litanie: `|:` … `:|` zonder vaste N) horen
**buiten** een speelplan; MusicXML-`<repeat>` blijft daar geldig voor blad én
Coria.

Dit is **niet** hetzelfde als VSA-templates `cycle`/`final` (tekstregels →
formule-frasen). Speelplan is voor vaste SATB-blokken in één `.mvsa`.

## Termen

| Term               | Betekenis                                                                 |
| ------------------ | ------------------------------------------------------------------------- |
| **Speelblok**      | Genoemd LSATB-segment (`@blok` *id*); staat één keer in de bron           |
| **Speelplan**      | Niet-lege lijst speelblok-ids = canonieke klinkende volgorde              |
| **Bladvorm**       | Wat op papier staat: elk speelblok één keer, bronvolgorde                 |
| **Klinkende vorm** | Tijdlijn na expansie van het speelplan                                    |
| **Speeltekst**     | Alleen vangnet als geen navigatiepatroon past (zelden)                    |

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
L: … |
…
@blok 3
L: … ||
…
```

- Opent een **speelblok** (genoemd LSATB-segment voor `@speelplan`). In de
  parser is dat een eigen segment (`origin=blok`), **geen** `@sectie`.
- Id: cijferreeks `[1-9][0-9]*` **of** `[a-z][a-z0-9_-]*`.
- Elk speelblok-id komt hoogstens één keer voor.
- Tussen blokken is **`||` niet verplicht** (en vaak ongewenst: `||` triggert
  in Coria een pauze). Geen `||`-eis tussen blokken (in tegenstelling tot
  expliciete sectie-eindestreep midden in een `@sectie`-bestand).
  Optioneel `||` alleen op het **laatste** blok van het bestand.

**`@sectie` vs `@blok`:** gebruik `@sectie` in bestanden **zonder** `@speelplan`
(export-id, schetsen). In een bestand **met** `@speelplan` moeten alle
muzikale segmenten via `@blok` (geen anonieme sectie, geen `@sectie`).
Nest geen speelplan in een sectie — één plan per bestand.

## Herhaalstrepen en speelplan

In een speelblok dat in `@speelplan` voorkomt zijn **`|:`** en **`:|`**
(en **`:||`**) **verboden**. Canonieke volgorde komt uit het speelplan, niet uit
bladherhaling.

Buiten een speelplan-bestand (geen `@speelplan`) blijven `|:` / `:|` / `:||`
gewoon toegestaan.

Toegestaan in speelblokken: `|` (frase); `||` mag maar is geen eis tussen
blokken (zie hierboven).

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

### MSCZ (`layout=partituur`)

Bladvorm: elk `@blok` één keer in bronvolgorde (tenzij vangnet **expand**).
Geen blok-id-labels boven de maten — navigatietekens zijn genoeg.

De exporter kiest automatisch (eerste match wint):

| Prioriteit | Patroon                                      | Bladtekens                                              |
| ---------- | -------------------------------------------- | ------------------------------------------------------- |
| 1          | plan = blokvolgorde                          | niets                                                   |
| 2          | `(a,b)×n + (a,c)` (3 blokken)                | `\|: a \|1..n. b :\| n+1. c` (volta)                    |
| 3          | `prefix + X×n + suffix` (n≥2)                | `\|: … :\|` (+ `times` als n>2)                         |
| 4          | `blad[0..ds] + blad[segno..fine]`            | Segno + Fine + D.S. al Fine (of D.C. al Fine)           |
| 5          | rest                                         | **expand**: speelplan uitgeschreven op het blad         |

Coria (`playback`) schrijft het speelplan altijd volledig uit (geen jumps).

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

- Blad (MSCZ): `|:` 1 `|1,2.` 2 `:|` `3.` 3.
- Coria (MXL): 1+2+1+2+1+3 achter elkaar.

Trisagion-vorm (`nls-1, nls-2, ksl, doxologie, nls-2, ksl`): Segno bij
`nls-2`, Fine aan het eind van `ksl`, **D.S. al Fine** na `doxologie`.

## Bewust later

- Meer sprongvormen (D.S. al Coda, geneste herhalingen).
- CLI-vlag voor compacte MXL (alleen als de consumer herhalingen begrijpt).
- Speelplan over meerdere bestanden; geneste plannen; `until: final` zoals
  templates.
