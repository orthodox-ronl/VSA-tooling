# Semantiek

Dit document beschrijft de betekenis van syntactisch [geldige VSA-notatie](@).

Bronbasis: `docs/spec/vsa-spec-v1.0.1.md`, aangevuld met latere documenten over [hoogte-markeringen](@) en [control tokens](@).

### Overzicht

De [VSA-notatie](@bron) wordt geïnterpreteerd via een gelaagd toonmodel:

```text
blokmetadata (`do`, `mode`, enz.)
    ↓
do-context
    ↓
modus
    ↓
toonladder
    ↓
EHM-sequenties
    ↓
muzikale posities
    ↓
rendering of export
```

De absolute toonhoogte maakt geen deel uit van de VSA-kernsyntax. Zij wordt, indien nodig voor interpretatie of MusicXML-export, geleverd via de [blokmetadata](@).

### Muzikale positie

Een [muzikale positie](@) is de kleinste muzikale eenheid binnen [VSA](@).

Elke [muzikale positie](@) heeft:

- een relatieve toonhoogtebeweging, bepaald door één [EHM](@);
- een duur, bepaald door één [ELM](@);
- een koppeling aan één [zangelement](@).

Een [zangelement-scope](@) zonder samengestelde [modifiers](@) bevat precies één [muzikale positie](@).

Voorbeeld:

```text
{/tekst_}
```

Dit betekent:

- [zangelement](@): `tekst`;
- toonhoogtebeweging: `/`;
- duur: `_`.

### Impliciete modifiers

Als in een [scope](@) geen [hoogte-modifier](@) aanwezig is, wordt impliciet één `~` gebruikt.

Als in een [scope](@) geen [lengte-modifier](@) aanwezig is, wordt impliciet één `~` gebruikt.

Voorbeeld:

```text
{tekst}
```

is semantisch gelijk aan:

```text
{~tekst~}
```

Als slechts één van beide [modifiers](@) aanwezig is, bepaalt die [modifier](@) het aantal [muzikale posities](@). De ontbrekende [modifier](@) wordt aangevuld met evenveel `~`-posities.

Voorbeeld:

```text
{/&\tekst}
```

is semantisch gelijk aan:

```text
{/&\tekst~&~}
```

### Samengestelde modifiers en melisma

Wanneer een [zangelement](@) meerdere [muzikale posities](@) bevat, wordt hetzelfde [zangelement](@) over meerdere opeenvolgende tonen gezongen. Dit heet een **melisma**.

Een melisma wordt gespecificeerd door 
- een (optionele) [hoogte modifier](@), die is samengesteld uit een rij [EHMs](@) die gescheiden zijn door `&`.
- een [zangelement](@)
- een (optionele) [lengte modifier](@), die is samengesteld uit een rij [ELMs](@) die gescheiden zijn door `&`.

Voor een melisma moet (natuurlijk) altijd tenminste of de [hoogte modifier](@), of de [lengte modifier](@) aanwezig zijn; immers, als ze er beide niet zijn is het gewoon een gezongen toon. Als een van beide ontbreekt, wordt hij geacht een rij `~` te zijn (gescheiden door `&`s) met evenveel [muzikale posities](@) als de gespecificeerde [modifier](@).

Voorbeelden:

```text
{-&/tekst~&_}
```

Dit bevat twee [muzikale posities](@):

| Positie | [EHM](@) | [ELM](@) | Betekenis                           |
| ------- | -------- | -------- | ----------------------------------- |
| 1       | `-`      | `~`      | zelfde toonhoogte, standaardduur    |
| 2       | `/`      | `_`      | één ladderstap omhoog, dubbele duur |

Het [zangelement](@) `tekst` wordt over beide posities gezongen.

Als zowel een [hoogte-modifier](@) als een [lengte-modifier](@) aanwezig zijn, moeten zij hetzelfde aantal [muzikale posities](@) bevatten.

### Do-context

De [do-context](@) is de grondtooncontext waarbinnen relatieve toonhoogtebewegingen worden geïnterpreteerd. In de zangpraktijk wordt deze context doorgaans niet expliciet genoteerd: de koorleid(st)er bepaalt de inzet op basis van de lokale traditie en vaak op basis van de toon waarop priester of diaken inzet. Koorleden volgen die context in de praktijk meestal stilzwijgend.

Voor visuele VSA-rendering hoeft de absolute [do-context](@) daarom niet in de zangtekst aanwezig te zijn. Voor MusicXML-export, automatische weergave of afspelen is wel een absolute starttoon nodig. Die wordt gespecificeerd in de Hugo [blokmetadata](@):

```markdown
::: vsa-notatie
do="C4"
mode="major"
:::
```

Hier levert `do="C4"` de absolute starttoon voor interpretatie en export. De [toonhoogte-markeringen](@) in de [VSA-tekst](@) zelf bevatten uitsluitend relatieve [hoogte-modifiers](@).

### Toonladder en toonladdergraden

Binnen een [do-context](@) wordt een geordende reeks toonladdergraden afgeleid:

```text
do → re → mi → fa → sol → la → ti → do
```

Deze graden vormen een cyclische structuur.

De afstand tussen opeenvolgende graden is niet uniform. De stapstructuur wordt bepaald door de gekozen modus.

### Modusdefinitie

Een modus definieert de intervalstructuur van de toonladder binnen een [do-context](@).

Een modus specificeert voor elke overgang tussen opeenvolgende graden of deze overgang een grote stap of een kleine stap is.

De zeven overgangen zijn:

```text
do→re, re→mi, mi→fa, fa→sol, sol→la, la→ti, ti→do
```

Een modus kan worden weergegeven als een patroon van zeven staptypen:

```text
G = grote stap
K = kleine stap
```

#### Majeurmodus

In de majeurmodus zijn de kleine stappen:

- `mi → fa`;
- `ti → do`.

Representatie:

```text
G G K G G G K
```

#### Natuurlijke mineurmodus

In de natuurlijke mineurmodus zijn de kleine stappen:

- `re → mi`;
- `sol → la`.

Representatie:

```text
G K G G K G G
```

#### Andere modi

Andere modi kunnen worden gedefinieerd door het stappatroon te wijzigen.

Voorbeelden:

```text
Dorisch:   G K G G G K G
Frygisch:  K G G G K G G
Lydisch:   G G G K G G K
```

De [do-context](@) bepaalt dus het startpunt. De modus bepaalt de interne structuur van de toonladder.

### Interpretatie van EHMs

Een [EHM](@) is een operator op de actuele toonladderpositie. Een [EHM](@)
bestaat uit een optionele halftoon-prefix (accidens) en een basisbeweging.

Twee lagen worden strikt gescheiden:

1. **Diatonische cursor** — de actuele toonladdergraad t.o.v. de
   [do-context](@) en modus. Alleen basisbewegingen (`/`, `\`, `-`, `~`, en
   gestapelde strepen) verplaatsen deze cursor.
2. **Accidens / halftoon-prefix** (`#` / `+` / `♯`, `b` / `♭`) — tijdelijke
   wijziging van de **klinkende toon** op de graad *ná* toepassing van de
   basisbeweging van díe [EHM](@). De prefix verandert de diatonische cursor
   niet.

**Zelfde toon behouden:** een [EHM](@) zonder ladderstap en zonder nieuwe
prefix (`~`, `-`, of impliciet `~`), én ongescopte reciteertekst, neemt de
**klinkende toon van de voorgaande noot** over — inclusief accidens. Zo klinken
`{+\go}{ri}{/os}` en `{+\go}ri{/os}` hetzelfde (Cis blijft op `ri` zonder
`#-` te schrijven). Een latere ladderstap (`/`, `\`, …) start vanaf de
natuurlijke graad, tenzij díe [EHM](@) opnieuw een prefix heeft.

#### Tot hoever werkt de halftoon? (normatief)

In **klassieke muzieknotatie** geldt een voorteken (kruis, mol) tot de
**volgende maatstreep**, of tot een **herstelteken** / nieuw voorteken op
dezelfde nootletter. Alle latere noten van die letter in dezelfde maat
blijven gewijzigd, ook als je tussendoor andere tonen zingt.

In **[VSA](@)** is dat **anders**. Een halftoon-prefix geldt alleen voor:

1. de **aankomsttoon** van díe [EHM](@), en
2. elke **onmiddellijk volgende zelfde-toon** (`~`, `-`, impliciet `~`,
   ongescopte recite) — zolang er geen nieuwe ladderstap komt.

De halftoon stopt bij de **eerste volgende ladderstap** (`/`, `\`, `//`, …)
zonder nieuwe prefix: die landt op de **natuurlijke** laddertoon van de
nieuwe graad. Een maatstreep (`//`, `[*]`, …) **beëindigt het VSA-accidens
niet**; zelfde-toon na een maatstreep houdt de chromatische klinktoon vast.

| Situatie | Klassieke notatie | [VSA](@) |
| -------- | ----------------- | -------- |
| C♯, daarna opnieuw C in dezelfde maat (via andere toon ertussen) | C blijft kruis tot maatstreep of ♮ | terugkeer via `\` / `/` zonder prefix → **natuurlijke** C |
| C♯, daarna zelfde toon (`-` / recite) | C♯ | C♯ |
| C♯, maatstreep, daarna opnieuw C zonder nieuw teken | meestal natuurlijke C | zelfde-toon na maatstreep → **nog steeds** C♯ |

Werkvoorbeelden: [Halftoon-prefix combinaties (voorbeelden)](#halftoon-prefix-combinaties-voorbeelden)
en [Kruis en mol](../reference/voorbeelden/kruis-en-mol.md#tot-hoever-werkt-de-halftoon).

`+` is een spelling/alias van `#` (zelfde semantiek), geen aparte operator.

Dit is **niet** een cumulatief “netto = basis ± ½ toon”-model waarin de
prefix de cursor chromatisch verschuift. Een reeks `#\` daarna `/` brengt de
cursor terug op de startgraad; de klinkende eindtoon (zonder nieuwe prefix)
is weer de natuurlijke laddertoon.

#### Basisbewegingen

| [EHM](@) | Semantisch effect            |
| -------- | ---------------------------- |
| `/`      | verplaats één graad omhoog   |
| `//`     | verplaats twee graden omhoog |
| `///`    | verplaats drie graden omhoog |
| `////`   | verplaats vier graden omhoog |
| `/////`  | verplaats vijf graden omhoog |
| `\`      | verplaats één graad omlaag   |
| `\\`     | verplaats twee graden omlaag |
| `\\\`    | verplaats drie graden omlaag |
| `\\\\`   | verplaats vier graden omlaag |
| `\\\\\`  | verplaats vijf graden omlaag |
| `-`      | behoud de huidige graad      |
| `~`      | behoud de huidige graad      |

#### Halftoon-prefix: cursor vs. klinkende toon (normatief)

| [EHM](@) | Cursor (basis) | Accidens op aankomsttoon | Daarna |
| -------- | -------------- | ------------------------ | ------ |
| `#/`     | +1 graad       | kruis                    | volgende ladderstap: natuurlijke nieuwe graad; `~`/`-`/recite: zelfde klinktoon |
| `b/`     | +1 graad       | mol                      | idem |
| `#\`     | −1 graad       | kruis                    | idem |
| `b\`     | −1 graad       | mol                      | idem |
| `#-`     | 0              | kruis op huidige graad   | `~`/`-`/recite houden die klinktoon |
| `b-`     | 0              | mol op huidige graad     | `~`/`-`/recite houden die klinktoon |

#### Acceptatievoorbeelden (normatief)

Met `do="C4"` en `mode="major"`, startcursor op do (graad 0):

| Reeks | Cursor na reeks | Klinkende tonen (spelling) | Eindklank = start? |
| ----- | --------------- | -------------------------- | ------------------ |
| `#\` daarna `/` | do (0) | B3# (ti met kruis), daarna C4 | ja |
| `b/` | re (1) | D♭4 | nee (cursor op re) |
| `b/` daarna `-` | re (1) | D♭4, daarna D♭4 (zelfde toon) | — |
| `#-` | do (0) | C#4 | cursor ongewijzigd |
| `b-` | do (0) | C♭4 | cursor ongewijzigd |

Met startmarkering `[/:]` (graad = re = D4):

| Reeks | Klinkende tonen | Cursor-eind |
| ----- | --------------- | ----------- |
| `{+\go}{ri}{/os}` | D→C♯→C♯→D | weer re |
| `{+\go}ri{/os}` (ongescopte `ri`) | D→C♯→C♯→D | weer re |

Met `do="F4"` en `mode="major"` (non-C, enharmoniek):

| Reeks | Cursor na reeks | Klinkende tonen (spelling) | Eindklank = start? |
| ----- | --------------- | -------------------------- | ------------------ |
| `#\` daarna `/` | do (0) | E4# (ti met kruis), daarna F4 | ja |
| `b/` | re (1) | G♭4 | cursor op re |

Contrast met het afgewezen float-model: onder “netto = basis ± ½” zou
`+\` gevolgd door `/` klinken als `b/` (blijvend een half trede verschoven).
In dit model is dat **niet** zo: `#\`+`/` herstelt cursor én natuurlijke
laddertoon.

[EHMs](@) worden sequentieel toegepast. Bij [blokmetadata](@) `do="C4"` en
`mode="major"` produceert de EHM-reeks `/`, `\\`, `///` de toonreeks:

```text
C4 → D4 → B3 → E4
```

Hierbij wordt uitgegaan van opeenvolgende toonladderstappen binnen de gekozen modus.

MusicXML-export: de diatonische graad bepaalt `<step>` / octaaf via de
modus; de halftoon-prefix bepaalt `<alter>` op díe noot. Zelfde-toon
voortzetting (`~`/`-`/recite) herhaalt de vorige klinkende toon (inclusief
`<alter>`). Daarnaast schrijft de exporter een zichtbaar
`<accidental>` (kruis, mol, of `natural` als herstelteken) wanneer de
klinkende alteratie afwijkt van de toonsoort of van een eerder voorteken
op dezelfde nootletter in dezelfde maat. Zo krijgt C♯ → D → C in één maat
op de laatste C een herstelteken, terwijl `{+\go}{ri}` het kruis slechts
één keer toont.

### Geldigheid van halftoon-prefix combinaties

Een [EHM](@) met halftoon-prefix is syntactisch alleen geldig wanneer de
prefix onmiddellijk vóór een basisbeweging staat (geen standalone `#`/`b`).

Semantisch:

1. de basisbeweging verplaatst (of behoudt) de **diatonische cursor** zoals
   zonder prefix;
2. de prefix is een tijdelijk **accidens** op de aankomstgraad (MusicXML
   `<alter>`); of een gegeven modus/export die spelling weigert, is een
   aparte geldigheidsregel — zij verschuift de cursor niet.

Voorbeeld (geen cursorvergiftiging):

```text
::: vsa-notatie
do="C4"
mode="major"

[//:] {#/tekst}
:::
```

Start op `mi` (`[//:]`): `#/` zet de cursor op `fa` met kruis (klinkend F#
bij do=C). De volgende [EHM](@) start vanaf natuurlijke `fa`, niet vanaf een
“½-trede tussen mi en fa”.

`#-` / `b-` blijven “chromatisch op huidige graad, cursor ongewijzigd”.
`b/` is één ladderstap omhoog plus mol op de aankomstgraad — niet een
verschuiving van de diatonische cursor met een half trede.

Een historische schrijfwijze zoals `{-\…}` is geen geldige [EHM](@)
(syntaxfout).

Hoogte-markeringen (`[…:]`) controleren de **diatonische cursor**. Een
accidens-prefix op een markering wijzigt die cursorcontrole niet; de
canonieke herstelmarkering is steeds graad-only (`[:]`, `[/:]`, `[\\:]`, …).

### Halftoon-prefix combinaties (voorbeelden)

Onderstaande frasen laten zien wat een kruis of mol **doet** en wat het
**niet** doet — vooral **tot hoever** de halftoon klinkt. Werkvoorbeeld met
CLI: [Kruis en mol](../reference/voorbeelden/kruis-en-mol.md).

#### Tot hoever klinkt het kruis? Contrast met maatstreep-regel

Met `do="C4"`, start `[:]`. In klassieke notatie zou één kruis op C alle
latere C’s in de maat wijzigen tot een herstelteken of maatstreep. In
[VSA](@) niet.

**A — halftoon stopt bij de volgende ladderstap (zelfde maat):**

```text
[:] {#-Cis}{/Re}{\Do} [:]
```

| Lettergreep | Klinkend | Waarom |
| ----------- | -------- | ------ |
| Cis | C♯ | `#-` zet kruis op do |
| Re | D | `/` = ladderstap → natuurlijke re |
| Do | C | `\` = ladderstap → **natuurlijke** do (geen blijvend kruis op C) |

In klassieke notatie zou de laatste C in dezelfde maat nog C♯ zijn tenzij
een ♮ geschreven staat. [VSA](@) hoeft geen herstelteken-prefix: de
ladderstap zonder prefix is genoeg. MusicXML-export zet wél een zichtbaar
`natural` op die laatste C, zodat de partituur dezelfde klinkende reeks toont.

**B — halftoon blijft op zelfde-toon, ook over een maatstreep:**

```text
[:] {#-Cis}{-nog} // {-verder} [:]
```

| Lettergreep | Klinkend | Waarom |
| ----------- | -------- | ------ |
| Cis | C♯ | `#-` |
| nog | C♯ | `-` = zelfde toon |
| (maatstreep) | — | beëindigt het VSA-accidens **niet** |
| verder | C♯ | `-` na maatstreep houdt nog steeds Cis |

In klassieke notatie zou `verder` zonder nieuw kruis meestal natuurlijke C
zijn. In [VSA](@) blijft de klinkende toon chromatisch tot er een
ladderstap zonder prefix komt.

**C — na maatstreep wél natuurlijk, omdat er een ladderstap is:**

```text
[:] {#-Cis} // {/Re} [:]
```

| Lettergreep | Klinkend | Waarom |
| ----------- | -------- | ------ |
| Cis | C♯ | `#-` |
| Re | D | `/` na de maatstreep → natuurlijke re; cursor op re |

#### Kruis op een dalende stap, daarna omhoog — cursor en natuurlijke toon herstellen

Met `do="C4"`, start `[:]`:

```text
[:] {+\neer}{/terug} [:]
```

| Stap | [EHM](@) | Cursor | Klinkend | Toelichting |
| ---- | -------- | ------ | -------- | ----------- |
| 1 | `+\` (`#\`) | ti | B♯ | ladderstap omlaag + kruis op aankomst |
| 2 | `/` | do | C | ladderstap omhoog; **geen** prefix → natuurlijke do |

De eindmarkering `[:]` slaagt: cursor en klinkende eindtoon zijn weer do.
Onder het afgewezen “basis ± ½”-model zou stap 2 klinken als D♭ en zou de
eindcontrole falen.

#### Mol omhoog, daarna zelfde toon — accidens blijft klinken

```text
[:] {b/om}{-hoog} [/:]
```

| Stap | [EHM](@) | Cursor | Klinkend | Toelichting |
| ---- | -------- | ------ | -------- | ----------- |
| 1 | `b/` | re | D♭ | ladderstap omhoog + mol |
| 2 | `-` | re | D♭ | zelfde toon: mol blijft zonder `b-` opnieuw |

Eindmarkering `[/:]` controleert alleen de **graad** re, niet of re mol of
natuurlijk klinkt.

#### Gregos-achtig: kruis vasthouden op de volgende lettergreep

```text
[/:] {+\go}{ri}{/os} [/:]
```

| Lettergreep | Bron | Klinkend (start re = D) |
| ----------- | ---- | ----------------------- |
| go | `+\` | C♯ |
| ri | impliciet `~` | C♯ (zelfde klinktoon) |
| os | `/` | D (natuurlijke re) |

`{+\go}ri{/os}` (ongescopte `ri`) klinkt hetzelfde.

#### Herstelteken in MusicXML op dezelfde nootletter

```text
[:] {#-Cis}{/Re}{\Do} [:]
```

| Noot | `<alter>` | Zichtbaar `<accidental>` |
| ---- | --------- | ------------------------ |
| Cis | `1` | `sharp` |
| Re | (geen) | (geen) |
| Do | (geen) | `natural` (herstelteken) |

[VSA](@) heeft geen aparte herstelteken-prefix; de natuurlijke C volgt uit
`\` zonder prefix. De MusicXML-export voegt het herstelteken toe zodat de
partituur dezelfde semantiek toont als de klinkende toonreeks.

#### Combinatietabel (snelle referentie)

| [EHM](@) | Cursor | Accidens | Typisch gebruik |
| -------- | ------ | -------- | --------------- |
| `#/` of `+/` | +1 | kruis | chromatische stijging |
| `b/` | +1 | mol | chromatische stijging met mol |
| `#\` of `+\` | −1 | kruis | chromatische daling (Liturgikon-`+` op `\`) |
| `b\` | −1 | mol | chromatische daling met mol |
| `#-` of `+-` | 0 | kruis | kruis op huidige graad |
| `b-` | 0 | mol | mol op huidige graad |
| `-` / `~` na accidens | 0 | (geen nieuwe) | houdt klinkende toon inclusief accidens |
| `/` of `\` na accidens | ±1 | (geen) | natuurlijke nieuwe graad |

### Interpretatie van ELMs

Een [ELM](@) bepaalt de duur van één [muzikale positie](@) ten opzichte van de standaardduur.

| [ELM](@) | Duur                |
| -------- | ------------------- |
| `-`      | 1 × standaardduur   |
| `~`      | 1 × standaardduur   |
| `-.`     | 1½ × standaardduur  |
| `~.`     | 1½ × standaardduur  |
| `_`      | 2 × standaardduur   |
| `_.`     | 3 × standaardduur   |
| `__`     | 4 × standaardduur   |
| `.`      | 1/2 × standaardduur |
| `..`     | 1/4 × standaardduur |

Voor MusicXML-export wordt de standaardduur gemapt naar een kwartnoot, tenzij extern anders gespecificeerd.

### Absolute en relatieve toonhoogte

[VSA](@) legt toonhoogten primair relatief vast. Elke [muzikale positie](@) bevat een [EHM](@) die de toonhoogteverandering ten opzichte van de voorgaande [muzikale positie](@) specificeert.

Een absolute toonhoogte kan nodig zijn voor interpretatie, validatie of MusicXML-export, maar staat niet in de [toonhoogte-markering](@). Zij wordt via [blokmetadata](@) geleverd.

Voorbeeld:

```markdown
::: vsa-notatie
do="C4"
mode="major"

[:] {\O}, {/Hei__}{\&/li}{/ge} {\&/God__&__}
:::
```

produceert, bij interpretatie in majeur met `C4` als `do`, de toonreeks:

```text
B3 C4 B3 C4 D4 C4 D4
```

### Toonhoogte-markeringen

Een [toonhoogte-markering](@) bevat alleen een relatieve [hoogte-modifier](@) en geeft daarmee aan op welke toonladdergraad de zang zicht bevindt ten opzichte van de [do-context](@) op de positie van die [toonhoogte-markering](@).

Elke [hoogte-markering](@) geeft een (toon)hoogte aan ten opzichte van de basistoon ('do').

Voor de eerste [hoogte-markering](@) wordt de hoogte (of basistoon) extern gegeven. 
In de praktijk van het zingen wordt dit aangegeven door de koorlei(st)er.
Binnen de context van conversies, bijvoorbeeld naar MusicXML, wordt dat gespecificeerd 
door de feitelijke conversie - dat is buiten de scope van [VSA](@).

Elke volgende [hoogte-markering](@) geeft aan dat de zang op die positie op die hoogte moet zitten. 
Een latere [hoogte-markering](@) vervangt dus niet de eerdere markering als documentstructuur, maar introduceert een nieuwe toonhoogte-positie in dezelfde melodische lijn.

Het is een gangbare praktijk om voor een [zangstuk](@bron) een [hoogte-markering](@) te schrijven,
en om dit ook aan het eind van een [zangstuk](@bron) te doen (ter controle voor zangers).
Indien twee [zangstukken](@bron) elkaar opvolgen, kan dat vanuit [VSA](@) perspectief dan ook
gezien worden als een enkel [zangstuk](@bron) met tussenliggende [hoogte-markeringen](@).


 Een beginmarkering `[:]` betekent dat de zang op de [do-context](@) begint. Een markering `[//:]` betekent dat de zang twee ladderstappen boven de [do-context](@) begint.

Een eindmarkering kan worden gebruikt als visuele afsluiting en als semantische eindcontrole. Een ontbrekende eindmarkering is toegestaan en betekent dat er geen expliciete eindtooncontrole is genoteerd. Een eindmarkering `[:]` is niet leeg in semantische zin: zij betekent dat de zang op de [do-context](@) eindigt en is equivalent aan `[-:]` c.q. `[~:]`. Een markering `[//:]` betekent dat de zang twee ladderstappen boven de [do-context](@) eindigt. Een implementatie mag een aanwezige eindmarkering controleren tegen de berekende eindtoon van het [zangstuk](@bron).

### Tekstmarkeringen buiten scopes

Bepaalde tekstfragmenten buiten [scopes](@) kunnen door implementaties semantisch worden geïnterpreteerd.

| Tekst | Betekenis                    | MusicXML           |
| ----- | ---------------------------- | ------------------ |
| `*`   | rustpunt of ademhaling       | ademteken          |
| `/`   | frasescheiding of maatstreep | maatstreep         |
| `//`  | sterke frasescheiding        | dubbele maatstreep |

Deze markeringen maken geen deel uit van de kernsyntax van [VSA-scopes](@),
maar mogen door [renderers](@) of weergavecomponenten en exporteurs semantisch worden verwerkt.

---
