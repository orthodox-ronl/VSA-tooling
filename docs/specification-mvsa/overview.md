# Doel en scope

**Status:** draft v0.

## Het idee in het kort

Orthodoxe koorpraktijk vraagt vaak **SATB** (of meer stemmen) met **één
gezongen tekst**, soms in meerdere talen of transliteraties tegelijk. Eenstemmige
[VSA](@) mengt tekst en hoogte in één regel (`{/in}`). Voor meerstemmig typwerk
in VSCode scheidt **mvsa** die rollen:

- **lyrics-regels** (`L:`, `L1:`, …): tekst, duur ([ELM](@)),
  melisma, [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md);
- **stemregels** (`S:`, `A:`, `T:`, `B:`, `S1:`, …): alleen toonhoogte.

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

Zie [Semantiek — directives](semantics.md#directives-do-mode-oct).

## Termen in deze specificatie

| Term             | Betekenis                                                              |
| ---------------- | ---------------------------------------------------------------------- |
| **mvsa-bestand** | Tekstbron (conventioneel `.mvsa`) met secties, systemen en directives. |
| **Sectie** | Muzikale eenheid: een of meer LSATB-systemen, eindigend met ` |     | ` (of specialisatie) op alle lyrics-/stemregels van het laatste systeem. Optioneel met `@sectie`-*id*. |
| **LSATB-systeem** | Maximale aaneengesloten reeks regels waarvan elke inhoudsregel begint met een LSATB-marker. Eindigt altijd op ` | ` of ` |     | ` (of specialisatie). |
| **LSATB-marker**   | Label dat voldoet aan `[LSATB]\d*:` — precies één teken uit `LSATB`, optioneel cijfers, dan `:`. Voorbeelden: `L:`, `L1:`, `S:`, `S2:`, `B:`.                                                                           |
| **Lyrics-regel**   | Regel met marker `L`, `L1`, `L2`, …                                                                                                                                                                                     |
| **Stemregel**      | Regel met marker `S`/`A`/`T`/`B` (eventueel genummerd).                                                                                                                                                                 |
| **Maat**           | Segment tussen maatstrepen; in deze praktijk valt een maat samen met een frase.                                                                                                                                         |
| **L-stuk**         | Brok op een lyrics-regel (grenzen: spatie, lettergreepstreepje, of ELM gevolgd door letters).                                                                                                                           |
| **Hoogte-stuk**    | Brok op een stemregel (alleen spaties scheiden).                                                                                                                                                                        |
| **Slot**           | Deel van een melisma-stuk, gescheiden door `&` binnen één brok; of de ene positie van een niet-melisma-stuk.                                                                                                            |
| **Lengte-positie** | Telbare duur/hoogte-eenheid die lyrics en stemmen moeten delen: elk L-stuk is één positie t.o.v. de stemmen, behalve dat een recite-groep (`( … )`) als **één** positie telt; binnen een melisma telt elk `&`-slot mee. |

Uitgebreide voorbeelden en eerdere ontwerpnotities:
[`docs/plans/mvsa-v0-syntax.md`](../plans/mvsa-v0-syntax.md).
