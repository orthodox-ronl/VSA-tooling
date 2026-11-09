# Eigen partituur-SVG — werkplan

| Veld            | Waarde                                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan; **niet normatief**. Schilder en `mvsa svg --engine eigen` bestaan. Nog geen standaardproduct en geen wijziging van het productiescherm.               |
| **Doel**        | Vastleggen hoe een eigen tekening uit Score-IR de keuzes van MuseScore en OSMD kan overnemen, en wanneer die tekening het schermpad mag worden                  |
| **Bewijs**      | Spike op [pull request 75](https://github.com/orthodox-ronl/VSA-tooling/pull/75): Alleluia toon 8, Alleluia toon 2, vredeslitanie (1a)                          |
| **Eigenaar**    | Tekening en contracten: [VSA-tooling](@bron). Inbedden op de site: bibliotheek. Samenstelling en colofon: bibliotheek, niet deze tekening                       |
| **Gerelateerd** | [contract-index](../formats/contract-index.md), [kale-muziek §4](kale-muziek-svg-en-uitgaven.md), [partituur-ir](partituur-ir.md), [CoriB](corib-mvp.md)        |

Het productiescherm blijft tot een apart besluit:
Score-IR → MusicXML uit die Score-IR → OSMD.
OSMD is het programma waarmee de site de partituur nu tekent.
MuseScore blijft het pad voor bewerken en voor de afdruk.
Dit werkplan vervangt dat pad niet.

---

## 0. Antwoord eerst

De spike liet zien dat Score-IR al de bedoelde partituurvorm bevat
(twee balken, recite, melisma, VSA van de sopraan). De eerste
tekening oogde nog als een schets; dat zat in de verf, niet in het model.
Met Bravura-contouren voor de noten en een echte accolade wordt het
beeld herkenbaar als partituur.
Dat pad is kansrijker dan OSMD blijven bijsturen, omdat OSMD de
afspraken niet zelf tekent: elke afspraak wordt een omweg via MusicXML
en een aanpassing achteraf.

De tekening die hieruit moet groeien, leest dezelfde Score-IR als OSMD
nu indirect leest. Alle keuzes die voor MuseScore en voor OSMD al
vastliggen, moeten in die tekening terecht kunnen. Nieuwe smaak
(pixelgelijk aan MuseScore, een tweede notenbalkmodel, OSMD nu
uitschakelen) hoort er niet bij.

Het lettertype voor zangtekst, cues en woorden is **Source Sans 3**,
gewicht 400, in de maten van MuseScore (checklist S7, leesbaarheid L2:
zangtekst 13 pt, cues 12 pt). De bestanden liggen in
`scripts/osmd-svg/fonts/`. De spike zette DejaVu Sans. DejaVu wordt
niet het productlettertype. Of een zwaarder gewicht later prettiger
leest, blijft open; de tekening volgt MuseScore tot dat opnieuw
bekeken wordt.

Een tropaar (en elk ander stuk) moet in meer dan één beeld op het
scherm kunnen. De pagina-Markdown zet het startbeeld. De lezer wisselt
in de UI. De tekening kiest dat beeld niet zelf. Zie §4.

---

## 1. Wat de spike al liet zien

De spike staat in `examples/spikes/score-ir-svg/` op de branch van
pull request 75. Drie stukken, elk als één SVG:

| Stuk                         | Bron                                                         | Wat het beeld raakt                                      |
| ---------------------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| Alleluia toon 8              | `examples/bug-cases/corib/alleluia-toon-8.mvsa`              | Recite, melisma «lu», C5 boven de alt-G, dubbele streep  |
| Alleluia toon 2              | `examples/bug-cases/corib/alleluia-toon-2.mvsa`              | Liggende VSA-streep binnen een melisma (`-&/`)           |
| Vredeslitanie (1a)           | `examples/mvsa/1a-vredeslitanie.mvsa`                        | Enkele streep, herhaling, dubbele streep, cues           |

Wat op die platen al op een partituur lijkt: notenkoppen, sleutels,
voortekens, stokrichting, de stokloze `||O||`, de accolade, de
maatstrepen en de herhaalpuntjes.

Wat op de spike nog een schets was: de bogen zijn eenvoudige krommen,
de afstand tussen noten is grof, er was één systeem per stuk (ook waar
de bron `@nieuw-systeem` zet), en de zangtekst was nog niet Source Sans 3.
De schilder in `src/vsa/eigen_svg.py` zet Source Sans 3 (gewicht 400,
ingebed vanuit `scripts/osmd-svg/fonts/`), een nieuw systeem waar
Score-IR `newSystem` zet, de S13-extender, een volta-haak over het
slot, bundels op achtsten en korter, en een boog die de stokken volgt.
Een regel die langer is dan `--system-width` (default 760) breekt af,
ook midden in een maat. De nootafstand blijft grof.
Het koppelteken in «ont-ferm» volgt het woordstreepje in de bron
(`syllabic` begin/end), ook als die lettergreep één noot is.

Het SVG heeft een viewBox en de eigen breedte. Een pagina mag het
verkleinen (`max-width: 100%`); het rekt niet uit. Een regel die langer
is dan de regelbreedte breekt af. Een venster dat ná het tekenen nog
smaller wordt, verkleint de plaat. Opnieuw tekenen op die breedte is
`--system-width`. Zie §7 en §8.

---

## 2. Uitgangspunt

Eén bedoelde partituurvorm. Drie manieren om die vorm uit te voeren:

```text
.mvsa / .vsa / .mscz
        │
        ▼
    Score-IR          ← de bedoelde vorm (al de contracten S8, S13, …)
        │
        ├── MusicXML uit Score-IR → OSMD          (huidig scherm)
        ├── MuseScore (mscz, svg, pdf)            (bewerken en afdruk)
        └── eigen schilder → SVG                  (dit werkplan)
```

Score-IR is het JSON-tussenmodel. De schilder leest dat model.
De schilder leest geen MusicXML en geen MuseScore-bestand.
Daardoor hoeft een afspraak niet nog eens door OSMD of door MuseScore
heen voordat het beeld klopt.

De contracten blijven in de hubs van de
[contract-index](../formats/contract-index.md).
Dit werkplan herhaalt de regels niet. Een testrun noemt het contract-id
(bijvoorbeeld checklist S8) en wijst naar de hub.

---

## 3. Keuzes die mee moeten

Elke rij is een keuze die voor MuseScore of voor OSMD al gemaakt is.
De kolom «Spike» zegt of pull request 75 die keuze al tekende.
«Fase» wijst naar §7. De schilder in `src/vsa/eigen_svg.py` dekt de
fase-2-rijen die `tests/test_eigen_svg.py` vastzet: drie beelden,
Source Sans 3, stokrichting, recite, extender, herhaling, cues,
maatnummer, `@nieuw-systeem`, en de woorden Segno / Fine / D.S.
Een volledige volta-haak is dat nog niet: de schilder zet het
voltanummer en een kort streepje. Checklist S20 blijft daarmee open.

### 3.1 Bladbeeld

| Id              | Keuze                                                                 | Spike                 | Fase |
| --------------- | --------------------------------------------------------------------- | --------------------- | ---- |
| Checklist S2    | Twee balken: sopraan+alt (G-sleutel) en tenor+bas (F-sleutel)         | ja                    | 2    |
| Checklist S3    | Geen partijnamen op de balken                                         | ja (geen namen gezet) | 2    |
| Checklist S4    | Stok sopraan en tenor omhoog, alt en bas omlaag                       | ja                    | 2    |
| Checklist S5    | Zangtekst één keer, tussen de balken                                  | ja                    | 2    |
| Leesbaarheid M4 | Geen lege derde balk                                                  | ja                    | 2    |
| Checklist S1    | Kern K1–K7 gelijk aan de betekenis van de noten                       | deels                 | 2    |

### 3.2 Lettertype en maten van de tekst

| Id                            | Keuze                                                                 | Spike                         | Fase |
| ----------------------------- | --------------------------------------------------------------------- | ----------------------------- | ---- |
| Checklist S7, leesbaarheid L2 | Zangtekst Source Sans 3, 13 pt, gecentreerd op de nootkop             | nee (DejaVu, vette 22 px)     | 2    |
| Leesbaarheid L2               | Cues Source Sans 3, 12 pt                                             | nee (DejaVu 13 px)            | 2    |
| Checklist S7                  | Woordtekst Source Sans 3, 12 pt; titel 18 pt waar een titel móet      | n.v.t. op kale muziek         | 5    |
| CLI                           | `--lyrics-font` / `--cue-font` mogen het lettertype overschrijven     | nee                           | 3    |

De bestanden staan al in de repo:
`scripts/osmd-svg/fonts/` (WOFF2, SIL Open Font License via Fontsource).
De schilder gebruikt die bestanden, niet een lettertype dat toevallig
op de pc van de beheerder staat. Anders valt de zangtekst terug op
een ander gezicht, zoals bij MuseScore gebeurt wanneer Source Sans 3
niet geïnstalleerd is (schermeis O6).

Notenkoppen, sleutels, voortekens, de accolade en de herhaalpuntjes
komen uit **Bravura** (SMuFL, eveneens SIL Open Font License).
Dat zijn contouren in het SVG, geen lettertype dat de kijker moet
hebben. MuseScore 4 tekent met een ander SMuFL-lettertype (Leland).
Het verschil in notenkop is klein. Bravura blijft de aanbeveling,
omdat de spike die contouren al gebruikt en omdat het bestand dan
geen tweede muzieklettertype nodig heeft.
Een gewone maatstreep, een dubbele streep en een slotstreep blijven
lijnen. Daar is geen glyph voor nodig; MuseScore doet dat ook zo.

### 3.3 Recite, melisma, strepen

| Id                                                 | Keuze                                                                                                 | Spike                                                                      | Fase |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---- |
| Checklist S8, leesbaarheid R2–R6                   | Lange recite: randnoten, stokloze `\|\|O\|\|`, overige middenlettergrepen alleen als tekst            | ja op de twee alleluia's                                                   | 2    |
| Checklist S8                                       | Geen breve als niet élke klinkende stem de recite deelt                                               | niet apart getest                                                          | 2    |
| Checklist S9, S16, leesbaarheid M6, M9, M10        | Enkele streep, dubbele streep, slotstreep, herhaling met puntjes, geen lege maat vóór `\|:`           | litanie: enkel, herhaling, dubbel                                          | 2    |
| Checklist S13, leesbaarheid L4, leesbaarheid S2–S4 | Lyric op de eerste noot, extender ná die lettergreep, slur alleen over de noten die van toon wisselen | slur ja; extender nog niet (de spike zette VSA-onderstreping in de plaats) | 2    |
| Leesbaarheid R4                                    | Geen extender en geen fraseslur onder de recite                                                       | ja (geen extender gezet)                                                   | 2    |
| Leesbaarheid R7                                    | Same-pitch melisma al compact in Score-IR, inclusief stip                                             | de schilder tekent de noot die de IR geeft                                 | 2    |
| Leesbaarheid L3                                    | Koppelteken tussen lettergrepen is geen melisma                                                       | ja, waar Score-IR `begin`/`middle`/`end` zet                               | 2    |
| Checklist S10, leesbaarheid M1                     | Maatnummer bij de eerste maat van elk systeem                                                         | nee                                                                        | 2    |
| Leesbaarheid M3, schermeis O4                      | Geen maatsoort op het blad                                                                            | ja (niet gezet)                                                            | 2    |

De VSA-strepen uit de spike zijn een beeld, geen vervanging van
checklist S13. In het beeld «noten met VSA» tekent de muzieklaag de
extender en de slur, en de VSA-laag de hoogte van de sopraan plus de
lengte-onderstreping. In het beeld «noten zonder strepen» ontbreekt
die VSA-laag. In het beeld «kale VSA» ontbreken de balken. Zie §4.2.

### 3.4 Cues, systeem, accolade

| Id                                  | Keuze                                                                                          | Spike                                      | Fase |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------ | ---- |
| Checklist S15, S19, leesbaarheid C1 | `@tekst` boven de gecue-de maat; meer regels als de bron een regeleinde heeft; spaties blijven | litanie: ja, nog grof                      | 2    |
| Leesbaarheid C6                     | Cue mag de maat iets verbreden; een holle maat met de noten links is slechter                  | deels (maat wordt breder dan de tekst)     | 2    |
| Checklist S14, S18, leesbaarheid C5 | Accolade alleen aan het begin van een systeem                                                  | ja zolang er één systeem is                | 2    |
| `@nieuw-systeem`                    | Nieuwe regel. `@tekst` dwingt zelf geen nieuwe regel af (leesbaarheid C2)                      | nee: de litanie blijft één lange regel     | 2    |
| Schermeis O7                        | Tekst aan een systeemovergang niet afkappen                                                    | n.v.t. tot er meer systemen zijn           | 2    |
| Schermeis O8–O9                     | Cue blijft bij de maat; lange cue mag naar één regel als die past                              | nee                                        | 2    |
| Schermeis O10                       | Noten en lettergrepen in de maat centreren waar dat de leesbaarheid dient                      | nee (tijd-raster)                          | 5    |

### 3.5 Wat níet op de kale tekening staat

Kale muziek is alleen de notenbalk. Titel, componist, copyright en
colofon komen uit de samenstelling van de pagina
([kale muziek](kale-muziek-svg-en-uitgaven.md)).

| Id                                       | Keuze                                                             | Spike           | Fase            |
| ---------------------------------------- | ----------------------------------------------------------------- | --------------- | --------------- |
| Schermeis O1                             | Geen titel, componist of copyright in het SVG                     | ja              | 2               |
| Schermeis O2                             | Geen partijnamen                                                  | ja              | 2               |
| Schermeis O3, leesbaarheid acceptatie 12 | Geen metronoom-teken. `@tempo` blijft beschikbaar om af te spelen | ja (niet gezet) | 2               |
| Checklist P4, leesbaarheid P6            | Copyright-regel en colofon: later, en niet in de kale SVG         | n.v.t.          | buiten dit plan |

### 3.6 Navigatie op het blad

| Id              | Keuze                                                                                                           | Spike | Fase |
| --------------- | --------------------------------------------------------------------------------------------------------------- | ----- | ---- |
| Checklist S20   | Volta-haken alleen boven de sopraan-alt-balk. Herhaalstrepen op beide balken. Segno en Coda niet in de accolade | nee   | 2    |
| Speelplan       | Zelfde tekens als partituur-MusicXML (Segno, Fine, D.S., Coda)                                                  | nee   | 2    |

Een stuk met volta of Segno hoort in de proefset vóórdat checklist S20
«gedaan» wordt. De drie spike-stukken hebben dat niet.
`examples/bug-cases/trisagion-8a-hemelum.mvsa` dekt herhaling plus
`@nieuw-systeem`. Een speelplan-stuk komt uit
[speelplan](../specification-mvsa/speelplan.md).

### 3.7 Scherm, afdruk, oefenen

| Keuze                                                                       | Waar de keuze nu staat                                    | Eigen tekening                                                                                          |
| --------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Scherm is geen MuseScore-pagina                                             | [kale muziek §4](kale-muziek-svg-en-uitgaven.md)          | De tekening is één of meer systemen, geen A4-pagina                                                     |
| Afdruk bouwt op een hoge kale SVG, gesneden naar A4                         | dezelfde afspraak                                         | Blijft MuseScore tot fase 6 een eigen besluit is                                                        |
| Oefenen (CoriB) gebruikt hetzelfde beeld; solo en cursor zijn een laag erop | [CoriB](corib-mvp.md), [partituur-ir §7](partituur-ir.md) | De noten krijgen stabiele kenmerken (`data-voice`, maat, index). De speler zelf is een ander werkplan   |
| Telefoon en tablet zonder handmatig zoomen                                  | [gebruikseisen §2](gebruikseisen-dragers.md)              | Meeschalen is het spike-bewijs. Opnieuw afbreken bij een smal venster is fase 5                         |
| Vier losse partijen voor Coria                                              | checklist M-reeks                                         | Blijft het afspeelbestand voor Coria. De eigen tekening is de partituur (twee balken), niet dat bestand |

---

## 4. Keuzes

### 4.1 Lettertype en muziektekens

| #   | Stand        | Keuze                                                                                                                                                                        |
| --- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K1  | gekozen      | Zangtekst en cues in Source Sans 3, gewicht 400, maten uit leesbaarheid L2 (13 pt en 12 pt). Gelijk aan MuseScore. Een zwaarder gewicht kan later, als de platen dat vragen. |
| K2  | aanbeveling  | Notenkoppen, sleutels, voortekens, accolade en herhaalpuntjes als Bravura-contouren. Leland (MuseScore 4) blijft mogelijk, maar vraagt een tweede contourset.                |
| K4  | uitgangspunt | OSMD en MuseScore blijven staan tot fase 4. De site en de afdruk hebben een werkend pad.                                                                                     |

### 4.2 Drie beelden, plus schrift

K3 als «VSA aan of uit» is de verkeerde vraag. Een stuk, bijvoorbeeld
een tropaar, moet in drie beelden kunnen. De pagina die op het scherm
staat (de Markdown van die pagina) noemt het startbeeld. De UI laat de
lezer wisselen. De schilder levert de beelden; de schilder kiest niet
welk beeld de pagina opent.

| Beeld                  | Wat de lezer ziet                                                                 | Waar dat vandaag al bestaat                                      |
| ---------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Kale VSA               | Lettergrepen met hoogte- en lengtestrepen. Geen notenbalk.                        | [`vsa svg`](../formats/vsa-svg.md) voor eenstemmige `.vsa`       |
| VSA met noten          | Dezelfde strepen, plus de partituur (twee balken, recite, melisma).               | De spike                                                         |
| Noten zonder strepen   | De partituur zonder die VSA-strepen.                                              | OSMD en de MuseScore-SVG                                         |

Regels voor de strepen, in de twee beelden die ze tonen:

- Hoogte van de sopraan, niet vier rijen.
- Een kale `-` blijft weg. Die streep komt alleen in een melisma dat ook
  stijgt of daalt (`-&/` of `-&\`).
- Een onderstreping staat op de nootpositie waar de bron een lengteteken
  heeft (`_`, `__`). Bij «lu_&~&~&_» zijn dat de eerste en de laatste noot.
- De strepen vervangen de extender van checklist S13 niet. Die extender
  hoort bij «noten zonder strepen» en bij «VSA met noten».

Transliteratie is een tweede as, geen vierde beeld. Dezelfde drie
beelden moeten kunnen met de brontekst en met de getranslitereerde
tekst. Het schrift volgt het besluit in
[kerkslavisch-transliteratie §5a](kerkslavisch-transliteratie.md#5a-besluiten-productmodel-nu):
zelfde lettergrepen, ander schrift, geen nieuwe melodie, en vandaag een
bestand mét en een bestand zonder de tweede tekstregel. «Alleen de
transliteratie, zonder de bronregel» staat daar als later. De drie
beelden gelden voor elk van die schriftvormen. Nederlands en
kerkslavisch met een andere lettergreepdeling blijven aparte
uitvoeringsvormen, geen weergave van elkaar.

De pagina en de UI horen bij de bibliotheek, niet bij een nieuwe
checklist hier.

| Wie                    | Wat                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| Tooling                | Maakt de afgeleiden: drie beelden, en per beeld de schriftvariant die §5a al kent.                        |
| Markdown van de pagina | Noemt het startbeeld (een tropaar opent bijvoorbeeld als kale VSA, een litanie als noten zonder strepen). |
| UI                     | Wisselt beeld en schrift. Download en print volgen het gekozen bestand.                                   |

Aanbeveling voor de bestanden: aparte SVG’s, dezelfde werkwijze als de
bestaande schakelaar met/zonder transliteratie. Eén SVG met verborgen
lagen kan later, als de wissel zonder nieuw bestand moet. De pagina
ziet hoe dan ook drie beelden van dezelfde bron, niet drie zangstukken.

---

## 5. Contracten

Geen tweede checklist. De hubs blijven de norm.

Wel een nieuw **kanaal** in de contract-index, pas als fase 3 een
aanroep heeft: «eigen SVG» naast OSMD en MuseScore. Dat kanaal linkt
naar dezelfde checklistregels. Alleen waar de verf anders móet dan de
hub nu beschrijft, komt er één zin bij de bestaande regel, in dezelfde
wijziging als de code. Voorbeelden die zo'n zin kunnen worden, en niet
eerder:

| Onderwerp               | Waarom een zin, geen nieuwe checklist                                                                                                                                       |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Spacer van checklist S8 | De schilder zet geen nootkop. OSMD heeft daar een marker plus een adapter voor nodig (`notehead none`). Die adapter is een OSMD-oplossing, geen eigenschap van de partituur |
| Extender en VSA         | Twee lagen in het beeld «VSA met noten». De extender hoort bij checklist S13. De strepen horen bij het beeld uit §4.2, niet bij een aparte checklist.                       |
| Maatstreep              | Lijn plus, bij herhaling, Bravura-puntjes. Geen aparte glyph-norm                                                                                                           |
| Accolade                | Bravura-teken, opgerekt over de twee balken, alleen aan het systeembegin (checklist S18)                                                                                    |

Niet doen in de contract-hubs zolang fase 4 geen besluit is:

- [kale muziek §4](kale-muziek-svg-en-uitgaven.md) omzetten van OSMD naar de eigen schilder.
- Een nieuw standaardproduct in de productcatalogus.
- De M-reeks (Coria) wijzigen. Die reeks blijft het afspeelbestand.

Wel doen zodra een fase code tekent die een regel raakt: de test noemt
het id, en de hub krijgt de zin als de emit afwijkt. Dat is dezelfde
regel als bij elke export-wijziging
(`.cursor/rules/contracten-eerst.mdc`).

---

## 6. Invoer en uitvoer

### Invoer

| Invoer                                    | Rol                                                                                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------------ |
| Score-IR, profiel `partituur`, versie 0.1 | De enige invoer van de schilder                                                            |
| `.mvsa`, `.vsa`, `.mscz`                  | Bron voor `{straat} score-ir`. De schilder roept die export aan of krijgt het JSON-bestand |
| MusicXML, inclusief `*.from-ir.musicxml`  | Blijft de invoer van OSMD. De schilder gebruikt dat bestand niet                           |
| MuseScore-SVG                             | Blijft fallback en afdrukbouwsteen                                                         |

De schilder weigert een onbekende `format` of een onbekende major van
`version`, dezelfde poort als in [partituur-ir §7](partituur-ir.md).

### Uitvoer per fase

| Fase          | Bestand                                                                                              | Wie het gebruikt                |
| ------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------- |
| 0–2           | SVG in de spike-map, niet een standaardproduct                                                       | Review van de platen            |
| 3             | `lied.mvsa.eigen-notes.svg` (en `eigen-vsa-notes`, `eigen-vsa`); geen vervanging van `lied.mvsa.svg` | Vergelijken op dezelfde stukken |
| 4, na besluit | Dan pas een naam in de productcatalogus, en een zin in kale muziek §4                                | Site                            |
| 5             | Hetzelfde SVG, met systeemafbreuk voor een smal venster                                              | Tablet en telefoon              |
| 6             | Alleen na een apart besluit: hoge SVG die de paginasnijder kan snijden                               | `index.md.pdf`                  |

Fase 2 levert per stuk de drie beelden uit §4.2, als aparte SVG's.
Elk bestand heeft een viewBox en de eigen breedte. Een venster dat
smaller is verkleint de plaat; de regelindeling ligt vast bij het
tekenen (`--system-width`).
Achtergrond wit, met een latere vlag voor transparant, gelijk aan
[`mvsa svg`](../formats/mvsa-svg.md).

Geen titelblok in het bestand. De pagina-Markdown zet de titel.

Stabiele kenmerken op noten en lettergrepen (`data-voice`, maat, index,
soort noot) blijven in het SVG. CoriB kan daar later een cursor of een
solo op zetten zonder een tweede tekening.

---

## 7. Fasering

Geen kalender. Elke fase is klaar als de «klaar wanneer»-zin waar is.
Een volgende fase begint niet omdat de vorige «bijna» is.

### Fase 0 — dit werkplan

Klaar wanneer het plan in [Plannen](README.md) staat en de
productiezin in kale muziek §4 ongewijzigd is.
Geen renderer, geen CLI, geen contract-hub.

### Fase 1 — lettertype en beelden

K1 is gekozen: Source Sans 3 zoals MuseScore (gewicht 400, L2).
Het weergavemodel is gekozen: drie beelden, schrift als aparte as,
startbeeld in de pagina-Markdown, wissel in de UI (§4.2).
K2 (Bravura) blijft de aanbeveling. K4 blijft het uitgangspunt.
Deze fase is daarmee klaar. Fase 2 hoeft niet op een extra ja te wachten.

### Fase 2 — de schilder dekt de tabel

De spike-schilder groeit tot de rijen in §3 met fase 2 een test hebben.
De test controleert het contract (stokrichting, géén nootkop op een
spacer, slur alleen over de toonwissel, extender aanwezig, Source Sans 3,
herhaalpuntjes, cue boven de maat, geen titel).
De test controleert geen pixels.

Proefset, in deze volgorde:

1. Alleluia toon 8 en toon 2 (recite, melisma, de twee notenbeelden).
2. Vredeslitanie (1a) (maatstrepen, herhaling, cues), als noten zonder strepen.
3. `examples/bug-cases/trisagion-8a-hemelum.mvsa` (`@nieuw-systeem` en herhaling), ook als kale VSA.
4. Eén speelplan-stuk met Segno of volta, vóór checklist S20.

Klaar wanneer die bronnen de fase-2-rijen halen en elk stuk de drie
beelden uit §4.2 kan leveren vanuit dezelfde Score-IR. Kale VSA voor
een eenstemmige `.vsa` blijft de bestaande `vsa svg`; de nieuwe eis is
dat een `.mvsa`-tropaar hetzelfde soort beeld krijgt, zonder notenbalk.

Die zin is waar voor de proefset in `tests/test_eigen_svg.py`.
De volta-haak loopt over de maten van het slot, alleen boven de
sopraan-alt-balk. Achtsten en korter in dezelfde tel krijgen een balk;
een losse achtste krijgt een vlag. De melismaboog volgt de stokpunten.

Buiten fase 2: site, `products`, OSMD uitschakelen, A4, cursor.

### Fase 3 — naast OSMD kunnen draaien

De aanroep is `mvsa svg --engine eigen`, naast `--engine osmd`.
De default blijft MuseScore. `--view` is `notes` (default),
`vsa-notes` of `vsa`. Zonder `-o` heet het bestand
`lied.mvsa.eigen-notes.svg` (of `eigen-vsa-notes` / `eigen-vsa`).
Met `--translit` komt daar het bestaande translit-stuk bij, bijvoorbeeld
`lied.mvsa.eigen-notes.translit-nls.svg`.
`--lyrics-font-size` en `--cue-font-size` gelden.
`--system-width` zet de regelbreedte (default 760). `none` breekt
alleen op `@nieuw-systeem`. Het SVG heeft de eigen breedte; een pagina
mag het verkleinen met `max-width: 100%`. Het rekt niet meer uit tot
de volle vensterbreedte.
Een ander `--lyrics-font` of `--cue-font` dan Source Sans 3 weigert
de aanroep. MuseScore-Style (afstand, marges, compact) weigert ook.
De aanroep schrijft geen products-meta en overschrijft `lied.mvsa.svg` niet.

Klaar wanneer dezelfde drie spike-stukken én de trisagion via die
aanroep een SVG geven, de test in CI draait, en de bibliotheek nog
steeds OSMD toont. Die aanroep en die test zijn er. Het productiescherm
is OSMD gebleven.

### Fase 4 — besluit

Vergelijk de eigen SVG met de OSMD-SVG en met de MuseScore-SVG op de
proefset. Het besluit wijzigt [kale muziek §4](kale-muziek-svg-en-uitgaven.md)
of laat die paragraaf staan.

Doorgaan alleen als de fase-2-rijen groen zijn én een beheerder de
platen naast de koormap legt en het beeld als partituur herkent.
Stoppen is een geldige uitkomst: OSMD blijft, de spike blijft als
verkenning, en er komt geen product.

### Fase 5 — smal venster en de site

Alleen na een «doorgaan» in fase 4.

- Systeemafbreuk zodat een telefoon niet één miniatuur van een hele
  regel toont ([gebruikseisen §2](gebruikseisen-dragers.md)).
- Inbedden in de bibliotheek-shortcode `muziek`, op dezelfde Score-IR.
- CoriB blijft één beeld: mute, solo en cursor gebruiken de kenmerken
  uit §6. De speler zelf volgt [corib-mvp](corib-mvp.md), niet dit plan.

Klaar wanneer een bekend stuk op een smalle breedte leesbaar blijft
(lettergrepen niet door elkaar, cue bij de maat) en de shortcode de
eigen SVG kan tonen zonder de MuseScore-fallback te verwijderen.

### Fase 6 — afdruk

Apart besluit. De hoge MuseScore-SVG voedt `index.md.pdf` nu.
Een eigen hoge SVG mag die rol pas overnemen als de systeemsnee naar A4
dezelfde stukken kan snijden. Checklist P6 (A4 staand) en de marges uit
checklist S7 horen bij die fase, niet bij het scherm.

---

## 8. Gebruik

### De platen bekijken

Voorbeelden staan in `examples/spikes/eigen-svg/` (`index.html`).
Opnieuw maken, op een Windows-pc met deze repo:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa --engine eigen --view vsa-notes -o examples\spikes\eigen-svg\alleluia-toon-8.vsa-notes.svg
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa --engine eigen --view notes -o examples\spikes\eigen-svg\alleluia-toon-8.notes.svg
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa --engine eigen --view vsa -o examples\spikes\eigen-svg\alleluia-toon-8.vsa.svg
```

De default-sibling zonder `-o` is `alleluia-toon-8.mvsa.eigen-vsa-notes.svg`
naast de bron, niet het product `alleluia-toon-8.mvsa.svg`.
De regelindeling volgt `@nieuw-systeem` en `--system-width`.
Een smaller venster verkleint de plaat; een andere regelbreedte
maak je met `--system-width`.

### Naast OSMD

De beheerder draait de gewone straat, met `--engine eigen`, en legt
het bestand naast de OSMD-SVG en de MuseScore-SVG.
De site verandert niet vanzelf.

### Voor een koorlid

Op de site blijft OSMD het beeld, tot fase 5. Een telefoon krijgt pas
een eigen indeling in fase 5. Tot die tijd is meeschalen een zoom, geen
nieuwe regelafbreuk. Dat verschil hoort in de besluitfase genoemd te
worden, omdat [gebruikseisen §2](gebruikseisen-dragers.md) «zonder
handmatig zoomen» vraagt en zoom alleen dat niet waarmaakt.

### Voor oefenen

CoriB tekent niet zelf. Als de eigen SVG het scherm wordt, leest CoriB
dezelfde Score-IR en hetzelfde SVG. Solo en cursor zijn lagen op de
noten, geen tweede partituur.

---

## 9. Scripts, tests, beheer

### Code

| Onderdeel         | Nu                                                                        | Later                                              |
| ---------         | --                                                                        | -----                                              |
| Schilder          | `src/vsa/eigen_svg.py` (`render_score_ir_svg`, `mvsa svg --engine eigen`) | Blijft één codepad voor de drie beelden            |
| Bravura-contouren | `src/vsa/bravura_glyphs.py` (paden, niet het fontbestand)                 | Het OTF blijft buiten de repo                      |
| Source Sans 3     | `scripts/osmd-svg/fonts/*.woff2`                                          | Hergebruiken. Geen tweede kopie van het lettertype |
| OSMD-adapter S8   | `scripts/osmd-svg/`                                                       | Blijft zolang OSMD het scherm is                   |
| MuseScore Style   | `vsa.mscz_partituur`                                                      | Blijft het afdruk- en bewerkpad                    |

De schilder houdt één codepad. Scherm, latere afdruk en CoriB delen
die schilder. Een aparte «mooie» en «snelle» variant is precies de
splijt die OSMD en MuseScore nu al kosten.

### Tests

Eén pytest-bestand per fase-2-rij is te veel. Eén bestand dat de
proefset laadt en per contract-id een bewering doet, is genoeg.
Naam van het id in de test (`S8`, `S13`, `L2`), niet alleen een vrije zin.

Geen pixelvergelijking met MuseScore. De acceptatie is de tabel in §3
plus het oog van een beheerder op de platen in fase 4.

CI draait `tests/test_eigen_svg.py` in de bestaande Python-run (`vsa-ci`).
Geen extra workflow: de aanroep is Python, zonder Node en zonder MuseScore.

### Wat een beheerder bijhoudt

| Wijziging                                              | Waar                                                                                     |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Een partituur-afspraak (stok, recite, melisma, streep) | De hub in de contract-index. Daarna de schilder én, zolang ze bestaan, OSMD en MuseScore |
| Alleen de verf (dikte van een lijn, vorm van een boog) | De schilder en de spike-plaat. Geen hub                                                  |
| Lettertype of puntgrootte                              | Checklist S7 en leesbaarheid L2, niet een lokale constante                               |
| Of de site OSMD of de eigen SVG toont                  | Kale muziek §4, pas in fase 4                                                            |
| Colofon, titel, koormapnummer                          | Bibliotheek-samenstelling, niet de schilder                                              |

Bron (de org-repo met de normatieve termen) krijgt geen kopie van dit
plan. Een zin met een link is genoeg als iemand daar het schermpad
beschrijft.

### Kosten die dit plan bewust nog niet maakt

- OSMD uit de site halen voordat de tabel groen is.
- MuseScore uit de afdruk halen.
- De catalogus opnieuw genereren.
- Een tweede Score-IR voor «oefenen».
- Optische spatiering. Een eerste balk, een boog buiten de stok en
  `--system-width` zitten al in de schilder; de fijne spatiering niet.

---

## 10. Documentatie

| Moment      | Bijwerken                                                                                                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nu (fase 0) | Dit bestand, [Plannen](README.md), de navigatie, een verwijzing vanuit [kale muziek §4](kale-muziek-svg-en-uitgaven.md) en [partituur-ir §8](partituur-ir.md)                                     |
| Fase 2      | De schilder en `tests/test_eigen_svg.py`. Voorbeelden in `examples/spikes/eigen-svg/`                                                                                                             |
| Fase 3      | Man-pagina van `mvsa svg`, [mvsa-svg](../formats/mvsa-svg.md), één rij in de contract-index («eigen SVG», link naar de bestaande id's). Die drie zijn bijgewerkt                                  |
| Fase 4      | Kale muziek §4, alleen als het besluit «doorgaan» is. Anders een zin «bekeken en niet overgenomen» in dit plan                                                                                    |
| Fase 5      | Bibliotheek `schermpartituur.md` (link, geen tweede checklist) en [CoriB](corib-mvp.md) als de speler het SVG gaat lezen                                                                          |

Handleidingen voor een koorlid (hoe de site eruitziet) horen bij de
bibliotheek, niet bij dit plan.

---

## 11. Grens van de mooiheid

Met Source Sans 3, Bravura-contouren, echte streepdiktes en de
contracten uit §3 kan het beeld voor dit SATB-repertoire als partituur
gelden. Dat is het doel van fase 2 en het materiaal voor het besluit
in fase 4.

Daarboven wordt het duur, en dat hoort niet in deze ronde:

- noten en lettergrepen die elkaar ontwijken in plaats van op een vast raster staan;
- een boog die om elke stok heen slaat zoals een graveur dat doet
  (de schilder volgt de stokpunten al, zonder die fijnere vorm);
- een balk die de helling per noot optisch bijstelt
  (achtsten en korter delen al één balk);
- een venster dat de regel opnieuw afbreekt zonder het bestand opnieuw
  te tekenen (`--system-width` kiest de breedte bij het maken);
- gelijkheid op de pixel met een MuseScore-export.

Als fase 2 die eerste lijst nodig blijkt te hebben om überhaupt
leesbaar te zijn, stopt het werkplan en blijft OSMD het scherm.
De spike is dan het bewijs dat het model klopt en de verf duurder is
dan een ander programma bijsturen.

---

## 12. Open punten

| Punt                                                             | Waar het landt                                                                                                                                                             |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K1 zwaarder dan MuseScore (gewicht 600)                          | Later, als de platen in Source Sans 3 400 dat vragen. Niet in fase 2                                                                                                       |
| Alleen transliteratie, zonder de bronregel                       | Al «bewust later» in [kerkslavisch-transliteratie §5a](kerkslavisch-transliteratie.md#5a-besluiten-productmodel-nu). De drie beelden wachten daar niet op                  |
| Welk startbeeld een pagina krijgt                                | De Markdown van die pagina (bibliotheek), niet de schilder                                                                                                                 |
| «ont-ferm» zonder koppelteken                                    | Opgelost: de export houdt `syllabic` begin/end van het woordstreepje, ook als de lettergreep één noot is (leesbaarheid L3, checklist K4). De schilder zet dan het streepje |
| Meerdere cues in één maat, of een cue midden in de maat          | Al open in [partituur-ir §9](partituur-ir.md). De schilder volgt het anker dat de IR geeft                                                                                 |
| Afspelen van een spacer (klinkt niet) tegenover de layout        | Blijft de vraag uit CoriB. De tekening volgt `print.spacer`                                                                                                                |
| Of fase 6 ooit de MuseScore-SVG als afdrukbouwsteen vervangt     | Apart besluit, niet stil meenemen met fase 4                                                                                                                               |
