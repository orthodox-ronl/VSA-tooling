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

`d4&-&-` betekent semantisch hetzelfde als `d4&d4&d4`. Bij export naar MusicXML
of MSCZ mag tooling dat samentrekken tot **één aangehouden noot** waarvan de
duur de som is van de slot-duren.

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

Deze regels mogen:

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

`@oct B=-1` verschuift het do-octaaf van de bas: een laddergraad zonder suffix
klinkt één octaaf lager dan bij `@oct B=0`. Een suffix `-` / `+` / `-2` telt
**extra** t.o.v. dat schrijfoctaaf.

Wetenschappelijke cijfers op toonnamen (`g3`, `bb4`) zijn absoluut (wrap bij C)
en **negeren** `@oct`.

## Absolute en relatieve hoogte

Zie ook het werkplan
[`mvsa-v0-syntax.md` §2](../plans/mvsa-v0-syntax.md).

- **EHM** op de stemregel: relatief t.o.v. de lopende toon van die stem.
- **Laddergraad / toonnaam:** zet de lopende toon absoluut t.o.v. `@do`.
- Mix per stem of per hoogte-stuk is toegestaan.
- Op laddergraden: `+` / `-` achter de naam = **octaaf**, geen kruis. Kruis/mol:
  `#` / `b` (prefix of suffix; ook gecombineerd met octaaf als `so-#` / `fa#-`)
  of Nederlandse namen (`fis` / `bes`). Details en verboden spellingen:
  [Syntax — kruis en mol](syntax.md#kruis-en-mol).

Octaafsuffix `so-` = `so-1`; kale `-`/`+` betekent −1 / +1. Andere octaven
vereisen een cijfer (`so-2`).

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

De kuiser mag recite-haakjes niet stilzwijgend weghalen of ELM-`~` niet in
woordstreepjes veranderen.

## Canonieke layout vs. tolerantie

| Onderwerp              | Canoniek                                                                                         | Kuiser                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| Woordstreepjes         | `-` tussen lettergrepen van één woord; geen `-` tussen woorden                                   | Mag spaties rond streepjes normaliseren                         |
| Maat-/sectiestrepen    | Op alle LSATB-regels op dezelfde posities                                                        | Mag strepen van één regel naar de andere kopiëren als eenduidig |
| **Kolomuitlijning**    | Zie [Syntax — canonieke kolomuitlijning](syntax.md#canonieke-kolomuitlijning-lsatb)               | Mag losser zijn; gegenereerde output en voorbeelden zijn strikt |
| Directives             | Sticky tot overrule                                                                              | —                                                               |

**Semantiek** (sync-telling) hangt niet van kolommen af: ongelijke spaties mogen
in losse invoer. De **standaardlayout** die tooling schrijft (en die in
`examples/mvsa` hoort te staan) volgt wél de kolomregel.

## Relatie tot eenstemmige VSA

ELM-betekenissen en de idee van [do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
komen uit VSA 1.0. mvsa herdefinieert **geen** eenstemmige VSA-scopes `{…}` op
de L-regel. Chromatische alias `+` in EHM’s blijft een open punt in VSA zelf;
op mvsa-laddergraden is `+` octaaf.
