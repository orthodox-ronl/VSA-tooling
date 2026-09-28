# Doel en scope

**Status:** draft v0.

## Het idee in het kort

Orthodoxe koorpraktijk vraagt vaak **SATB** (of meer stemmen) met **één
gezongen tekst**, soms in meerdere talen of transliteraties tegelijk. Eenstemmige
[VSA](@) mengt tekst en hoogte in één regel (`{/in}`). Voor meerstemmig typwerk
in VSCode scheidt **mvsa** die rollen:

- **lyrics-regels** (`L:`, `L1:`, `lyrics:`, …): tekst, duur ([ELM](@)),
  melisma, [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md);
- **stemregels** (`S:`, `A:`, `T:`, `B:`, `S1:`, `cantus:`, …): alleen
  toonhoogte. Optioneel staat een [EHM](@) in de
  [regelidentifier](#termen-in-deze-specificatie) (`S-:`, `T\6:`): dan is de
  hoogtestijl van die regel **relatief** (vsa-achtig) met die EHM als
  beginanker; zonder EHM is de stijl **absoluut** (do-re-mi of a–g).

Maatstrepen houden lyrics en stemmen synchroon. Een **sectie** is een muzikaal
rijtje maten met een duidelijk eind (`||`). Een **LSATB-systeem** is het
editor-blok van opeenvolgende lyrics-/stemregels in VSCode (vaak vijf regels,
soms meer bij `L1`/`L2` of `S1`/`S2`).

```text
@do F4
@mode major

@sectie openingsfrase
L: … | … ||
S: … | … ||
A: … | … ||
T: … | … ||
B: … | … ||
```

Dit is **geen** MuseScore-pagina-“systeem” (layout op A4). Pagina-indeling hoort
bij rendering/export, niet bij mvsa-brontekst.

## Doel

- SATB (+ eventueel meerdere lyrics of verdubbelde stemmen) intypbaar en
  diffbaar in git;
- tekst niet vier keer over S/A/T/B dupliceren;
- bekende VSA-duurtekens (ELM) en relatieve/absolute hoogte hergebruiken;
- pad openhouden naar validate/export zonder dat die tools nu al bestaan.

## Niet-doelen (deze draft)

- Vervanging van eenstemmige VSA 1.0;
- blokhergebruik en template-projectie als norm;
- CLI-werkstromen en kuiser-implementatie (wel: gedragseisen voor canonieke vorm);
- volledige gelijkschakeling van chromatische `+` in eenstemmige VSA-EHM.

## Defaults

| Directive | Default als weggelaten |
| --------- | ---------------------- |
| `@do`     | `F4`                   |
| `@mode`   | `major`                |
| `@oct`    | `0` voor elke stem     |

Zie [Keywords](keywords.md) en
[Semantiek — directives](semantics.md#directives-do-mode-oct).

## Termen in deze specificatie

| Term                | Betekenis                                                                                                                                                                                                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **mvsa-bestand**    | Tekstbron (conventioneel `.mvsa`) met secties, systemen en directives.                                                                                                                                                                                                                                                           |
| **Sectie**          | Muzikale eenheid (`@sectie` of anoniem): een of meer LSATB-systemen. Eindigt canoniek met `\|\|` (of `:\|\|`); ook impliciet bij een nieuwe `@sectie`, bij EOF, of (later) bij `::: mvsa-notatie`. Validate mag `MVSA-SECTIE-IMPLICIT` geven. **Niet** van toepassing op speelblokken (`@blok`) — zie [Speelplan](speelplan.md). |
| **Speelblok**       | Genoemd segment (`@blok` *id*) voor een speelplan. Geen `\|\|`-eis tussen blokken. Eén `@speelplan` per bestand.                                                                                                                                                                                                                 |
| **LSATB-systeem**   | Aaneengesloten reeks regels met een [regelidentifier](#termen-in-deze-specificatie); `#`-commentaar ertussen mag; een **lege regel eindigt** het systeem. Eindigt altijd op `\|` of `\|\|` (of specialisatie).                                                                                                                   |
| **regelidentifier** | Label aan het begin van een inhoudsregel: `stemidentifier` + optionele [EHM](@) + `:`. Voorbeelden: `L:`, `L1:`, `S:`, `S-:`, `T\6:`, `cantus:`. Zie [Syntax — regelidentifier](syntax.md#regelidentifier).                                                                                                                      |
| **stemidentifier**  | Naamdeel van de regelidentifier: `[A-Za-z0-9_-]+`, waarbij het **laatste** teken geen `_` of `-` mag zijn. Begint de naam met `L` of `l`, dan is het een lyrics-regel; anders een stemregel.                                                                                                                                     |
| **Lyrics-regel**    | Regel waarvan de stemidentifier met `L` of `l` begint (`L:`, `L1:`, `lyrics:`). Een EHM in die regelidentifier is een fout.                                                                                                                                                                                                      |
| **Stemregel**       | Regel waarvan de stemidentifier niet met `L`/`l` begint (`S:`, `A:`, `cantus:`, …). Met EHM in de identifier: relatieve hoogtestijl + beginanker; zonder EHM: absolute stijl.                                                                                                                                                    |
| **Maat**            | Segment tussen maatstrepen; in deze praktijk valt een maat samen met een frase.                                                                                                                                                                                                                                                  |
| **L-stuk**          | Brok op een lyrics-regel (grenzen: spatie, lettergreepstreepje, of ELM gevolgd door letters).                                                                                                                                                                                                                                    |
| **Hoogte-stuk**     | Brok op een stemregel (alleen spaties scheiden).                                                                                                                                                                                                                                                                                 |
| **Slot**            | Deel van een melisma-stuk, gescheiden door `&` binnen één brok; of de ene positie van een niet-melisma-stuk.                                                                                                                                                                                                                     |
| **Lengte-positie**  | Telbare duur/hoogte-eenheid die lyrics en stemmen moeten delen: elk L-stuk is één positie t.o.v. de stemmen, behalve dat een recite-groep (`( … )`) als **één** positie telt; binnen een melisma telt elk `&`-slot mee.                                                                                                          |

Uitgebreide voorbeelden en eerdere ontwerpnotities:
[`docs/plans/mvsa-v0-syntax.md`](../plans/mvsa-v0-syntax.md).
