# Semantiek (draft)

**Status:** draft v0.

## Sync-contract (lengte-posities)

Binnen elke **maat** moeten alle lyrics-regels van het systeem en alle
stemregels **dezelfde structuur van lengte-posities** hebben:

1. Hetzelfde aantal L-stukken (events), waarbij een recite-run als **één**
   L-stuk / één positie telt;
2. Bij elk melisma-stuk: hetzelfde aantal `&`-slots in elke lyrics-regel en in
   elke stemregel.

Kolomuitlijning in de editor is voor **invoer** optioneel comfort: wat telt voor
validatie is de **telling**, niet het aantal spaties. Gegenereerde en canonieke
bestanden volgen wél de
[canonieke kolomuitlijning](syntax.md#canonieke-kolomuitlijning-lsatb).

### Ongelijke partituurnoten onder één lettergreep

Soms beweegt de sopraan onder één lettergreep over drie tonen, terwijl de tenor
één noot aanhoudt. Op de lyrics-regel staan dan drie slots; de tenor schrijft
toch drie slots, met aanhouden:

```text
L: … Ster~&~&~ …
S: … a4&b4&c5 …
T: … d4&-&- …
```

`d4&-&-` betekent semantisch hetzelfde als `d4&d4&d4`. Bij export naar **MSCZ**
(partituur) trekt tooling opeenvolgende melisma-noten op dezelfde hoogte samen
tot **één noot** waarvan de duur de som is van de slot-duren. Playback-``.mxl``
houdt de slots apart (Coria).

## Reciteertoon

Een L-stuk tussen `( … )` is een recite-run: meerdere lettergrepen (en
eventueel meerdere woorden), **één** hoogte-stuk per stem. Optionele ELM
direct na `)` zet de duur; zonder ELM geldt de recite-standaard (export:
breve). Uitgewerkte voorbeelden: [Syntax — reciteertoon](syntax.md#reciteertoon).

```text
L: (Eer aan de Va-der,) Geest_. |
S: f#4                      f#4 |
```

Hier zijn twee posities: de recite-groep, daarna `Geest_.` (zelfde toon, andere
duur — daarom een apart L-stuk).

## Directives: `@do`, `@mode`, `@oct`

Praktische beschrijving van alle gedefinieerde `@`-keywords (inclusief
`@title`, `@tekst`, `@sectie`, `@start`): [Keywords](keywords.md).

Deze sticky toon-directives mogen:

- bovenaan het bestand;
- aan het begin van een sectie (vóór of na `@sectie`);
- **tussen** LSATB-systemen van dezelfde sectie.

**Geldigheid:** een directive geldt vanaf het **eerstvolgende** LSATB-systeem
onder die regel, totdat dezelfde soort directive opnieuw wordt gezet. Eerdere
systemen in de sectie houden de oude waarde. Types overrulen elkaar niet:
`@oct` laat `@do` ongemoeid.

| Directive | Betekenis                                                                                                                   | Default          |
| --------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `@do`     | Grondtoon van de [do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md), bv. `F4` of `G4` | `F4`             |
| `@mode`   | Modus, bv. `major`                                                                                                          | `major`          |
| `@oct`    | Schrijfoctaaf per stem, bv. `@oct S=0 A=0 T=-1 B=-1`                                                                        | alle stemmen `0` |

Ontbrekende stem in `@oct` → `0` voor die stem.

### Schrijfoctaaf

`@oct B=-1` verschuift het **schrijf-do** van de bas: laddergraden zonder
suffix, beginankers (`B-:` / `T\5:`), EHM-eindankers (`||-`, `||\3`) en
**toonnamen a–g zonder wetenschappelijk cijfer** tellen t.o.v. dat schrijf-do
(`@do` + `@oct` voor die stem). Een suffix `-` / `+` / `-2` op een laddergraad
of toonnaam telt **extra** t.o.v. het schrijfoctaaf.

**Do-octaaf:** a–g zonder cijfer liggen in het halfopen interval
`[schrijf-do, schrijf-do + 12)`. Bij `@do F4` is `c` = C5 (= so), niet C4.

Wetenschappelijke cijfers op toonnamen (`g3`, `bb4`, `c4`) zijn absoluut
(wrap bij C) en **negeren** `@oct`.

## Absolute en relatieve hoogte

Zie ook het werkplan
[`mvsa-v0-syntax.md` §2](../plans/mvsa-v0-syntax.md) en
[Syntax — regelidentifier](syntax.md#regelidentifier).

De **regelidentifier** zet de default/start van een stemregel:

| Regelidentifier | Stijl-default                         | Beginanker                                                      |
| --------------- | ------------------------------------- | --------------------------------------------------------------- |
| `S:` (geen EHM) | Absoluut (do-re-mi of a–g)            | Geen; eerste absolute token zet de lopende toon                 |
| `S-:` / `T\6:`  | Relatief (vsa-achtig)                 | De EHM in de identifier (zelfde rol als `@start` voor die stem) |

Daarnaast op de regel zelf:

- **EHM** in een hoogte-stuk: relatief t.o.v. de lopende toon van die stem.
- **Laddergraad / toonnaam:** zet de lopende toon absoluut t.o.v. het
  schrijf-do (`@do` + `@oct`; anker, ook op een relatieve regel).
- Mix per stem of per hoogte-stuk is toegestaan.
- Op laddergraden: `+` / `-` achter de naam = **octaaf**, geen kruis. Kruis/mol:
  `#` / `b` (prefix of suffix; ook gecombineerd met octaaf als `so-#` / `fa#-`)
  of Nederlandse namen (`fis` / `bes`). Details en verboden spellingen:
  [Syntax — kruis en mol](syntax.md#kruis-en-mol).

Octaafsuffix `so-` = `so-1`; kale `-`/`+` betekent −1 / +1. Andere octaven
vereisen een cijfer (`so-2`).

`@start S=-` en `S-:` betekenen voor stem `S` hetzelfde beginanker; de
identifier-vorm is de voorkeur als de EHM bij die stemregel hoort.

### Lopende toon over systeembraken

De **lopende toon** van elke stem loopt door over LSATB-systeembraken (lege
regel tussen systemen), in de volgorde waarin export of validatie de systemen
afloopt:

| Context                          | Volgorde                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------- |
| Export **playback** (``.mxl``)   | `sections_for_layout`: bij `@speelplan` de **klinkende** (uitgeschreven) vorm |
| Export **partituur** (``.mscz``) | Bladvorm: documentvolgorde, elk speelblok één keer (tenzij expand-vangnet)    |
| Eindanker-check / normalize      | Documentvolgorde                                                              |

Gevolg: een kale `-` (of `~` als hoogte) aan het **begin** van een nieuw
systeem betekent “zelfde toon als de laatste klinkende noot van die stem in
het vorige systeem” — precies wat soft-wrap na import schrijft.

**Beginanker wint:** staat op de nieuwe stemregel een EHM in de
regelidentifier (`S-:`, `T\6:`, …) of een expliciete `@start`-toewijzing voor
die stem, dan wordt de lopende toon **opnieuw gezet** en geldt leading `-`
ten opzichte van dat anker (niet ten opzichte van het vorige systeem).

Zonder beginanker en zonder eerdere toon blijft het gedrag: `-` klinkt als
schrijf-do (zoals binnen één systeem vóór de eerste absolute toon).

## Ankers: zetten vs. checken

| Plaats                          | Rol                                                             | Voorbeeld     |
| ------------------------------- | --------------------------------------------------------------- | ------------- |
| EHM in de **regelidentifier**   | **Zet** de lopende toon (beginanker), zoals `@start`            | `S-:`, `T\6:` |
| Token **aan de maatstreep**     | **Checkt** alleen de lopende toon na die maat; wijzigt die niet | `\|mi`, `\|/` |
| Laddergraad als **hoogte-stuk** | Zet de lopende toon (klinkt / telt als lengte-positie)          | `… mi \|`     |

### Eindanker (maatstreep)

Vorm en disambiguatie:
[Syntax — eindanker aan de maatstreep](syntax.md#eindanker-aan-de-maatstreep).

- **Kale streep** (`|`, `||`, …): geen marker, geen check. (Geen equivalent van
  VSA-`[:]`: die lege vorm bestaat in mvsa niet.)
- **EHM** na de streep (`|/`, `|-`, `|\6`, …): dezelfde EHM-inhoud als in VSA
  (zonder `[`…`:]`). De verwachte ladderpositie is die van de EHM t.o.v. het
  **schrijf-do** van die stem (`@do` + `@oct`); die wordt vergeleken met de
  berekende lopende toon van de stem na de maat.
- **Absoluut** (`|mi`, `||fa`, `|g4`, …): verwachte toon absoluut t.o.v. het
  schrijf-do / wetenschappelijk octaaf.

Bij mismatch: error. Bij match: de lopende toon blijft ongewijzigd (geen reset).

## Pitfalls rond `~`

Het teken `~` is op de L-regel **alleen** ELM (duur). Recite markeer je met
`( … )`, niet met een leading `~`.

| Rol                       | Waar                                       | Voorbeeld          |
| ------------------------- | ------------------------------------------ | ------------------ |
| Recite-groep              | Tussen `(` en `)`                          | `(hei-li-ge)`      |
| ELM (duur 1×, geen glyph) | Direct na lettergreep, na `)`, of als slot | `li~`, `(ia,)~`    |

**Gevolg:**

- `(hei)` is recite op “hei”.
- `hei~` is lettergreep “hei” met ELM-duur `~` (geen recite).
- In melisma’s heeft ELM-`~` de voorkeur boven ELM-`-` vóór een
  lettergreepstreepje: schrijf `li~&~-ge`, niet `li-&--ge` (dubbele `-` is
  ambigu voor lezer en kuiser).
- **Canoniek** op L: lone standaard-lengte is **impliciet** (geen `~` na de
  lettergreep). Schrijf `~` wél in `&`-melisma (`ziel~&~`) en na recite-`)`
  als de duur geen breve is (`()~`, `(ia)~` — zonder ELM na `)` = breve).
  Kale ELM-`-` is invoer-tolerantie (kuiser → eerst `~`, daarna lone `~`
  weglaten). Woordstreepje met extra breedte: spaties **vóór** `-letter`
  (`…_&_  -li`).

De kuiser mag recite-haakjes niet stilzwijgend weghalen of ELM-`~` niet in
woordstreepjes veranderen.

## Canonieke layout vs. tolerantie

| Onderwerp              | Canoniek                                                                                         | Kuiser                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Standaard-lengte op L  | Lone `~` weggelaten; `~` bij `&`-melisma en na `)` (niet-breve); `-` hoort bij lettergrepen      | Eenduidige ELM-`-` → `~`, daarna lone `~` weg; waarschuwt bij ambiguë `-` (regel + kolom)       |
| Woordstreepjes         | `-` direct vóór de volgende lettergreep; bij breedte spaties *ervóór* (`hei  -li`)               | Geen stille `hei- li`→`hei-li`-collapse; Pyphen-warnings bij ontbrekende / verdachte streepjes  |
| Maat-/sectiestrepen    | Op alle LSATB-regels op dezelfde posities                                                        | Mag strepen van één regel naar de andere kopiëren als eenduidig                                 |
| **Kolomuitlijning**    | Zie [Syntax — canonieke kolomuitlijning](syntax.md#canonieke-kolomuitlijning-lsatb)              | Mag losser zijn; gegenereerde output en voorbeelden zijn strikt                                 |
| Directives             | Sticky tot overrule                                                                              | —                                                                                               |

**Semantiek** (sync-telling) hangt niet van kolommen af: ongelijke spaties mogen
in losse invoer. De **standaardlayout** die tooling schrijft (en die in
`examples/mvsa` hoort te staan) volgt wél de kolomregel.

## Relatie tot eenstemmige VSA

ELM-betekenissen en de idee van [do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
komen uit VSA 1.0. mvsa herdefinieert **geen** eenstemmige VSA-scopes `{…}` op
de L-regel. Chromatische alias `+` in EHM’s blijft een open punt in VSA zelf;
op mvsa-laddergraden is `+` octaaf.
