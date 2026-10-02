# Hulptekst-reviewcorpus (expert-review)

| Veld       | Waarde                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------ |
| **Status** | werkdocument voor review (niet normatief)                                                        |
| **Doel**   | Beoordeling van het **parochieschema** voor bidirectionele hulptekst (uitspraak, geen vertaling) |
| **Schema** | `parochie` in `vsa.transliterate`                                                                |
| **Plan**   | [kerkslavisch-transliteratie.md](kerkslavisch-transliteratie.md)                                 |

Dit document is bedoeld om **per e-mail** naar een deskundige te sturen
(kerkslavisch / Cyrillisch-leesbaar / Nederlandse parochiepraktijk). De kolom
*Huidige tooling* toont wat VSA-tooling **nu** produceert. Vul *Jouw voorstel*
en *Toelichting* in waar je het oneens bent of een betere vorm kent.

**Belangrijk:** dit is geen betekenisvertaling. Het gaat om **meezingen**:
kan een Nederlandstalige zanger de Latijnse regel hardop lezen en dicht bij
de kerkslavische uitspraak komen? Kan een Cyrillisch-geletterde zanger de
Cyrillische regel gebruiken om Nederlandse tekst mee te zingen?

Machineleesbare kopie van dezelfde rijen (TSV): bij een verse build opnieuw te
genereren met de huidige module; de tabellen hieronder zijn de
review-snapshot.

---

## 1. Wat we willen weten

1. Zijn de **Latijnse** vormen voor kerkslavisch herkenbaar en uitspreekbaar
   voor NL-zangers, en nog herkenbaar voor Russischtalige lezers?
2. Zijn de **Cyrillische** vormen voor Nederlands bruikbaar voor zangers uit
   het (voormalig) oostblok (ongeveer Nederlandse klank)?
3. Welke **vaste uitzonderingen** moeten in een override-lijst (eigennamen,
   liturgische formules)?
4. Mag `у` → `oe` (NL-traditie) blijven, of liever `u`?
5. Hoe gaan we om met Nederlandse **g** / **ch** / **sch** en leenwoorden
   (`God`, `Glorie`, `Christus`)?

---

## 2. Kerkslavisch → Latijn (woorden)

Kies bewust lastige letters: `ж`/`ш`/`щ`/`ч`/`ц`/`х`, `ы`/`и`/`й`, `я`/`ю`/`у`,
zachte tekens, en bekende liturgische woorden.

| Bron (ksl)  | Huidige tool  | Jouw voorstel | Toelichting |
| ----------- | ------------- | ------------- | ----------- |
| Господи     | Gospodi       |               |             |
| помилуй     | pomiloej      |               |             |
| Святый      | Svjatyj       |               |             |
| Боже        | Bozje         |               |             |
| Крепкий     | Krepkij       |               |             |
| Безсмертный | Bezsmertnyj   |               |             |
| Аллилуиа    | Alliloeia     |               |             |
| Аминь       | Amin          |               |             |
| Слава       | Slava         |               |             |
| Отцу        | Ottsoe        |               |             |
| Сыну        | Synoe         |               |             |
| Христе      | Christe       |               |             |
| Христос     | Christos      |               |             |
| Богородице  | Bogoroditse   |               |             |
| Дево        | Devo          |               |             |
| радуйся     | radoejsja     |               |             |
| благодатная | blagodatnaja  |               |             |
| Марие       | Marie         |               |             |
| Царю        | Tsarjoe       |               |             |
| Небесный    | Nebesnyj      |               |             |
| Утешителю   | Oetesjiteljoe |               |             |
| Иже         | Izje          |               |             |
| сый         | syj           |               |             |
| исполняяй   | ispolnjajaj   |               |             |
| Пресвятая   | Presvjataja   |               |             |
| Троице      | Troitse       |               |             |
| Иисусе      | Iisoese       |               |             |
| Божий       | Bozjij        |               |             |
| церковь     | tserkov       |               |             |
| человеки    | tsjeloveki    |               |             |
| жизнь       | zjizn         |               |             |
| земля       | zemlja        |               |             |
| дух         | doech         |               |             |
| Трисвятое   | Trisvjatoe    |               |             |
| херувимы    | cheroevimy    |               |             |
| Серафимы    | Serafimy      |               |             |

---

## 3. Kerkslavisch → Latijn (korte zinnen)

- Господи помилуй ->
  Gospodi pomiloej
  *(jouw opmerkingen)*
- Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас -> 
  Svjatyj Bozje, Svjatyj Krepkij, Svjatyj Bezsmertnyj, pomiloej nas
  *(jouw opmerkingen)*
- Слава Отцу и Сыну и Святому Духу ->
  Slava Ottsoe i Synoe i Svjatomoe Doechoe
  *(jouw opmerkingen)*
- Ныне и присно и во веки веков. Аминь -> 
  Nyne i prisno i vo veki vekov. Amin
  *(jouw opmerkingen)*
- Христос воскресе из мертвых -> 
  Christos voskrese iz mertvych
  *(jouw opmerkingen)*

---

## 4. Nederlands → Cyrillisch (woorden)

Hier zitten bekende knelpunten: Nederlandse **g** (nu → `х`), digraphen
(`oe`/`ij`/`ui`/`ch`/`sch`), en leenwoorden met harde **g** (`God`, `Glorie`).

| Bron (nl)      | Huidige tool   | Jouw voorstel | Toelichting |
| -------------- | -------------- | ------------- | ----------- |
| Heer           | Хер            |               |             |
| ontferm        | онтферм        |               |             |
| U              | У              |               |             |
| Amen           | Амен           |               |             |
| Glorie         | Хлори          |               |             |
| God            | Ход            |               |             |
| Vader          | Вадер          |               |             |
| Zoon           | Зон            |               |             |
| Heilige        | Хейлихе        |               |             |
| Geest          | Хест           |               |             |
| wereld         | верелд         |               |             |
| zondaars       | зондарс        |               |             |
| barmhartigheid | бармхартиххейд |               |             |
| koninkrijk     | конинкрейк     |               |             |
| hemelen        | хемелен        |               |             |
| brood          | брод           |               |             |
| vergeef        | верхеф         |               |             |
| schulden       | схулден        |               |             |
| eeuwen         | еувен          |               |             |
| Christus       | Христус        |               |             |
| opgestaan      | опхестан       |               |             |
| waarlijk       | варлейк        |               |             |
| schoen         | схун           |               |             |
| ijver          | ейвер          |               |             |
| huis           | хёйс           |               |             |
| vrouw          | враув          |               |             |
| goed           | худ            |               |             |
| dag            | дах            |               |             |
| nacht          | нахт           |               |             |
| alleluia       | аллелёйа       |               |             |

---

## 5. Nederlands → Cyrillisch (korte zinnen)

- Heer ontferm U ->                                          
  Хер онтферм У
  *(jouw opmerkingen)*
- Glorie zij God -> 
  Хлори зей Ход
  *(jouw opmerkingen)*
- Eer aan de Vader en de Zoon en de Heilige Geest -> 
  Ер ан де Вадер ен де Зон ен де Хейлихе Хест
  *(jouw opmerkingen)*
- nu en altijd en in de eeuwen der eeuwen. Amen ->     
  ну ен алтейд ен ин де еувен дер еувен. Амен
  *(jouw opmerkingen)*
- Christus is opgestaan uit de doden ->       
  Христус ис опхестан ёйт де доден
  *(jouw opmerkingen)*

---

## 6. Hoe dit terugkomt in de tooling

Na review:

1. Pas de mappingtabellen in `src/vsa/transliterate.py` aan (schema
   `parochie`).
2. Werk `tests/test_transliterate.py` bij met de afgesproken vormen.
3. Optionele override-lijst voor eigennamen / vaste formules.

Export (blad lyric 2 / Coria) volgt automatisch de module; zie het
[werkplan](kerkslavisch-transliteratie.md).

---

## 7. Mailbare checklist voor de reviewer

- [ ] Kolommen *Jouw voorstel* / *Toelichting* ingevuld waar nodig
- [ ] Expliciet antwoord op §1 vraag 4 (`oe` vs `u`)
- [ ] Expliciet antwoord op §1 vraag 5 (Nederlandse `g` / leenwoorden)
- [ ] Lijstje “altijd zo” (overrides) indien van toepassing
