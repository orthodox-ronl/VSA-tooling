# Keuzes voor de transliteraties

| Veld       | Waarde                                                                 |
| ---------- | ---------------------------------------------------------------------- |
| **Status** | **v1 bevroren** (branch `translit`); expert-antwoorden hieronder       |
| **Code**   | `src/vsa/transliterate.py` (schema `parochie`)                         |
| **Intern** | apostrof `'`; `Иисусе` → `Iesusje`; bron-hoofdletter volgen            |

**Samenvatting v1 (wat de tooling doet):**

- Ksl→Latijn: default `е`→`je`, uitzonderingen `це`/`пре`/`ге`/`ец` en na
  `ж ш щ ч ц г`; `ь`→`'`; `-ий`/`-ый`→`iej`; overrides o.a. `Nynje`,
  `Djevo`, `Marieje`, `Trisvjatoje`, `Voskresje`, `Gospod'`, `Iesusje`.
- Nl→Cyrillisch: `Heer`→`Хиир`; `en`/`den`→`эн`/`дэн`; `Eer`→`Ир`;
  `ee`→`ей` (uitz. `eeuwen`→`эувен`); `ij`→`ей`; `ui` begin→`ау`, midden→`ёй`;
  `g`→`х`; overrides `Amen`→`Аминь`, `Christus`→`Христус`, enz.

Open: expert stuurt later meer `е`/`e`-patronen → kleine tabelupdate.

---

## Keuze 1 — Letter е in het kerkslavisch (Latijnse hulptekst)

Jij schreef: bij ныне hoor je duidelijk nynje, maar bij Богородице / Царице meer een gewone è (Bogoroditse, niet “Bogoroditsje”).

Vraag: Wat willen we als standaard?

A. Meestal е → e (Bogoroditse, Tsaritse). Alleen bij woorden waar je echt je hoort, zetten we een uitzondering (zoals ныне → nynje, Дево → Djevo).
B. Vaker е → je, behalve een lijstje uitzonderingen zonder je.
C. Geen algemene regel: alleen een lijstje vaste schrijfwijzen voor de liturgische woorden die we echt gebruiken.

Wil je er 5–10 woorden bij zetten waar jij wél je wilt, en 5 waar juist géén je?

---

Antwoord: -

Ik stel voor om vooral 'je’ aan te houden, aangezien de ‘e’ klank wat uitzonderlijker is. Er zijn patronen zoals woorden met ‘це’. Ik kan zoveel mogelijk patronen verzamelen, en die als richtlijn aanhouden voor de ‘e’ klank.

Hier hoor je een duidelijke ‘e’ klank

Woorden met ‘це’ zoals in:
Царице
Богородице
Владыце

Woorden met ‘пре’ zoals in:
Преподобне
Пресвятая

Woorden met ‘ге’ zoals in:
Ангельское
Ангелы

Woorden met ‘ец’ zoals in:
Старец

## Keuze 2 — Het zachte teken ь (bijv. Господь, Аминь)

Nu laten we ь weg (Amin, Gospod). Jij hoort bijna een j: Gospodj.

Vraag: Hoe schrijven we ь voor Nederlandse lezers?

A. Altijd als j erna (Gospodj; Amin/Amien/Aminj — zie ook keuze 3/4).
B. Als haakje ’ (Gospod’, Amin’).
C. Meestal weglaten; alleen bij een paar vaste woorden j zetten.

Welke vorm vind jij het duidelijkst voor meezingen: Gospodj of Gospod’?


Antwoord: B

Ik neig naar keuze B, omdat een ‘j’ misschien te verwarrend is. De ‘ь’ klank is subtiel, maar wel aanwezig. Af en toe een 'j' toevoegen lijkt me ook verwarrend. Een apostrof is subtiel en stoort denk ik het minst.

## Keuze 3 — Uitgangen zoals -ий / -ый (Крепкий, Божий)

Nu: Krepkij, Bozjij.
Jouw voorstel: Krepkiej, Bozjiej (meer “ie”-klank voor NL-ogen).

Vraag:

A. Houden: …kij / …jij (Krepkij, Bozjij).
B. Standaard: …kiej / …jiej (Krepkiej, Bozjiej).
C. Alleen bij een paar bekende woorden anders; verder A of B.

---

Antwoord: B 

Ik neig naar B voor de leesbaarheid. Bij woorden met ‘ж' en ‘ш/щ’ zou 'iej' duidelijker kunnen zijn, omdat zie letters al met 'zj' en ‘sj’ getranslitereerd worden. Dan krijg je dus dubbele ‘j’s’. Bozjiej is misschien wat duidelijker Bozjij.

## Keuze 4 — Аминь

Nu: Amin. Jouw voorstel: Amien.

Vraag:

A. Amin
B. Amien
C. Amin’ / Aminj (als we ь zichtbaar maken)

---

Antwoord: C

## Keuze 5 — “Heer” naar Cyrillisch

Nu wordt Heer → Хер. Jij waarschuwt: dat is in het Russisch een vulgair woord. Voorstellen: Хир of Хеер.

Vraag: Welke vaste vorm willen we altijd?

A. Хир
B. Хеер
C. Iets anders: …

(Dit zetten we dan vast als uitzondering, los van de algemene letterregels.)

---

Antwoord: A of Хиир

Ik heb opgemerkt dat ‘Heer’ in Zwolle als ‘Хиир’ in de mappen staat. Dat lijkt me eigenlijk het best.

## Keuze 6 — Nederlandse e / ee / en naar Cyrillisch

Probleem: kale е wordt door Russischtaligen vaak als “je” gelezen.
Jouw richting: vaker de “vlakke è” met э, bv. эн (en), дэн (den), en bij “Eer” Эр of Ир.

Vraag — korte woordjes (kies per regel):

en     → ен   of   эн   ?
den    → ден  of   дэн  ?
Eer    → Ер   of   Эр   of   Ир  ?
eeuwen → еувен  of  эйвен  of  ейвен  ?

Vraag — ee in woorden zoals Geest / vergeef:

A. Geest → Хейст, vergeef → верхейф (met ей)
B. Geest → Хэйст, vergeef → верхэйф (met эй)
C. Geest → Хест laten, alleen “gevaarlijke” woorden aanpassen

---

Antwoorden:

Vraag — korte woordjes (kies per regel):

en     → ен   of   эн   ? >> эн
den    → ден  of   дэн  ?  >> дэн
Eer    → Ер   of   Эр   of   Ир  ? >> ир
eeuwen → еувен  of  эйвен  of  ейвен  ? >> эувен*


Vraag — ee in woorden zoals Geest / vergeef:

A. Geest → Хейст, vergeef → верхейф (met ей) 
B. Geest → Хэйст, vergeef → верхэйф (met эй)
C. Geest → Хест laten, alleen “gevaarlijke” woorden aanpassen

Antwoord: A

## Keuze 7 — Nederlandse ij en ui

Nu ongeveer: ij → ей, ui → ёй.
Jij: ij → ай of ей (Heilige: Хайлихе / Хейлихе); ui in het midden ёй.

Vraag:

1.⁠ ⁠ij standaard → ей of ай? (voorbeeld: Heilige, leidt, mij)
2.⁠ ⁠ui standaard → ёй? Mag dat ook aan het begin/eind van een woord?

Geef gerust 3 voorbeeldwoorden per keuze.

---


Antwoord vraag 1 'ij’: ей
Antwoord vraag 2 ‘ui’: 
- ёй niet aan het begin van een woord, anders: ‘joj’

## Keuze 8 — Wat mag op de “altijd zo”-lijst?

Dit is géén regel, maar een woordenlijstje dat we handmatig vastzetten.

Wil je aangeven welke van deze (of meer) altijd zo moeten, ook als de letterregels iets anders zouden doen?

Kerkslavisch → Latijn (jouw voorkeur invullen):

ныне → ? (jij: nynje)
Дево → ? (jij: Djevo)
Господь → ?
Марие → ? (jij: Marieje)
Крепкий → ?
Трисвятое → ? (jij: Trisvjatoje?)
воскресе → ? (jij: voskresje?)
Богородице Дево радуйся … → mag dit als vaste frase?

Nederlands → Cyrillisch:

Heer → Хир (als keuze 5)
Amen → ?
Christus → Христус houden, of Христос?
alleluia → ?
God / Glorie → hoe? (harde g vs ch-klank)

---
Antwoorden:


Kerslavisch:
Господь > Gospod’
Крепкий > krepkiej
Bogoroditse Djevo radoejsja 

Nederlands > Cyrillisch

Heer > Хиир*
Amin’ > Аминь
Christus > Христус
Alleluia > аллелуиа
God / Glorie en andere Nederlandse ‘g’ klanken als ‘x’ in Сyrillisch > Ход, Хлори

