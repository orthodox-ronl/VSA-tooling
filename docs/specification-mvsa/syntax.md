# Syntax (draft)

**Status:** draft v0.

Deze pagina beschrijft de **canonieke schrijfvorm** van mvsa. Een kuiser mag
eenvoudige afwijkingen herstellen; de parser mag tolerant zijn, maar tools die
canonieke output schrijven volgen deze regels.

## 1. Bestand

Een mvsa-bestand is UTF-8-tekst. Lege regels en commentaar zijn toegestaan waar
hieronder aangegeven.

| Soort regel  | Vorm                                                                                 |
| ------------ | ------------------------------------------------------------------------------------ |
| Commentaar   | Regel die (na optionele spaties) begint met `#`, of een HTML-commentaar `<!-- … -->` |
| Directive    | Regel die begint met `@` (zie [Semantiek](semantics.md#directives-domodeoct))        |
| Sectiekop    | `@sectie` + spatie + id                                                              |
| LSATB-inhoud | Begint met een LSATB-marker                                                          |

## 2. LSATB-marker

```text
marker ::= [LSATB] digit* ":"
```

| Marker             | Rol                                |
| ------------------ | ---------------------------------- |
| `L`, `L1`, `L2`, … | Lyrics                             |
| `S`, `S1`, `S2`, … | Sopraan (of eerste/tweede sopraan) |
| `A`, `A1`, …       | Alt                                |
| `T`, `T1`, …       | Tenor                              |
| `B`, `B1`, …       | Bas                                |

Andere stem-id’s (`cantus:`) horen **niet** in v0. Na de dubbele punt volgt
inhoud (hoogte- of lyrics-tekst), voorafgegaan door optionele spaties.

## 3. LSATB-systeem

Een **LSATB-systeem** is een aaneengesloten reeks inhoudsregels die elk met een
LSATB-marker beginnen. Tussen twee systemen van **dezelfde sectie** mogen:

- lege regels;
- `#`-commentaar;
- HTML-commentaar;
- directives (`@do`, `@mode`, `@oct`, …).

Een systeem:

1. bevat minstens één lyrics-regel of stemregel (in de praktijk beide);
2. heeft een **vaste volgorde** van markers die voor alle systemen in dezelfde
   sectie gelijk is;
3. bestaat uit een **geheel aantal maten**;
4. **eindigt** op elke LSATB-regel met `|` of `||` (of een specialisatie, zie
   hieronder).

Canoniek staan `|` / `||` / `|:` / `:|` / `:||` op **dezelfde kolomposities**
(zelfde maatgrenzen) op alle LSATB-regels van dat systeem. De kuiser mag ontbrekende
strepen op S/A/T/B aanvullen als minstens één LSATB-regel ze al heeft en de
plaatsing eenduidig is; anders is het een fout.

## 4. Maatstrepen en sectie-einde

| Teken   | Betekenis                                        |
| ------- | ------------------------------------------------ |
| `\|`    | Einde van een maat (frase) binnen de sectie      |
| `\|:`   | Begin herhaling (zoals in VSA/partituurpraktijk) |
| `:\|`   | Einde herhaling                                  |
| `\|\|`  | Einde van de **sectie**                          |
| `:\|\|` | Einde van de sectie mét herhalingsteken          |

v0 vereist **geen** `\|\|:` of `:\|\|:` als overgang naar een volgende sectie.
Een nieuwe sectie begint altijd in een **nieuw** LSATB-systeem (nieuwe set
regels), zodat die gecombineerde tekens niet nodig zijn.

## 5. Sectie

### Begin

Een sectie begint aan het begin van een tekstregel die niet tot een reeds
begonnen sectie behoort, en wel met:

- een sectiekop `@sectie` *id*, of
- een LSATB-marker (anonieme sectie).

```text
@sectie nl1
L: …
S: …
```

**Sectie-id:** `[a-z][a-z0-9_-]*` (bijvoorbeeld `nl1`, `slav1`, `doxologie`).

### Einde

De sectie eindigt wanneer op **alle** LSATB-regels van een systeem een
sectie-eindestreep (`||` of `:||`) staat. Regels **daarna** horen niet meer bij
die sectie (geen “trailing metadata” voor die sectie).

### Meerdere systemen per sectie

Een lange sectie mag over meerdere LSATB-systemen worden gesplitst (leesbaarheid
in de editor). Elk tussensysteem eindigt op `|` (of herhalingsspecialisatie die
geen sectie-einde is). Alleen het **laatste** systeem van de sectie eindigt op
`||` of `:||`.

Alle systemen in één sectie hebben hetzelfde aantal LSATB-regels en dezelfde
marker-volgorde.

## 6. Lyrics-regel (L)

### Geen accolades

In mvsa staan geen VSA-scopes `{…}` op de lyrics-regel. Duur hoort als ELM
achter de lettergreep of in melisma-slots.

### Brokgrenzen (L-stukken)

Een nieuw L-stuk begint na:

1. een **spatie**, of
2. een **lettergreepstreepje** `-` tussen lettergrepen, of
3. een **ELM** waarna meteen weer een letter volgt (`le.&.lu_` → `le.&.` en `lu_`).

`&` binnen een brok scheidt **slots** (melisma), geen nieuwe L-stukken.
Leestekens (`,` `.` `;` …) zijn **geen** L-stuk, ook niet met spaties eromheen.

### Canonieke woordstreepjes

Tussen opeenvolgende lettergrepen van **hetzelfde woord** staat altijd `-`.
Tussen het einde van een woord en het begin van het volgende woord staat **geen**
`-` (wel spatie en/of leesteken). Tussen die lettergrepen mogen wel ELM’s,
recite-`~`, maatstrepen en leestekens staan.

De kuiser mag eenvoudige fouten herstellen (bijvoorbeeld `hei- li- ge` →
`hei-li-ge`).

### Melisma (vorm A)

Meerdere slots op één lettergreep: één L-stuk met `&` tussen ELM-slots, bijvoorbeeld
`Ster~&~&~` of `God_.&_.`.

### Reciteertoon

Prefix `~` op een L-stuk (of een met streepjes aaneengesloten run vanaf die
`~`) markeert een [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)-run.
Die hele run is **één** lengte-positie voor de stemmen.

```text
L: ~hei-li-ge ~On sterf'_. …
```

Zie [Semantiek — pitfalls rond `~`](semantics.md#pitfalls-rond-).

### ELM’s

De ELM-set volgt VSA 1.0 (`_`, `__`, `_.`, `-`, `~`, `.`, `..`, `-.`, `~.`,
samengesteld met `&`). Op de lyrics-regel betekent kale `-` **tussen letters**
een lettergreepstreepje; `-` **als ELM** staat in duurpositie (direct na de
lettergreep of als slot na `&`).

## 7. Stemregel

Op een stemregel staan alleen **hoogte-stukken**, gescheiden door spaties:

- relatief (EHM): `/`, `\`, `-`, `/3`, `#\`, …;
- absoluut: laddergraden `do` `re` `mi` `fa` `so`/`sol` `la` `si`/`ti` en/of
  toonnamen `c`…`b`, `Bb`, `fis`, …;
- octaaf: suffix `-` / `+` / `-1` / `+2` / … of wetenschappelijk cijfer op
  toonnamen (`g3`, `bb4`);
- melisma: `a4&b4&c5` of `d4&-&-` (aanhouden / zelfde toon in volgende slots).

Geen lyrics en geen `_` / `.&.` op de stemregel — die horen in L.

`so` = `sol`; `si` = `ti`. Namen zijn hoofdletterongevoelig waar dat geen
toonnaam-conflicten geeft (`Bb` vs `b`).

## 8. Voorbeeld (één sectie, één systeem)

```text
@do G4
@mode major

@sectie voorbeeld
L: O Hei_.-li~&~-ge God_.&_. | hei-li-ge Ster~&~&~-ke_. ||
S: f#4 g4 f#4&g4 a4 g4&a4    | b4 b4 b4 a4&b4&c5 b4    ||
A: d#4 e4 d#4&d#4 f#4 e4&f#4 | g4 g4 g4 f#4&g4&a4 g4   ||
T: b3  b3 b3&- b3 b3&d4      | d4 d4 d4 d4&-&- d4      ||
B: b2  e3 b2&- b2 e3&f#3     | g3 g3 g3 d3&-&- g3      ||
```
