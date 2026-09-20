# mvsa v0 — meerstemmige invoersyntax (werkplan)

| Veld            | Waarde                                                                                                                                    |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | niet-normatief werkontwerp                                                                                                                |
| **Doel**        | Intypbare SATB + lyrics in VSCode; later koppelbaar aan [vsa-templates](../specification-vsa-templates/README.md) zonder nodeloos typwerk |
| **Vervangt**    | het eerdere [vsa-polyphony-proposal.md](vsa-polyphony-proposal.md) (alleen nog doorverwijzing + wat daaruit open blijft)                  |
| **Gerelateerd** | [specification-vsa-templates](../specification-vsa-templates/README.md)                                                                   |

Dit document is het **werkplan voor meerstemmige invoer (mvsa)**. Het neemt de
doelen van de eerdere polyfonie-schets over en kiest een concrete schrijfsyntax
(L-regel + stemregels). Wat uit die schets nog niet is besloten, staat in §10.

Templates (laag 2/3) komen alleen aan bod waar de syntax daarop moet anticiperen
(`~` voor de [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)).

Bij tegenstrijdigheid met de officiële VSA-specificatie wint die specificatie
tot dit plan is overgenomen.

### Doelen (uit de eerdere schets, hier gehandhaafd)

- weinig typwerk als dezelfde melodie nieuwe tekst krijgt;
- tekst niet vier keer dupliceren over S/A/T/B;
- stemmen synchroon houden;
- formulematige orthodoxe praktijk (glas/toon → vaste slots → tekst erop);
- bekende VSA-tekens (EHM/ELM) hergebruiken waar dat helpt — zonder de
  eenstemmige VSA-syntax stiekem te herdefiniëren.

Formule-pad in het kort:

```text
toon/glas  →  melodieformule (stemregels / template)
           →  tekstprojectie (L-regel, o.a. met ~)
           →  SATB-uitwerking
```

Dat pad dekt wat de oude schets “tekstprojectie + SATB-overlays” noemde; de
*schrijfwijze* is nu L + stemmen, niet `${n}` in de stemregel.

---

## Woordenlijst (lees dit eerst)

Lees van boven naar beneden: latere termen bouwen op eerdere.
In dit document mag je **brok** en **token** door elkaar gebruiken; ze betekenen
hetzelfde.

| Term                            | Betekenis in dit document                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Brok** (ook: **token**)       | Een stuk tekst op een regel dat als **één eenheid** telt. **L-regel en stemregel scheiden brokken verschillend** (zie de twee rijen hieronder en §3.1). Het teken `&` *binnen* een brok maakt geen nieuwe brokken; het verdeelt dat ene brok in **slots**.                                                                                                                                                                                                                                                                     |
| **Brokgrens op de L-regel**     | Een nieuw L-stuk begint na (1) een **spatie**, (2) een **lettergreepstreepje** `-` tussen twee lettergrepen (zoals in `Al-le`), of (3) een **ELM** waarna meteen weer een letter volgt (zoals `le.&.lu_` → brokken `le.&.` en `lu_`). De ELM zelf hoort bij het **linker** brok. Voorbeeld: `Al-le.&. lu_` telt als **drie** brokken: `Al`, `le.&.`, `lu_` — ook zonder spatie tussen `Al` en `le`. Let op: `-` *na* `&` in een melisma (`Al-&-`) is geen lettergreepstreepje maar slot-inhoud; dat splitst geen nieuw L-stuk. |
| **Brokgrens op de stemregel**   | Alleen **spaties** scheiden hoogte-stukken. Kale `-` op de stemregel = EHM “zelfde toon”. Achter een laddergraad is `-` het octaafsuffix (`so-`), geen nieuwe brok.                                                                                                                                                                                                                                                                                                                                                            |
| **L-regel**                     | De regel die met `L:` begint: de gezongen tekst, plus duur- en melisma-tekens.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Stemregel**                   | Een regel die met een stem-label begint (`S:`, `A:`, `T:`, `B:`, of een andere id): alleen informatie over toonhoogte, geen gezongen woorden.                                                                                                                                                                                                                                                                                                                                                                                  |
| **L-stuk**                      | Een **brok** op de L-regel. Voorbeeld: `Al-le.&. lu_` → drie L-stukken: `Al`, `le.&.`, `lu_`.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Hoogte-stuk**                 | Een **brok** op een stemregel (alleen op spaties gesplitst). Voorbeeld: `S: / \3 -` → drie hoogte-stukken: `/`, `\3`, `-`.                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Melisma**                     | Meerdere opeenvolgende tonen (noten) op **één** lettergreep.                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Slot**                        | Eén van de opeenvolgende tonen binnen een melisma, of — als er geen melisma is — de ene toon die bij een lettergreep hoort. In de schrijfwijze scheidt `&` de slots *binnen* één brok. Voorbeeld: in het L-stuk `Al-&-&-` zijn er drie slots (lettergreep “Al”, dan twee verdere tonen op die lettergreep). In het hoogte-stuk `\&/&\/` zijn er drie slots (drie toonhoogten achter elkaar).                                                                                                                                   |
| **Event**                       | Het moment waarop L en de stemmen **samen** iets doen: één L-stuk hoort bij één hoogte-stuk per stem (behalve bij reciteertoon `~`, zie §5). Bij een melisma telt elk **slot** mee als eigen moment binnen dat ene L-stuk / hoogte-stuk. In de praktijk: “hier zingt iedereen tegelijk op deze lettergreep”, of “hier klinkt de volgende toon van dit melisma”.                                                                                                                                                                |
| **Melisma-stuk**                | Een L-stuk of hoogte-stuk dat met `&` uit meer dan één **slot** bestaat. Voorbeelden: `Al-&-&-&.&.&-` (L) of `\&/&\/` (stem).                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Hoogtemarkering (EHM)**       | Een relatieve stap ten opzichte van de **vorige toon van dezelfde stem**: `/` (omhoog), `\` (omlaag), `-` (zelfde toon), `/3`, `\6`, enz. Zoals in eenstemmige VSA, maar dan op de stemregel.                                                                                                                                                                                                                                                                                                                                  |
| **Laddergraad**                 | Een absolute toonnaam ten opzichte van de [do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md): `do`, `re`, `so`/`sol`, `fa#`, `so-`, `g`, `bes`, … “Absoluut” betekent hier: je schrijft de toon zelf, niet “één stap omhoog vanaf de vorige”.                                                                                                                                                                                                                                            |
| **Schrijfoctaaf**               | Per stem: hoe hoog een laddergraad zonder octaafsuffix klinkt t.o.v. `@do`. Zo schrijft de bas `re` i.p.v. `re-` / `re-1`. Zie §2.4.                                                                                                                                                                                                                                                                                                                                                                                           |
| **Lopende toon** (van een stem) | De toon waarop die stem **nu** staat terwijl je de regel van links naar rechts leest. Bij EHM’s schuift de lopende toon bij elke stap; een laddergraad **zet** de lopende toon opnieuw.                                                                                                                                                                                                                                                                                                                                        |
| **Referentiestart**             | De afgesproken “nul” voor relatieve beginankers (`-`, `\6`, …): welke laddergraad hoort bij “geen stap” voor dit stuk? Die volgt uit `do:` en de stukafspraak (bv. “S opent op mi”).                                                                                                                                                                                                                                                                                                                                           |
| **Anker**                       | Een hoogte-stuk waarmee je de **verwachte** lopende toon van een stem vastzet of controleert — aan het **begin**, **tussendoor**, en/of aan het **eind** van een frase. Bij relatieve EHM’s is dat vaak nodig. Schrijf je overal laddergraden, dan is elk hoogte-stuk al zo’n vastlegging; aparte ankers zijn dan niet verplicht.                                                                                                                                                                                              |

---

## 1. Wat is een mvsa-systeem?

Een **systeem** is één muzikale “regelgroep”:

- precies één **L-regel** (lyrics + duur/melisma),
- één regel per **stem** (alleen toonhoogte),
- optioneel metadata (`@do`, `@oct`, `@start`, …).

Stemvolgorde is vrij; de L-regel mag tussen de stemmen staan. Een lege regel
(of een expliciete systeemscheiding, nader te kiezen) scheidt systemen.

Elke inhoudsregel begint met een label en een dubbele punt:

```text
L: …
S: …
A: …
T: …
B: …
```

Andere stem-id’s mogen (`cantus:`, `S1:`), zolang ze uniek zijn binnen het stuk.

---

## 2. Twee manieren om hoogte te schrijven

In gewone VSA zitten toonhoogten **in de tekst** (`{/in}`, `{\vlees_}`, …).
In mvsa horen hoogten in de **stemregels**. De L-regel heeft geen `/` `\` `#`
meer tussen de letters.

Je mag per stemregel (of per **hoogte-stuk**) twee stijlen gebruiken — **allebei mogen**:

| Stijl                      | Wat je typt                       | `@start` nodig?                           | Ankers begin/midden/eind?                                       |
| -------------------------- | --------------------------------- | ----------------------------------------- | --------------------------------------------------------------- |
| **Relatief (EHM)**         | `/` `\` `-` `/3` `\6` `#\` …      | Ja (of start in het label, zie hieronder) | **Ja** — anders weet je na een lange regel niet of je nog klopt |
| **Absoluut (laddergraad)** | `mi` `so-` `fa#` `Bb` `g` `fis` … | **Nee**                                   | Nee om te *zetten*; optioneel wél om te *controleren*           |

### 2.1 Relatieve stijl: hoogtemarkeringen + ankers

Elke stem heeft een **eigen** **lopende toon**. Een `/` op de S-regel beweegt alleen
S, niet A/T/B.

Hoogtemarkeringen zijn er **niet alleen** voor de begintoon. Bij relatief typen
wil je vaak:

1. **Beginanker** — waarop de stem start vóór het eerste event;
2. **Tussenankers** — “hier moet S weer op mi staan” na een lastige sprong;
3. **Eindanker** — “de frase moet op fa eindigen” (controle + duidelijkheid bij
   het lezen).

Zonder (2) en (3) blijft relatief typen fragiel: één tikfout verschuift de hele
rest, en je ziet het eindpas.

**Beginanker** — twee schrijfwijzen, zelfde betekenis:

```text
# In het label (oorspronkelijk idee)
[-:S]   …     # beginanker: nulstand t.o.v. de referentiestart van de do-context
[\6:T]  …     # beginanker: zes diatonische stappen omlaag
[/3:A]  …     # beginanker: drie stappen omhoog

# Of centraal
@start S=- A=\3 T=\6 B=\8
S: …
```

| Schrijfwijze  | Betekenis                                                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `-` als begin | Geen stap omhoog/omlaag t.o.v. de referentiestart (welke laddergraad dat is, volgt uit `do:` / stukafspraak, bv. “S opent op mi”). |
| `\6` `/3`     | Zes omlaag / drie omhoog vanaf die referentiestart.                                                                                |
| `/n` `\n`     | Zelfde sprongen *binnen* de regel.                                                                                                 |

**Tussen- en eindankers** in relatieve stijl: schrijf een **laddergraad** als
hoogte-stuk. Dat zet de **lopende toon** van die stem opnieuw (en documenteert de
verwachting):

```text
S: / \ /3 mi / \ fa |
#           ^^        tussenanker: hier opnieuw mi
#                   ^^ eindanker: frase eindigt op fa
```

Zo blijven EHM’s prettig om *beweging* te typen, terwijl ankers de *verwachte
hoogte* vastleggen — precies waar klassieke VSA-hoogtemarkeringen in de tekst
ook voor dienden, nu expliciet op de stemregel.

### 2.2 Absolute stijl: laddergraden (do-re-mi en toonnamen)

Schrijf je overal laddergraden, dan *is* elk hoogte-stuk al de klinkende toon
t.o.v. `@do`. Dan hoef je **geen** `@start S=- A=\3 …` meer: de eerste `mi`
op S *is* de start, de laatste `fa` *is* het eind.

Zonder octaafsuffix ligt de toon in het **do-octaaf**: vanaf `@do` omhoog tot
de `si` daarboven. Bij `@do F4` is dat F4…E5:

| do-re-mi     | `do` | `re` | `mi` | `fa` | `so` / `sol` | `la` | `si` / `ti` |
| ------------ | ---- | ---- | ---- | ---- | ------------ | ---- | ----------- |
| Toonnaam     | F    | G    | A    | Bb   | C            | D    | E           |
| Klinkend     | F4   | G4   | A4   | Bb4  | C5           | D5   | E5          |

`so` en `sol` zijn dezelfde graad; `si` en `ti` ook. Namen zijn
hoofdletterongevoelig (`Do` = `do`).

#### 2.2.1 Octaafsuffix

| Schrijfwijze    | Betekenis                                               |
| --------------- | ------------------------------------------------------- |
| `so`            | `sol` in het do-octaaf (hier C5)                        |
| `so-` / `so-1`  | één octaaf omlaag (C4); kale `-` betekent **−1**        |
| `so+` / `so+1`  | één octaaf omhoog (C6); kale `+` betekent **+1**        |
| `so-2` / `so+2` | andere octaven: **getal verplicht** (`so-` is nooit −2) |

`sol-1` blijft geldig; `so-` is de korte vorm. Het suffix komt **achter** een
eventueel kruis/mol (`fa#-`, `bes+`).

**Waar springt het octaaf?** Het suffix `−`/`+` is altijd **dezelfde toonklasse,
twaalf halve tonen omlaag/omhoog** — voor do-re-mi én voor a–g. Er is geen
tweede sprong “bij de C” alleen voor toonnamen.

Wel is de **ongemarkeerde** ligging het **do-octaaf** (vanaf `do` omhoog tot
`si`). Wetenschappelijke octaafnummers springen bij C. Als `@do` F, G, A of Bb
is, vallen `so`/`la`/`si` (en `c`/`d`/`e`) daardoor in het **volgende**
C-octaaf. Dan heb je op die namen één `-` extra nodig om bij `do-`/`f-` in
dezelfde basligging te blijven:

| Klinkend | do-re-mi | a–g   | Waarom het suffix verschilt |
| -------- | -------- | ----- | --------------------------- |
| F3       | `do-`    | `f-`  | ongemarkeerd is F4          |
| G3       | `re-`    | `g-`  | ongemarkeerd is G4          |
| A3       | `mi-`    | `a-`  | ongemarkeerd is A4          |
| C3       | `so-2`   | `c-2` | ongemarkeerd is C5, niet C4 |
| D3       | `la-2`   | `d-2` | ongemarkeerd is D5          |
| E3       | `si-2`   | `e-2` | ongemarkeerd is E5          |

Daarom is `si-` (E4) inderdaad één toon onder `do` (F4): `si` zit aan de
**bovenkant** van het do-octaaf. De ABC-buur van `c` (C5) is **`b`** (B4), niet
`b-` (B3). `si-`↔`do` en `b`↔`c` zijn hetzelfde idee (toon vlak onder de
wrap); de wrap ligt bij **do** vs bij **C**. `b-` naast `c` zetten is die twee
wraps door elkaar halen.

Met een **schrijfoctaaf** per stem (§2.4) telt `+`/`-` t.o.v. díe stem.
`@oct B=-1` slokt één `-` op: F3 wordt `do` / `f`, C3 wordt `so-` / `c-`.

**Baslijnen consistent schrijven** — twee gelijkwaardige vormen, niet een
andere betekenis van `-`:

| Vorm                                    | Wanneer                             | Deze Alleluia-bas (G3…C3…A3)                                  |
| --------------------------------------- | ----------------------------------- | ------------------------------------------------------------- |
| `@oct B=-1` plus `-` alleen onder de do | do-re-mi, of a–g zonder bladcijfers | `re re re si- do&la-&so-&do re mi` · `g g g e- f&d-&c-&f g a` |
| Wetenschappelijk cijfer op a–g          | van de bladmuziek (sprong bij C)    | `g3 g3 g3 e3 f3&d3&c3&f3 g3 a3`                               |

Het cijfer is **absoluut** (MIDI-/wetenschappelijk octaaf, wrap bij C) en
negeert `@oct`. Alleen op toonnamen, niet op do-re-mi (`si3` bestaat niet;
dat blijft `si-2`). Voorbeelden: `f4`, `g3`, `bb4`, `f#4`, `c3`.
`c` zonder cijfer blijft C5 (= `so`); `c3` is C3 (= `so-2`). Zonder cijfer en
zonder `@oct` blijft de bas `re-` / `si-2` / `c-2` — dat is geen fout, alleen
lastig te tellen.

**Wel of niet?** Absoluut cijfer is wél gewenst naast `+`/`-`: handig bij
overname van bladmuziek/MusicXML. Relatief `g-` blijft handig met `@oct`.
Beide mogen; mix in één stem mag (`bb4 so g-`), maar één stijl per frase is
leesbaarder.

#### 2.2.2 Kruis en mol

Toonsoortteken **direct achter** de graad, vóór het octaafsuffix:

| Vorm   | Voorbeeld    | Betekenis                                               |
| ------ | ------------ | ------------------------------------------------------- |
| `#`    | `fa#` `do#-` | kruis                                                   |
| `b`    | `sib` `mib`  | mol (niet verwarren met toonnaam `b` / `B`, zie §2.2.3) |
| prefix | `#do` `bmi`  | zelfde als `do#` / `mib` (herkenbaar uit VSA-EHM)       |

**`+` en `-` achter een laddergraad zijn octaaf, geen kruis/mol.** Anders botst
`so+` (octaaf) met “`+` = kruis”. Wie een kruis wil, schrijft `#` of een
Nederlandse toonnaam (`fis`). De VSA-alias `+` voor kruis blijft op **EHM’s**
(`+\` / `#\`); of die `+` in de eenstemmige VSA-spec kruis blijft, is een
apart open punt.

#### 2.2.3 Toonnamen (a–g) naast do-re-mi

Zodra `@do` (en bij voorkeur `@mode`) bekend is, mag je **dezelfde** hoogte
als toonnaam schrijven. Beide stijlen mogen **door elkaar** in één stemregel
en zelfs in één melisma-stuk: `do g`, `f re`, `f g` en `do re` zijn bij
`@do F4` dezelfde twee tonen (F dan G).

Toegestane toonnamen (hoofdletterongevoelig):

| Familie    | Voorbeelden                                                 |
| ---------- | ----------------------------------------------------------- |
| Engels a–g | `c` `d` `e` `f` `g` `a` `b` ; kruis/mol `f#` `fb` `bb` `Bb` |
| Nederlands | `fis` `bes` `es` `as` `cis` `des` `gis` `ais` `dis` …       |

`b` / `B` is **B (Engels)** = si-kruis t.o.v. do=F, niet automatisch Bes.
Bes schrijf je `bb` / `Bb` / `bes`. (Nederlandse `b` = Bes en `h` = B is een
valkuil; `h` mag als alias van Engels `b`.)

Octaafsuffix `+`/`-` werkt hetzelfde als bij do-re-mi. Optioneel cijfer op a–g
(`g3`, `c3`, `bb3`, `f#3`): wetenschappelijk octaaf, zie §2.2.1. `c-` is C4
(= `so-`), niet C3; C3 is `c-2` of `c3`.

```text
@do F4
@mode major
# geen @start

L: ~Al-le-lu-ia , ~Al-le-lu-ia , al- le- lu_&-&-&_ i_ a__ |
S: fa              fa              fa  so  mi&do&re&mi     fa mi |
A: re              re              re  re  do&fa-&si-&do   re si- |
T: so-             so-             …                              |
B: re-             re-             …                              |
```

Zelfde S-recite in toonnamen: `Bb Bb` i.p.v. `fa fa`. Mix is bedoeld:
`S: Bb Bb Bb so mi&do&re&mi fa mi`.

### 2.3 Mag je mixen?

Ja, als de lezer het nog volgt: een frase grotendeels in EHM’s, met een
eindanker `mi`; of één stem in do-re-mi en een andere in EHM’s; of toonnamen
naast do-re-mi (§2.2.3). De parser behandelt een laddergraad als “zet de
lopende toon hier”; daarna mogen weer relatieve stappen volgen.

### 2.4 Schrijfoctaaf per stem (v0-keuze)

Doel: de bas (en vaak de tenor) niet vol `re-` / `g-2` te hoeven zetten, en
optioneel de sopraan een octaaf **hoger** te laten klinken dan je typt.

**Regel:** `@oct` (of hetzelfde in het stemlabel) verschuift het do-octaaf van
die stem. Een laddergraad **zonder** suffix gebruikt dat schrijfoctaaf. Een
suffix `-` / `+` / `-2` is **extra** t.o.v. het schrijfoctaaf van die stem.

```text
@do F4
@oct S=0 A=0 T=-1 B=-1
# weggelaten stemmen = 0

S:  fa     # Bb4  (do-octaaf)
A:  re     # G4
T:  la     # D4   (niet la- / d-)
B:  re     # G3   (niet re- / g-)
#   re-    # G2   (-1 t.o.v. het bas-schrijfoctaaf)
```

Zelfde betekenis in het label (handig als je één stem leest):

```text
T[-1]: la  la  …
B[-1]: re  re  …
S[+1]: do      # klinkt F5 als @do F4 — “een octaaf hoger dan genoteerd”
```

| Stem | Typisch koor (niet verplicht) | Effect                                     |
| ---- | ----------------------------- | ------------------------------------------ |
| S    | `0` of `+1`                   | `+1` = klinkt een octaaf hoger dan je typt |
| A    | `0`                           | gelijk aan het do-octaaf                   |
| T    | `-1` (of `0` bij hoge tenor)  | tenor-8vb: `la` i.p.v. `la-`               |
| B    | `-1` of `-2`                  | `-2` als de bas anders in `…-2` verdrinkt  |

Geen stille SATB-defaults: wie `@oct` weglaat, heeft overal schrijfoctaaf **0**
(zoals de voorbeelden tot nu toe). Zet `@oct` expliciet zodra T/B lagere
octaven nodig hebben — dan blijft `so` op S en `so` op B bewust een octaaf
uit elkaar, en `so-` op S is dezelfde toon als `so` op T bij `T=-1`.

`@start` / `[-:S]` blijft het **beginanker** in EHM-stijl. `@oct` zegt alleen
in welk octaaf je **laddergraden** typt; het vervangt `@start` niet.

---

## 3. L-regel — lyrics zonder `{` `}`

### 3.1 Events en hoe L-stukken ontstaan

Een **event** koppel je zo aan wat je ziet:

1. Kijk op de L-regel: elk **L-stuk** is in principe één event — behalve bij `~`
   (meer lettergrepen, één hoogte) en behalve extra **slots** binnen één
   melisma-stuk (`&`).
2. Op elke stemregel hoort bij dat event één **hoogte-stuk** (of bij melisma:
   evenveel slots).

**Hoe ontstaan L-stukken?** (brokgrenzen op de L-regel)

| Grens                       | Voorbeeld      | Resultaat                                |
| --------------------------- | -------------- | ---------------------------------------- |
| **Spatie**                  | `barm har_`    | twee L-stukken: `barm`, `har_`           |
| **Lettergreepstreepje** `-` | `Al-le.&.`     | twee L-stukken: `Al`, `le.&.`            |
| **ELM + meteen letters**    | `le.&.lu_`     | twee L-stukken: `le.&.`, `lu_`           |
| Combinatie                  | `Al-le.&. lu_` | **drie** L-stukken: `Al`, `le.&.`, `lu_` |

Een (samengestelde) ELM (`_`, `__`, `_.`, `~`, `-`, `~&~`, `.&.`, …) plak je
**achter** de lettergreep (of in melisma-slots na `&`) en blijft **in hetzelfde**
L-stuk. Geen accolades: VSA `{lu_}` → mvsa `lu_`. De **volledige** ELM-set uit
de VSA-spec geldt ook in mvsa (`_.`, `~`, `-.`, …), niet alleen `_` / `__`.

**Geen** L-stukgrens:

| Situatie                          | Waarom niet                                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `-` na `&` in melisma (`Al-&-&-`) | Dat `-` is slot-inhoud, geen lettergreepstreepje                                                              |
| `&` alleen                        | Verdeelt **slots** binnen één L-stuk, geen nieuwe L-stukken                                                   |
| `\|`                              | Maat-/frasestreep (sync); specialisaties `\|:` en `:\|` = herhaling                                           |
| Komma, punt, `;`                  | **Leesteken: nooit een L-stuk**, ook niet met spaties eromheen (`ia , ~Al` telt `ia` en `~Al`, niet de komma) |

### 3.2 Woordstreepjes — schrijfvormen, zelfde telling

Lettergrepen mag je met streepjes en/of spaties zetten; de **telling** volgt de
grenzen hierboven (streepje telt wél als grens):

| Schrijfwijze           | L-stukken                                  |
| ---------------------- | ------------------------------------------ |
| `barm- har_ tig- heid` | 4: `barm`, `har_`, `tig`, `heid`           |
| `barm har_ tig heid`   | 4 (zelfde)                                 |
| `barm-har_`            | **2:** `barm`, `har_`                      |
| `barm- har_`           | 2 (zelfde)                                 |
| `Al-le.&. lu_`         | **3:** `Al`, `le.&.`, `lu_`                |
| `Al-le.&.lu_`          | **3:** `Al`, `le.&.`, `lu_` (grens na ELM) |

Streepjes blijven nuttig voor de lezer (“één woord”); voor de computer zijn het
tegelijk **brokgrenzen** tussen lettergrepen.

### 3.3 Melisma — vorm A

Meerdere slots op **één** lettergreep zitten in **één L-stuk**, met `&` ertussen
(geen losse `&` als eigen L-stukken):

```text
Al-&-&-&.&.&-
```

Betekenis: lettergreep “Al”, daarna verdere melisma-**slots** in L; elke stem levert
evenveel slots (hoogten gescheiden door `&`) in **één** hoogte-stuk. v0-afspraak:
**één melisma-stuk op L ↔ één samengesteld hoogte-stuk per stem**, met hetzelfde
aantal `&`-slots.

---

## 4. Stemregels

Op een stemregel staan uitsluitend **hoogte-stukken**, gescheiden door spaties:

- relatief: `/` `\` `-` `#\` `b/` `/3` `\2` …
- absoluut: `mi` `so-` `fa#` `Bb` `g` `fis` `bes+` …
- samengesteld melisma: `\&/&\&\&/&/` of `fa&so&la` of `f&d&c&f-`

Geen gezongen tekst en geen `_` / `.&.` op de stemregel — die horen in L.

### Sync-contract (vrije SATB, zonder `~`)

Tussen twee `|` (en binnen één melisma-stuk):

```text
aantal L-stukken  =  aantal hoogte-stukken op S  =  A  =  T  =  B
```

Binnen een melisma-stuk moeten de `&`-slots in L en in elke stem gelijk lopen.

Kolom-uitlijning in de editor is optioneel comfort; wat telt is het **aantal
stukken**, niet het aantal spaties op het scherm.

---

## 5. Reciteertoon — prefix `~`

Op de [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
zingen meerdere lettergrepen op **hetzelfde** akkoord (variabele tekstlengte,
vaste hoogte per stem).

**Syntax:** L-stukken die tot een recite-run horen, beginnen met `~` (of hangen
met streepjes aan een `~`-begin, zie hieronder). Die hele run deelt **één**
hoogte-stuk in elke stem.

```text
# Elke lettergreep met ~
L: ~Gij ~waart ~een En_ gel …

# Eén ~, streepjes plakken de lettergrepen van de run
L: ~Al-le-lu-ia ~Al-le-lu-ia …

# Zonder spatie tussen twee runs: ook bedoeld als geldig —
# de tweede ~ start een nieuwe run (twee hoogte-stukken in de stemmen)
L: ~Al-le-lu-ia~Al-le-lu-ia …
```

Aanbevolen voor leesbaarheid: spatie of komma tussen runs
(`~Al-le-lu-ia , ~Al-le-lu-ia`). De plakvorm zonder spatie mag de parser
toestaan; voor mensen in VSCode is de vorm mét spatie duidelijker.

Daarna volgt gewoonlijk een cadens zonder `~` (nieuwe hoogte-stukken per event).

Zo blijven stemregels kort, terwijl L lang mag zijn — zonder `mi mi mi mi` te
herhalen.

---

## 6. Voorbeeld: Alleluia toon 8 (recite + cadens)

Typbaar experiment (niet door `vsa` geparsed):
`examples/mvsa/alleluia-toon-8.mvsa`. Dat bestand bevat de oorspronkelijke
schets, de gesleutelde SATB in do-re-mi én toonnamen, en een `@oct`-schets.

Oorspronkelijke schets (nog met VSA-accolades):

```text
L: ~Al-le-lu-ia,~Al-le-lu-ia,~al-{le}-{lu_&-&-&_&}{i_}{\a__}
```

### Omzetting naar mvsa

1. Komma’s mogen blijven; ze tellen **niet** als L-stuk (ook niet met spaties).
2. `{le}` → `le`; `{lu_&-&-&_&}` → `lu_&-&-&_&`; `{i_}` → `i_`; `{\a__}` → `a__`.
3. De **`\` bij a** was een hoogtemarkering → die hoort op de **stemregel**, niet in L.
4. Alleen de **eerste twee** alleluia’s zijn pure recite (`~`). De derde heeft
   melisma/beweging → gewone events, 1:1 met hoogte-stukken.

**Variant A — laddergraden (geen `@start`):**

```text
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: ~Al-le-lu-ia , ~Al-le-lu-ia , al- le- lu_&-&-&_ i_ a__ |
S: fa              fa              fa  so  mi&do&re&mi     fa mi |
A: re              re              re  re  do&fa-&si-&do   re si- |
T: la              la              …                              |
B: re              re              …                              |
```

`so` = `sol`. `fa` = `Bb`. Met `@oct T=-1 B=-1` is tenor-`la` dezelfde toon
als `la-` / `d-` zonder schrijfoctaaf, en bas-`re` dezelfde als `re-` / `g-`.

**Variant B — relatief met begin- én eindanker:**

```text
@do F4
@mode major
@start S=- A=\3 T=\6 B=\8

L: ~Al-le-lu-ia , ~Al-le-lu-ia , al- le- lu_&-&-&_& i_ a__ |
S: -               -               /  \   /&-&-&           \  /  re |
#                                                                    ^^ eindanker (controle)
A: -               -               …                                    |
T: -               -               …                                    |
B: -               -               …                                    |
```

(De exacte cadens vullen vanaf het Kiev/Groningen-blad. Duur `_` blijft in L.)

| L-stuk                     | Stemgedrag                                                  |
| -------------------------- | ----------------------------------------------------------- |
| `~Al-le-lu-ia`             | Vier lettergrepen, **één** hoogte-stuk                      |
| tweede `~Al-le-lu-ia`      | Opnieuw één hoogte-stuk                                     |
| `al- le- lu_&-&-&_ i_ a__` | Cadens: elk L-stuk (en elk `&`-slot) eist hoogte in S/A/T/B |

---

## 7. Voorbeeld: vrije SATB (relatief, twee maten)

Typbaar experiment (niet door `vsa` geparsed):
`examples/mvsa/alleluia-toon-1.mvsa`. Bovenaan in dat bestand staan de
oorspronkelijke drie maten (met VSA-accolades); eronder de omzetting van de
eerste twee maten.

```text
@start S=- A=\3 T=\6 B=\8

L: Al- le.&. lu_ i_ a_ , al- le- lu_ ia | Al-&-&-&.&.&- le lu_&_ ia__ |
S: -&/ /     \   #\ /  /  /  \         | \/&\/&\\&\/&/  \&-  \       |
A: -   -     /3  \2 -  /  /2 -         | \/&\/&\\&\/&/  \&-  \2      |
T: -&/ /     \   \  /  /  /  \         | -&-&-&\2&/2&/  \&\  \       |
B: -   -     /   \3 /3 \  \4&/2 /2     | \3&-&-&/&\/&/3 \3&- /3      |
```

Geen `~`: elk L-stuk (plus melisma-`&`) heeft matching hoogte-stukken. Optioneel
mag je aan het eind van een maat een laddergraad als eindanker toevoegen.

---

## 8. Brug naar templates (alleen richting, geen norm)

| Modus              | L                       | Stemmen                                 |
| -----              | -                       | -------                                 |
| Vrije SATB         | veel events             | evenveel hoogte-stukken                 |
| Formule / template | `~`-runs + korte cadens | **weinig** hoogte-stukken = vaste slots |

Zelfde bestandsvorm: een `tropaar-toon-4`-stemtemplate is dan een set
S/A/T/B-regels per frase; per tropaar schrijf je vooral nieuwe L-regels met `~`.
YAML in [`library/tropaar-toon-4/`](../specification-vsa-templates/library/tropaar-toon-4/README.md)
blijft voorlopig leidend tot mvsa die rol overneemt.

---

## 9. Beslissingen vastgelegd in dit plan

| Onderwerp                | Keuze                                                                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Melisma in L             | Vorm **A** (één L-stuk: `Al-&-&-&.&.&-`)                                                                                                 |
| Woordstreepjes           | `barm-har_`, `barm har_`, `barm- har_` alle drie ok; op de **L-regel** scheiden streepjes én spaties L-stukken (plus ELM+letters)        |
| Brokgrens stem           | Alleen spaties; kale `-` = EHM “zelfde toon”; `so-` = octaafsuffix                                                                       |
| Accolades in L           | **Nee** in mvsa v0                                                                                                                       |
| Maatstreep               | `\|`; herhaling `\|:` / `:\|`                                                                                                            |
| Recite                   | prefix `~` op L; ook `~Al-le-lu-ia~Al-le-lu-ia` toegestaan, spatie aanbevolen                                                            |
| Hoogte schrijven         | **EHM en/of laddergraad** (do-re-mi én toonnamen a–g); mix toegestaan                                                                    |
| Laddergraad-namen        | `so` = `sol`; `si` = `ti`; toonnamen `f`/`Bb`/`fis`/`bes` bij gegeven `@do`                                                              |
| Octaafsuffix             | `so-` = `so-1`; altijd ±12 halve tonen. Ongemarkeerd = do-octaaf. C3/D3/E3 bij do=F: `c-2`/`so-2`, niet `c-`.                            |
| Octaafcijfer (a–g)       | optioneel `g3` `c3` `bb3`: wetenschappelijk, wrap bij C, negeert `@oct`; niet op do-re-mi                                                |
| Kruis/mol op laddergraad | achter de naam: `#` / `b` (`fa#`, `sib`); `+`/`-` = octaaf, geen kruis                                                                   |
| Schrijfoctaaf            | `@oct` of `B[-1]:` — suffix telt t.o.v. die stem; weglaten = 0 voor alle stemmen                                                         |
| `@start`                 | Alleen nodig (of handig) in **relatieve** stijl; niet verplicht bij pure laddergraden                                                    |
| Ankers                   | Begin + tussendoor + eind horen bij relatieve stijl; bij laddergraden volstaat opschrijven                                               |
| Label-start              | `[-:S]`, `[\6:T]` blijft equivalent aan `@start`; `T[-1]:` is schrijfoctaaf (§2.4)                                                       |
| Tekstbron                | Één **L-regel** (niet genummerde `${n}`-placeholders in stemregels)                                                                      |
| Stemmen t.o.v. elkaar    | In v0 **gelijkwaardig** uitgeschreven; overlays t.o.v. S = open punt (§10)                                                               |

### Bewust verlaten uit de eerdere polyfonie-schets

| Oude schets                                                            | Waarom niet meer leidend                                                                          |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Tekst via `${1}`, `${2}` in S/A/T/B + aparte `1=…`-lijst               | Vervangen door één L-regel; minder indirection, beter leesbaar in VSCode                          |
| S als enige canonieke bron, A/T/B alleen als afwijking                 | Kan later als *suiker* (§10); v0 eist het niet                                                    |
| `~` / `-` als “onzichtbare vs zichtbare standaard-glyph” in stemmarkup | **`~` op L is nu reciteertoon.** Die glyph-semantiek mag terugkomen onder **andere** tekens (§10) |
| Accolades `{…}` met gemengde EHM+ELM+placeholder                       | In mvsa: ELM in L, EHM op de stem; geen `{}` in L                                                 |

---

## 10. Open punten (bewust later)

### Uit mvsa v0 zelf

- Parser: precieze grens van een `~`-run bij streepjes vs. spaties vs. plakvorm.
- Optionele template-slots overslaan (`?` / open / link).
- Chromatische `+`/`b` vs `#` in **eenstemmige VSA-EHM**. Op mvsa-laddergraden:
  `+`/`-` = octaaf, kruis/mol = `#`/`b` of `fis`/`bes` (§2.2.2).
- Systeemscheiding: lege regel vs. `@system`.
- Of een eindanker een *extra* hoogte-stuk is (alleen controle) of het *laatste*
  klinkende event mag vervangen — nu: anker **is** een gewoon hoogte-stuk met
  laddergraad (klinkt / zet de lopende toon).
- Officiële opname in `specification/` na experimenten.

### Nog meenemen uit de eerdere polyfonie-schets

Deze ideeën zijn **niet** verworpen; ze staan alleen nog niet in de v0-syntax.

1. **Overlays t.o.v. S** — A/T/B als afwijking van de sopraan (`=S`, interval t.o.v. S, of “alleen waar anders”) om homofoon typwerk te verminderen. Past op “S canoniek + overlays” uit de oude schets.
2. **Zichtbare vs. structurele standaardtoon** — per stem kunnen markeren of een
   standaardhoogte wél of geen glyph krijgt (oude betekenis van `~` vs `-` in
   die schets). Mag **niet** opnieuw `~` heten (dat is recite op L). Nieuwe
   tekens of stem-opties kiezen.
3. **Batch-tekst buiten het bestand** — tabel of lijst van tekstsegmenten die op
   vaste muziekslots landen (geest van `${n}`), bv. veel troparen op één
   stemtemplate zonder elke L handmatig in hetzelfde bestand te zetten. Alleen
   nodig als L-per-bestand te zwaar blijkt voor corpuswerk; anders overbodig.

---

## 11. Blokhergebruik en parallelle L (schets)

Typbaar experiment:
`examples/mvsa/trisagion-8a-slav-hemelum.mvsa` (uit VSA-demo Hemelum-mxl).

| Behoefte                  | Voorstel                                                        |
| ------------------------- | --------------------------------------------------------------- |
| Blok labelen              | `@:naam` vóór L + stemmen                                       |
| Parallelle tekstlagen     | `L:` + `L':` (zelfde events; bv. kerkslavisch + transliteratie) |
| Stemmen hergebruiken      | `@voices =:naam` of `S: =:naam`                                 |
| Deelbereik / aaneenrijgen | `@:nieuw = :a[3-4] + :b`                                        |
| Hele blok kopiëren        | `@:nieuw = :oud` (L én stemmen)                                 |

**Check op de bron-MXL:** maten 1–4 en 5–8 zijn *niet* pitch+duur-identiek
(andere lettergreepdeling), wél dezelfde melodische contour. Maten 3–8 en
11–16 *zijn* exact gelijk. Compact schrijven van 5–8 als `@voices =:nl1` is
dus **tekstprojectie op één stemgrid**, geen byte-kopie van de MXL-ritmiek.
`@:final = :nl1[3-4] + :slav1` wél als exacte herhaling van m3–8.

Nog open: exacte parser-semantiek van `[3-4]`, of `L'` verplicht evenveel
events heeft, en of `@include` een alias van `=` mag zijn.

---

## 12. Leesvolgorde voor VSCode

1. Woordenlijst bovenaan.
2. §2 (EHM vs laddergraad, toonnamen, schrijfoctaaf).
3. §6 Alleluia toon 8 (`~` + beide hoogtestijlen).
4. §7 vrije SATB (1:1 L-stukken ↔ hoogte-stukken).
5. §9–§10 (beslissingen + open punten).
6. §11 blokhergebruik + `examples/mvsa/trisagion-8a-slav-hemelum.mvsa`.
7. Daarna [tropaar-toon-4](../specification-vsa-templates/library/tropaar-toon-4/README.md)
   als je stemregels als formule-slots wilt hergebruiken.
