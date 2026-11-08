# Eigen partituur-SVG — werkplan

| Veld            | Waarde                                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan; **niet normatief**; geen productcode in deze stap                                                                                                     |
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

Het lettertype voor zangtekst, cues en woorden is al gekozen:
**Source Sans 3**. Dat is de Style van de MuseScore-partituur
(checklist S7, leesbaarheid L2) en het lettertype in de OSMD-SVG
(`scripts/osmd-svg/fonts/`, gewichten 400, 600 en cursief).
De spike zette DejaVu Sans. DejaVu wordt niet het productlettertype.

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

Wat nog een schets is: de bogen zijn eenvoudige krommen, de afstand
tussen noten is grof, er is één systeem per stuk (ook waar de bron
`@nieuw-systeem` zet), en de zangtekst is nog niet Source Sans 3.
Een koppelteken in «ont-ferm» ontbreekt omdat Score-IR «ont» als losse
lettergreep noteert (`syllabic: single`), niet als begin van een woord.

Het SVG-bestand schaalt mee met de vensterbreedte (`width="100%"` en
een viewBox). De indeling breekt niet opnieuw af als het venster smal
wordt. Voor papier en voor een telefoon is dat niet genoeg; zie §7 (fase 5) en §8.

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
De kolom «Spike» zegt of pull request 75 die keuze al tekent.
«Fase» wijst naar §7.

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

De VSA-strepen uit de spike zijn een extra laag, geen vervanging van
checklist S13. De muzieklaag tekent de extender en de slur.
De VSA-laag tekent de hoogte van de sopraan en de lengte-onderstreping.
Zie §4 voor wanneer die laag aan staat.

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
| Telefoon en tablet zonder handmatig zoomen                                  | [gebruikseisen §2](gebruikseisen-dragers.md)              | Meeschalen is fase 1-bewijs. Opnieuw afbreken bij een smal venster is fase 5                            |
| Vier losse partijen voor Coria                                              | checklist M-reeks                                         | Blijft het afspeelbestand voor Coria. De eigen tekening is de partituur (twee balken), niet dat bestand |

---

## 4. Voorgestelde productkeuzes

Vier punten zijn nog een bevestiging waard. De rest van §3 is overnemen,
niet opnieuw kiezen.

| #   | Voorstel                                                                       | Waarom                                                                                                                  | Alternatief                                                                             |
| -   | --------                                                                       | ------                                                                                                                  | -----------                                                                             |
| K1  | Zangtekst en cues in Source Sans 3, gewicht 400, maten uit L2 (13 pt en 12 pt) | Gelijk aan MuseScore en aan de OSMD-SVG                                                                                 | Gewicht 600 (het bestand ligt al in de repo) als de vette spike-tekst de voorkeur houdt |
| K2  | Muziektekens als Bravura-contouren                                             | Geen ontbrekend lettertype; spike doet dit al                                                                           | Leland, dichter bij MuseScore 4, tweede licentie en tweede contourset                   |
| K3  | VSA-laag uit, tenzij de aanroep die laag vraagt                                | De koormap toont vandaag geen schuine strepen boven de lettergrepen. Kale muziek blijft daardoor vergelijkbaar met OSMD | Altijd aan, omdat de spike juist dáár meer kan dan OSMD                                 |
| K4  | OSMD en MuseScore blijven staan tot fase 4                                     | De site en de afdruk hebben een werkend pad. De eigen tekening moet de tabel in §3 eerst halen                          | OSMD nu al uit het scherm halen                                                         |

VSA-laag, wanneer K3 aan staat (zoals de spike, als voorstel voor die laag):

- Hoogte van de sopraan, niet vier rijen.
- Een kale `-` blijft weg. Die streep komt alleen in een melisma dat ook
  stijgt of daalt (`-&/` of `-&\`).
- Een onderstreping staat op de nootpositie waar de bron een lengteteken
  heeft (`_`, `__`). Bij «lu_&~&~&_» zijn dat de eerste en de laatste noot.
- De laag vervangt de extender van checklist S13 niet.

Gewicht van de zangtekst (K1) en de VSA-standaard (K3) zijn de twee
punten waarop een beheerder dit werkplan kan bijsturen zonder de
architectuur te wijzigen.

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
| Extender en VSA         | Twee lagen. De extender hoort bij checklist S13. De VSA-strepen horen bij een vlag, beschreven in dit werkplan tot de vlag een product is                                   |
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

| Fase          | Bestand                                                                | Wie het gebruikt                |
| ------------- | ---------------------------------------------------------------------- | ------------------------------- |
| 0–2           | SVG in de spike-map, niet een standaardproduct                         | Review van de platen            |
| 3             | Optioneel naast OSMD, nog geen vervanging van `lied.mvsa.svg`          | Vergelijken op dezelfde stukken |
| 4, na besluit | Dan pas een naam in de productcatalogus, en een zin in kale muziek §4  | Site                            |
| 5             | Hetzelfde SVG, met systeemafbreuk voor een smal venster                | Tablet en telefoon              |
| 6             | Alleen na een apart besluit: hoge SVG die de paginasnijder kan snijden | `index.md.pdf`                  |

Het SVG van fase 2 en 3 heeft een viewBox en `width="100%"`, zodat een
venster het beeld kleiner maakt zonder de noten te herrekenen.
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

### Fase 1 — de vier voorstellen in §4 bevestigen

K1 tot en met K4 staan als voorstel. Een beheerder zet in dit bestand
de gekozen kolom op «gekozen» of wijzigt K1 of K3.
Klaar wanneer die vier rijen geen «voorstel» meer zijn.
Tot die tijd mag fase 2 de spike wel laten staan, maar geen Source Sans 3
inbouwen op een gok over het gewicht, en de VSA-laag niet tot standaard
maken.

### Fase 2 — de schilder dekt de tabel

De spike-schilder groeit tot de rijen in §3 met fase 2 een test hebben.
De test controleert het contract (stokrichting, géén nootkop op een
spacer, slur alleen over de toonwissel, extender aanwezig, Source Sans 3,
herhaalpuntjes, cue boven de maat, geen titel).
De test controleert geen pixels.

Proefset, in deze volgorde:

1. Alleluia toon 8 en toon 2 (recite, melisma, VSA-vlag).
2. Vredeslitanie (1a) (strepen, herhaling, cues).
3. `examples/bug-cases/trisagion-8a-hemelum.mvsa` (`@nieuw-systeem` en herhaling).
4. Eén speelplan-stuk met Segno of volta, vóór checklist S20.

Klaar wanneer die vier bronnen de fase-2-rijen halen en de VSA-laag
uit dezelfde Score-IR aan en uit kan.

Buiten fase 2: site, `products`, OSMD uitschakelen, A4, cursor.

### Fase 3 — naast OSMD kunnen draaien

Een aanroep, nog geen standaardproduct. Voorstel voor de vlag, pas
invullen als de man-pagina meegaat: `mvsa svg --engine eigen`, naast
het bestaande `--engine osmd`. De default blijft de huidige engine.

Klaar wanneer dezelfde drie spike-stukken én de trisagion via die
aanroep een SVG geven, de test in CI draait, en de bibliotheek nog
steeds OSMD toont.

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

### Zolang de schilder een spike is

De platen opnieuw maken, op een Windows-pc met deze repo:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\bug-cases\corib\alleluia-toon-8.mvsa -o examples\spikes\score-ir-svg\alleluia-toon-8.svg --from-mvsa
```

Die aanroep bestaat alleen op de branch van pull request 75.
`index.html` naast die SVG laat het beeld meeschalen. Versmal het
venster: de tekening wordt kleiner, de regelindeling blijft één systeem.

### Als fase 3 er is

De beheerder draait de gewone straat, met de nieuwe engine-vlag, en
legt het bestand naast de OSMD-SVG en de MuseScore-SVG.
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

| Onderdeel         | Nu                                                                       | Later                                                                 |
| ---------         | --                                                                       | -----                                                                 |
| Schilder          | `examples/spikes/score-ir-svg/render_score_ir_svg.py` op de spike-branch | Module onder `src/vsa/` pas in fase 2, als de spike de proefset haalt |
| Bravura-contouren | `bravura_glyphs.py` in de spike (paden, niet het fontbestand)            | Zelfde: paden in de repo, het OTF niet als productafhankelijkheid     |
| Source Sans 3     | `scripts/osmd-svg/fonts/*.woff2`                                         | Hergebruiken. Geen tweede kopie van het lettertype                    |
| OSMD-adapter S8   | `scripts/osmd-svg/`                                                      | Blijft zolang OSMD het scherm is                                      |
| MuseScore Style   | `vsa.mscz_partituur`                                                     | Blijft het afdruk- en bewerkpad                                       |

De schilder houdt één codepad. Scherm, latere afdruk en CoriB delen
die schilder. Een aparte «mooie» en «snelle» variant is precies de
splijt die OSMD en MuseScore nu al kosten.

### Tests

Eén pytest-bestand per fase-2-rij is te veel. Eén bestand dat de
proefset laadt en per contract-id een bewering doet, is genoeg.
Naam van het id in de test (`S8`, `S13`, `L2`), niet alleen een vrije zin.

Geen pixelvergelijking met MuseScore. De acceptatie is de tabel in §3
plus het oog van een beheerder op de platen in fase 4.

CI draait die test in de bestaande Python-run (`vsa-ci`). Geen extra
workflow tot fase 3 een CLI heeft die op Linux én Windows moet.

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
- Optische spatiering, bundels en bogen die de melodiecontour volgen,
  vóórdat de contractrijen kloppen. Dat is de grens uit §10.

---

## 10. Documentatie

| Moment      | Bijwerken                                                                                                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nu (fase 0) | Dit bestand, [Plannen](README.md), de navigatie, een verwijzing vanuit [kale muziek §4](kale-muziek-svg-en-uitgaven.md) en [partituur-ir §8](partituur-ir.md). Geen man-pagina, geen contract-hub |
| Fase 2      | De spike-README op die branch. Nog steeds geen product-CLI-pagina                                                                                                                                 |
| Fase 3      | Man-pagina van `mvsa svg`, [mvsa-svg](../formats/mvsa-svg.md), één rij in de contract-index («eigen SVG», link naar de bestaande id's)                                                            |
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

Daarboven wordt het duur, en dat hoort niet in fase 2:

- noten en lettergrepen die elkaar ontwijken in plaats van op een vast raster staan;
- bogen die om stokken heen lopen;
- bundels (achtsten aan één balk);
- een systeem dat op een smal venster opnieuw afbreekt (dat is fase 5,
  en alleen na het besluit);
- gelijkheid op de pixel met een MuseScore-export.

Als fase 2 die eerste lijst nodig blijkt te hebben om überhaupt
leesbaar te zijn, stopt het werkplan en blijft OSMD het scherm.
De spike is dan het bewijs dat het model klopt en de verf duurder is
dan een ander programma bijsturen.

---

## 12. Open punten

| Punt                                                             | Waar het landt                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| K1 gewicht 400 of 600                                            | Bevestigen in fase 1                                                                                                     |
| K3 VSA standaard uit of aan                                      | Bevestigen in fase 1                                                                                                     |
| «ont» als `syllabic: single` terwijl de bron `ont-ferm` schrijft | Score-IR / parser, niet de schilder. De schilder zet een koppelteken alleen bij `begin`/`middle`/`end` (leesbaarheid L3) |
| Meerdere cues in één maat, of een cue midden in de maat          | Al open in [partituur-ir §9](partituur-ir.md). De schilder volgt het anker dat de IR geeft                               |
| Afspelen van een spacer (klinkt niet) tegenover de layout        | Blijft de vraag uit CoriB. De tekening volgt `print.spacer`                                                              |
| Of fase 6 ooit de MuseScore-SVG als afdrukbouwsteen vervangt     | Apart besluit, niet stil meenemen met fase 4                                                                             |
