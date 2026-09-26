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
| Directive    | Regel die begint met `@` (zie [Semantiek](semantics.md#directives-do-mode-oct))      |
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

### Canonieke kolomuitlijning (LSATB)

De **standaardlayout** van een `.mvsa` (wat tooling schrijft bij genereren of
canonieke herschrijving, en wat in `examples/mvsa` hoort te staan) lijkt in de
editor onder elkaar. Per **maat**, binnen één LSATB-systeem:

1. Tel de **lengte-posities** op de lyrics-regel (L-stukken). Een recite-groep
   `( … )` telt als **één** positie; optionele ELM direct na `)` hoort bij die
   positie.
2. Op elke stemregel (S/A/T/B) staat voor die maat hetzelfde aantal
   hoogte-stukken, in dezelfde volgorde.
3. Voor elke positie *i* deelt de **anker-kolom** (0-based tekenpositie op de
   regel, ná de marker en de spatie na `:`) mee:
   - op L: de eerste letter van de lettergreep; bij een woordstreepje vóór de
     lettergreep (`-li`) de letter na dat streepje; bij recite het teken `(`;
   - op elke stemregel: het **eerste teken** van het bijbehorende hoogte-stuk
     (`fa`, `mi&do&re&mi`, `f#4`, `/`, …).

4. Maatstrepen (`|`, `||`, `|:`, `:|`, `:||`) staan op **dezelfde
   kolomposities** op alle LSATB-regels van het systeem: na elke maat (en aan
   het sectie-einde) begint de streep in VSCode in dezelfde kolom. De
   standaardlayout vult spaties aan het eind van een maat zo nodig aan tot die
   strepen onder elkaar vallen.

In VSCode (vaste-breedteletter) staan die ankers én de maatstrepen dus **in
dezelfde kolom** op L, S, A, T en B. Spaties tussen posities (en vóór een
maatstreep) worden toegevoegd of weggehaald tot dat klopt. Woordstreepjes
blijven aan de lettergreep: canoniek `le-lu` (aanliggend). Als een stemtoken
breder is dan de lettergreep tot aan de volgende anker-kolom, komt er ruimte
*vóór* het streepje (`le -lu`), zodat stemtokens met spaties gescheiden blijven
en de ankers (eerste letters / eerste noottekens) toch onder elkaar staan.
Vermijd `le-  lu` (streepje direct gevolgd door spaties): die vorm leest de
kuiser als ELM `-` op “le”, niet als woordstreepje.

```text
L: (Al-le-lu-ia, Al-le-lu-ia, Al)-le  -lu_&-&-&_         i_  a__  ||
S: fa                             so   mi&do&re&mi       fa  mi   ||
A: re                             re   do&fa-&si-&do     re  si-  ||
T: la-                            so-  so-&mi-&so-&so-   la- so-# ||
```

Hier deelt `(` de kolom met `fa`/`re`/`la-`; de `l` van `-le` deelt de kolom
met `so`/`re`/`so-`; de `l` van `-lu_…` deelt de kolom met `mi&…` / `do&…` /
`so-&…`; en `||` staat op alle regels in dezelfde kolom. Omdat `so-` drie
tekens breed is, staat er ruimte vóór het woordstreepje (`le  -lu`), niet
eráchter.

**Validatie** eist deze kolommen **niet**: alleen de positietelling telt
([Semantiek](semantics.md#sync-contract-lengte-posities)). Losse invoer mag
rompiger zijn; de kuiser mag normaliseren. Gegenereerde output en de
voorbeelden in `examples/mvsa` volgen wél deze layout. Hulpje:
`python scripts/align_mvsa_columns.py examples/mvsa`.

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

Buiten een recite-groep begint een nieuw L-stuk na:

1. een **spatie**, of
2. een **lettergreepstreepje** `-` tussen lettergrepen, of
3. een **ELM** waarna meteen weer een letter volgt (`le.&.lu_` → `le.&.` en `lu_`).

`&` binnen een brok scheidt **slots** (melisma), geen nieuwe L-stukken.
Leestekens (`,` `.` `;` …) zijn **geen** L-stuk, ook niet met spaties eromheen.

**Uitzondering — recite:** alles tussen `(` en `)` is **één** L-stuk / lengte-positie,
ongeacht spaties en streepjes erin. Zie [Reciteertoon](#reciteertoon).

### Canonieke woordstreepjes

Tussen opeenvolgende lettergrepen van **hetzelfde woord** staat altijd `-`.
Tussen het einde van een woord en het begin van het volgende woord staat **geen**
`-` (wel spatie en/of leesteken). Tussen die lettergrepen mogen wel ELM’s,
recite-haakjes, maatstrepen en leestekens staan.

De kuiser mag eenvoudige fouten herstellen (bijvoorbeeld `hei- li- ge` →
`hei-li-ge`).

### Melisma (vorm A)

Meerdere slots op één lettergreep: één L-stuk met `&` tussen ELM-slots, bijvoorbeeld
`Ster~&~&~` of `God_.&_.`.

### Reciteertoon

Een [reciteertoon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)-run
staat tussen **ronde haakjes**:

```text
( tekst met - en spaties )ELM?
```

De hele groep is **één** lengte-positie (één hoogte-stuk per stem). Er is
**geen** leading `~` meer als recite-marker. Optioneel volgt **direct na** `)`
een ELM voor de duur van die positie.

| Onderdeel                     | Betekenis                                                           |
| ----------------------------- | ------------------------------------------------------------------- |
| `(` … `)`                     | Recite-run; spaties = woorden, `-` = lettergreepstreepjes           |
| geen ELM na `)`               | Recite-standaardduur (export: breve / `\|\|O\|\|`)                  |
| ELM na `)` (`_`, `~`, `.`, …) | Andere duur (`(Zoon van God)_`, `(Al-le-lu-ia,)~`)                  |
| `)-` + lettergreep            | **Woordstreepje** over de recite-grens (niet ELM-`-`)               |
| `~` elders op L               | Alleen **ELM-duur** (`hei~`, melisma-slots) — start **geen** recite |

Kale ELM-`-` na `)` voegt geen nuttige duur toe t.o.v. de standaard (zelfde
kwart-duur als `~`). Zet een streepje **achter** de `)` alleen als het woord
doorloopt naar de volgende lettergreep: `(… Al)-le-…`. Schrijf **niet**
`(… Al-)` met een losse `-` vóór de `)` — die eindstreep wordt genegeerd.

#### Eenvoudige gevallen

```text
# Eén woord
L: (hei-li-ge) …

# Twee aparte recite-posities
L: (Al-le-lu-ia,) (Al-le-lu-ia,) …

# Meerdere woorden; langere duur met betekenisvolle ELM
L: (Zoon van God)_ …

# Recite, daarna gewone posities
L: (Al-le-lu-ia,) (Al-le-lu-ia,) al-le lu_&-&-&_ i_ a__ ||
```

#### Streepje binnen vs. achter `)`

```text
# Genegeerd: '-' vóór ')' zonder volgende lettergreep in de groep
L: (Al-le-lu-ia, Al-le-lu-ia, Al-) …

# Canoniek: woord loopt door ná de recite — streepje ACHTER ')'
L: (Al-le-lu-ia, Al-le-lu-ia, Al)-le-lu_&-&-&_ i_ a__ ||

# Zelfde doorloop, andere duur op de recite (ELM '_' na ')', dan streepje)
L: (Al-le-lu-ia, Al-le-lu-ia, Al)_-le-lu_&-&-&_ i_ a__ ||
```

| Schrijfwijze     | Effect                                                                      |
| ---------------- | --------------------------------------------------------------------------- |
| `(… Al-)`        | Eind-`-` in de groep: **geen** lettergreepverbinding, **geen** ELM (dood)   |
| `(… Al)-` alleén | Losse `-` na `)`: **woordstreepje zonder vervolg** — vermijd; geen ELM-duur |
| `(… Al)-le-…`    | Recite tot “Al”, daarna “le…” als **zelfde woord** (canonieke vorm)         |
| `(… Al)_`        | Recite met duur `_` (halve); streepje hoort hier niet                       |

#### Interacties met `-` en ELM-`~`

| Schrijfwijze              | Betekenis                                                                 |
| ------------------------- | ------------------------------------------------------------------------- |
| `(hei)`                   | Recite op “hei”, standaardduur                                            |
| `hei~`                    | Lettergreep “hei” + ELM-duur `~` (**geen** recite)                        |
| `(hei-li-ge)`             | Recite; `-` binnen haakjes = lettergreepstreepje                          |
| `Chris_-tus_`             | Twee lengte-posities; `-` tussen posities = zelfde woord                  |
| `(… voor) Chris_`         | Recite eindigt bij `)`; nieuwe positie (nieuw woord)                      |
| `(… Al)-le_…`             | Recite eindigt bij `)`; `-` = zelfde woord doorlopend                     |
| `-` op de **stemregel**   | EHM “zelfde toon” — los van lyrics-haakjes                                |
| `so-` op de **stemregel** | Octaafsuffix — geen lettergreepstreepje                                   |

#### Randgevallen

```text
# FOUT: zonder haakjes is dit geen recite; spaties maken aparte L-stukken.
L: Al-le-lu-ia, Al-le-lu-ia, …

# GOED: elke recite in eigen haakjes; cadens erbuiten.
L: (Al-le-lu-ia,) (Al-le-lu-ia,) al-le lu_&-&-&_ i_ a__ ||
```

```text
# GOED: grens is de `)`, niet een ELM midden in de tekst.
L: Komt_, (laat ons … voor) Chris_-tus_, ||

# GOED: langere recite-duur met ELM na de sluiting (_ of ~, niet kale -).
L: (Zoon van God)_ |
```

```text
# Non-interactie: ELM-`~` in een melisma is geen recite.
L: Ster~&~&~-ke_.

# Ambigu / vermijden: ELM-`-` vlak vóór een lettergreepstreepje.
# Schrijf liever ELM-`~` in het melisma: li~&~-ge  (niet li-&--ge).
```

Zie ook [Semantiek — pitfalls rond `~`](semantics.md#pitfalls-rond).

### ELM’s

De ELM-set volgt VSA 1.0 (`_`, `__`, `_.`, `-`, `~`, `.`, `..`, `-.`, `~.`,
samengesteld met `&`). Op de lyrics-regel betekent kale `-` **tussen letters**
een lettergreepstreepje; `-` **als ELM** staat in duurpositie (direct na de
lettergreep of na `&`). Direct na een recite-`)` is kale `-` **geen** ELM maar
een woordstreepje naar de volgende lettergreep; kies voor duur `_`, `~`, `.`,
`-.`, …

Leestekens mogen **achter** de lettergreep of **achter** de ELM staan en horen
bij de tekst van die lettergreep (`Komt_,`, `ia,`, `tus_,`). Binnen `(…)` horen
komma’s bij de lettergreep vóór de `)`.

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

### Kruis en mol

Chromatische verhoging of verlaging schrijf je met `#` (kruis) of `b` (mol).
**Niet** met `+` / `-`: die zijn op laddergraden en toonnamen **octaafsuffix**.

#### Laddergraden (do-re-mi)

| Vorm                         | Voorbeelden              | Betekenis                                       |
| ---------------------------- | ------------------------ | ----------------------------------------------- |
| `#` / `b` achter de graad    | `fa#` `do#` `mib` `sib`  | kruis of mol op die graad                       |
| `#` / `b` vóór de graad      | `#fa` `#do` `bmi`        | zelfde als achter de graad (VSA-EHM-herkenbaar) |
| met octaaf, kruis na graad   | `fa#-` `do#+` `sib-2`    | eerst voorteken, dan octaafsuffix               |
| met octaaf, kruis na octaaf  | `so-#` `la+#`            | eerst octaafsuffix, dan voorteken (ook geldig)  |

`so-#` en `so#-` betekenen dezelfde toon: sol, één octaaf omlaag t.o.v. het
schrijfoctaaf, mét kruis. Kies per frase één volgorde en blijf daarbij.

Nederlandse toonnamen (`fis` `bes` `cis` …) zijn een alternatief voor
`fa#` / `sib` / … en volgen dezelfde octaafregels (`fis-`, `bes-2`).

#### Toonnamen (a–g)

| Vorm        | Voorbeelden              | Betekenis                          |
| ----------- | ------------------------ | ---------------------------------- |
| kruis / mol | `f#` `fb` `bb` `Bb` `c#` | voorteken direct op de letter      |
| + octaaf    | `f#-` `bb4` `c#-2`       | wetenschappelijk cijfer of suffix  |

`b` / `B` alleen is de toonnaam **B** (Engels), niet Bes. Bes is `bb` / `Bb` /
`bes`.

Op EHM’s blijft `#\` / `b\` (en eventueel VSA-`+\`) het chromatische voorteken
vóór een relatieve stap — dat is geen laddergraad-syntax.

#### Wat niet mag (ook al is het “een toon”)

`#` / `b` mag alleen een **gangbare spelling** van een toon op of naast de
diatonische ladder in de actieve `@mode` opleveren. Een spelling die die ladder
ontwijkt of een bestaande laddertoon enharmonisch hernoemt, is een **fout**.

Voorbeelden bij `@mode major` (majeur-ladder vanaf `@do`):

| Schrijfwijze       | Waarom fout                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| `e#` / `E#` / `#e` | E♯ is enharmonisch F (= `fa` / `f` bij veel `@do`); geen eigen ladderplaats |
| `bc`               | geen geldig hoogte-token (plakt `b` en `c`); schrijf `bb`/`bes` of `c`/`do` |
| `cb` in majeur     | C♭ is enharmonisch B (= `si`/`ti` / `b`); geen gangbare majeur-spelling     |

In `@mode minor` bestaan verhoogde en verlaagde laddergraden ook, maar **op
andere treden** dan in majeur. Dezelfde letter+voorteken-combinatie kan daar
wél of juist níet kloppen — hangt van `@do` en de mineurladder af. Schrijf
chromatische tonen bij voorkeur als **laddergraad + `#`/`b`** (`si#`, `mib`)
zodat duidelijk is welke trede je bedoelt; vermijd “creatieve” enharmonieën
(`e#`, `cb`, …) die alleen via omweg dezelfde klank raken.

Validatie mag zulke spellingen als **error** melden zodra de modus bekend is;
export mag ze niet stilzwijgend “corrigeren” naar een andere trede.

## 8. Voorbeeld (één sectie, één systeem)

```text
@do G4
@mode major

@sectie voorbeeld
L: O   Hei_.-li~&~  -ge  God_.&_. | hei-li-ge Ster~&~&~-ke_. ||
S: f#4 g4    f#4&g4  a4  g4&a4    | b4  b4 b4 a4&b4&c5  b4   ||
A: d#4 e4    d#4&d#4 f#4 e4&f#4   | g4  g4 g4 f#4&g4&a4 g4   ||
T: b3  b3    b3&-    b3  b3&d4    | d4  d4 d4 d4&-&-    d4   ||
B: b2  e3    b2&-    b2  e3&f#3   | g3  g3 g3 d3&-&-    g3   ||
```

De anker-kolommen (eerste letter van elke L-positie / eerste teken van elk
hoogte-stuk) én de maatstrepen (`|` / `||`) staan op alle LSATB-regels in
dezelfde kolom; zie
[canonieke kolomuitlijning](#canonieke-kolomuitlijning-lsatb).