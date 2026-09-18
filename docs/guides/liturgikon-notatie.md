# Liturgikon-notatie

## Appendix 1 - Uitleg van notatie volgens Nederlands Liturgikon

Onderstaande tekst is overgenomen uit het Liturgikon, pp 27-30 (een uitgave van
de Nederlands Orthodoxe Kerk, dr. Kuyperstraat 2, den Haag, maart 1968):

### De Muziek

Hoewel overal in de Orthodoxe Kerken dezelfde liturgische teksten worden gebruikt, 
is er geen algemene muziektraditie. In Griekenland en de Balkanlanden worden nog 
de oude eenstemmige melodieën gebruikt, die echter merkbaar een Turkse invloed 
hebben ondergaan.

De Russische Kerk heeft sinds een eeuw de meerstemmige muziek ingevoerd, 
volgens de Europese harmonieleer. Het gebruik van een of meer tegenstemmen 
is al veel ouder. Ook de Griekse kerkmuziek kent de *ison*, de op één toonhoogte 
aangehouden begeleidende grondtoon.

De Nederlandse Kerk, evenals de meeste Missiekerken, heeft zich aangesloten 
bij het Russische gebruik, omdat dit reeds met beperkte en weinig‑geschoolde 
krachten tot een aannemelijk resultaat voert.

Maar ook in deze melodieën is veel verscheidenheid, zodat een bepaalde keuze 
gedaan moest worden. Om voor de hand liggende redenen zijn hiervoor meestal 
de eenvoudigste voorbeelden genomen.

Alle russische componisten hebben ook kerkmuziek geschreven. 
Veel daarvan draagt een concertkarakter of is slechts voor grotere koren geschikt. 
Maar onder hun werk bevinden zich ook onsterfelijk‑schone eenvoudige melodieën. 
Wie slechts ééns het vastenlied *‘Aan de stromen van Babylon…’* of op Goede Vrijdag 
*‘De rechtvaardige Josef…’* heeft horen zingen, weet dat hij deze zangen nooit meer 
vergeten zal. En eigenlijk kan hetzelfde al gezegd worden van het gewone 
*Kyrie eleison*, of het *‘Wij prijzen U…’* van elke heilige Liturgie.

De vierstemmige liturgiemuziek is apart uitgegeven. 
In deze uitgave is alleen de melodie aangegeven, in een vereenvoudigd neumenschrift.

### De Muzieknotatie

Deze kan het best duidelijk gemaakt worden aan de hand van enkele voorbeelden.

![Drie voorbeelden van de notatie](assets/liturgikon-voorbeelden.jpg)

De tekens bóven de tekst geven een verandering van toonhoogte aan. 
Het aantal boven elkaar geplaatste stijgende of dalende strepen betekent een 
stijging of daling van de melodie van evenveel tonen.

Wanneer een notengroep op dezelfde toon begint als de laatstgezongen toon, 
wordt deze aangegeven met een horizontaal streepje 
(zie het begin van het derde voorbeeld).

![Derde voorbeeld](assets/liturgikon-voorbeeld-3.jpg)

Om de plaats van de melodie in de toonladder vast te leggen, wordt voor het stuk 
de eerste toon aangegeven. Staat er alleen een liggend streepje, dan begint de zang 
op de grondtoon (do). Hiervoor wordt, zo mogelijk, de toon van priester of diaken 
aangehouden.

Deze ‘do’ moet dus niet verward worden met de ‘c’, die een vaste toonhoogte heeft. 
Staat een stuk met één kruis geschreven, dan is ‘g’ de grondtoon of de ‘do’, enz. 
Zo is in het tweede voorbeeld de begintoon een ‘mi’, maar die zal in werkelijkheid 
gezongen worden op ‘a’, of in die buurt. Dit moet de koorleider bepalen.

De gekozen notatie geeft dus uitsluitend de relatieve toonhoogte aan ten opzichte 
van de laatst gezongen toon, d.w.z. dat als men ergens een verkeerd interval 
genomen heeft, dan de hele rest verkeerd uitkomt; maar bij enigermate bekende 
melodieën bestaat hiervoor in de praktijk geen gevaar. Het is natuurlijk een nadeel, 
maar daar staat tegenover dat deze tekens veel vlotter geleerd worden dan noten 
lezen, en dat het gebruik mogelijk is waar muzieknotatie te kostbaar zou zijn. 
De slottoon wordt telkens aangegeven, om de overgang naar een volgend stuk te weten.

![Tweede voorbeeld](assets/liturgikon-voorbeeld-2.jpg)

Een kruis (+) betekent een extra stijging van een halve toon; 
een mol (♭) een extra daling van een halve toon. 
Zo worden ze ook als herstellingstekens gebruikt (zie bovenstaand voorbeeld).

Wanneer een zelfde melodietje steeds herhaald wordt, zoals bv. in de Zaligsprekingen, 
dan worden deze tekens niet steeds weer geschreven, omdat het oor zich gemakkelijk 
aanpast aan de andere toonschaal.

![Derde voorbeeld](assets/liturgikon-voorbeeld-3.jpg)

De tekens onder de tekst geven de duur van de tonen aan. 
Zonder teken duurt elke noot één tel, of een kwartnoot. 
Een horizontale onderstreping verdubbelt de duur tot een halve noot, twee tellen. 
Dubbele onderstreping is vier of drie tellen (zie slot van 2e en 3e voorbeeld).

Een punt of verticaal streepje onder de tekst maakt deze tot een achtste noot 
of halve tel (zie 3e voorbeeld).

Het einde van een muzikaal zinsdeel wordt aangegeven door een sterretje (*) 
tussen de tekst, en dit zal dus vaak een rustteken zijn.

Er is geen strakke maat: het ritme moet de zinsbouw en de betekenis 
zo duidelijk mogelijk doen uitkomen.

De muziektekens zijn een uiterste vereenvoudiging van het oude Neumenschrift, 
uit de tijd dat er nog geen notenbalk was uitgevonden. 
Zij hebben het voordeel van een heel grote ruimtebesparing, 
en zijn vooral bruikbaar voor eenvoudige melodieën, 
zoals die juist in de kerkmuziek het meeste voorkomen. 
Ze kunnen ook gemakkelijk aan bestaande boeken worden toegevoegd.

### Relatie tussen de Liturgikon-notatie en VSA

De [VSA-notatie](@bron) is sterk geïnspireerd door de vereenvoudigde neumennotatie zoals beschreven in het Nederlands Liturgikon (1968), maar is daar niet volledig identiek aan. [VSA](@) formaliseert en generaliseert verschillende aspecten van deze praktijknotatie om parsing, validatie, rendering en export naar formaten zoals SVG en MusicXML mogelijk te maken.

De belangrijkste verschillen zijn:

| Onderwerp          | Liturgikon-notatie                              | [VSA](@)                                                                                            |
| ------------------ | ----------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Doel               | Praktische zanghulp voor menselijke zangers     | Formele, machine-verwerkbare notatie                                                                |
| Syntax             | Geen formele grammatica                         | Volledig formele syntax (EBNF)                                                                      |
| Structuur          | Markeringen direct boven/onder tekst            | Gestructureerde [scopes](@) `{...}`                                                                 |
| Toonhoogte         | Relatieve intervalnotatie                       | Relatieve toonladder-notatie binnen een [do-context](@)                                             |
| `#`/`b` als prefix | Extra halve toon bovenop een bestaande beweging | Accidens-prefix vóór een basisbeweging; wijzigt alleen de klinkende aankomsttoon, niet de diatonische cursor; aliases: `+`/`♯` voor `#`, `♭` voor `b` |
| Lege posities      | Impliciet                                       | Expliciet via `~`                                                                                   |
| Melisma            | Impliciet / ad hoc                              | Formeel model via samengestelde [modifiers](@)                                                      |
| Validatie          | Alleen muzikaal gehoor                          | Syntactische en semantische validatie                                                               |
| Export             | Niet voorzien                                   | SVG en MusicXML                                                                                     |

#### Wat een kruis en een mol in VSA doen

In het Liturgikon staat dat een kruis (`+`) een *extra* stijging van een
halve toon betekent bovenop een bestaande richtingspijl, en een mol (`♭`)
een *extra* daling. Die formulering is bedoeld voor zangers die op het
blad lezen. [VSA](@) moet dezelfde muzikale bedoeling machineleesbaar
maken, en splitst daarom twee lagen strikt:

1. **Diatonische cursor** — waar je op de toonladder staat (do, re, mi, …).
   Alleen de basisbeweging (`/`, `\`, `-`, `~`, gestapelde pijlen) verplaatst
   die cursor.
2. **Accidens (kruis of mol)** — een tijdelijke wijziging van de
   **klinkende** toon op de graad *ná* die basisbeweging. De prefix
   (`#` / `+` / `♯`, of `b` / `♭`) schuift de cursor **niet** chromatisch mee.

Concreet:

- `{+/syllabe}` = één ladderstap omhoog, **én** een kruis op de aankomsttoon.
- `{+\syllabe}` = één ladderstap omlaag, **én** een kruis op de aankomsttoon.
- `{#-syllabe}` = cursor blijft staan; alleen een kruis op de huidige graad.
- Zelfde-toon (`{ri}`, `{-…}`, `{~…}`, of ongescopte tekst) houdt de
  **klinkende** toon vast, inclusief een eerder kruis of mol — zonder dat je
  `#-` opnieuw hoeft te schrijven.
- Een latere ladderstap zonder nieuwe prefix landt weer op de **natuurlijke**
  laddertoon van die graad (het accidens “verdampt” met de cursorstap).

Dat is **niet** het afgewezen model “netto = basis ± ½ toon”, waarin de
prefix de cursor blijvend een half trede verschuift. Onder dat model zou
`{+\neer}{/terug}` eindigen alsof je `{b/…}` had gezongen, en zou een
eindmarkering `[:]` ten onrechte falen. Zie
[Interpretatie van EHMs](../specification/semantics.md#interpretatie-van-ehms)
en het werkvoorbeeld
[Kruis en mol](../reference/voorbeelden/kruis-en-mol.md).

**Herstelteken:** het Liturgikon gebruikt `+` en `♭` soms ook als
herstellingsteken op het blad. [VSA](@) heeft geen aparte
“herstelteken”-prefix. Terugkeer naar de natuurlijke laddertoon gebeurt
door een ladderstap **zonder** nieuwe halftoon-prefix. Bij MusicXML-export
schrijft de tool wél een zichtbaar `<accidental>natural</accidental>`
wanneer die terugkeer in dezelfde maat op dezelfde nootletter nodig is
(bijvoorbeeld C♯ → D → C).

Voorbeelden van de correspondentie:

| Liturgikon | [VSA](@) | Cursor            | Klinkend op aankomsttoon    |
| ---------- | -------- | ----------------- | --------------------------- |
| `+` op `/` | `#/`     | +1 graad          | kruis                       |
| `♭` op `/` | `b/`     | +1 graad          | mol                         |
| `+` op `\` | `#\`     | −1 graad          | kruis                       |
| `♭` op `\` | `b\`     | −1 graad          | mol                         |
| `+` op `-` | `#-`     | ongewijzigd       | kruis (chromatisch)         |
| `♭` op `-` | `b-`     | ongewijzigd       | mol (chromatisch)           |

Een standalone `#` of `b` zonder basisbeweging is niet geldig in [VSA](@). Als een historische notatie een kruis of mol plaatst bij een toon zonder expliciete richtingspijl, moet dit in [VSA](@) worden uitgeschreven als `#-` of `b-`.

#### Praktijkvoorbeeld: kruis daarna omhoog eindigt weer op do

Het Liturgikon-citaat (“extra stijging van een halve toon”) lijkt op een
lineair “basis ± ½”-model. Als je dat letterlijk in de **cursor** zou stoppen,
dan zou `{+\neer}{/terug}` klinken als een enkele `{b/…}`: je komt niet terug
op de begintoons. Dat is funest voor eindcontrole en later voor meerstemmige
cursors.

In [VSA](@) is `+` een kruis op de aankomstgraad (hier: ti), en `/` beweegt
alleen de diatonische cursor weer omhoog naar do. Zelfde-toonlettergrepen
(`{ri}` of ongescopte `ri`) houden de klinkende toon vast — zonder `#-` te
hoeven schrijven. Zichtbaar via eindmarkering `[:]` en MusicXML (`B#` → … → `C`).

Bestand: `examples/docs-walkthroughs/halftoon-accidens-cursor.vsa`

```text
[:] {+\neer}{/terug_} op do. [:]

[:] {b/om}{-hoog_} op re. [/:]
```

| Frase | Wat je hoort / ziet (do=C4) | Wat validatie checkt |
| ----- | --------------------------- | -------------------- |
| A `{+\neer}{/terug}` | B♯, dan C; eindklank = start | eindmarkering `[:]` = graad do → OK |
| B `{b/om}{-hoog}` | D♭, dan D♭ (zelfde toon houdt mol) | eindmarkering `[/:]` = graad re → OK |

Controleer lokaal:

```cmd
vsa validate examples\docs-walkthroughs\halftoon-accidens-cursor.vsa
```

Bij omzetting van historische notaties naar [VSA](@) kunnen de volgende situaties optreden:

- historische notaties laten sommige toonladderinformatie impliciet, terwijl [VSA](@) die expliciet moet modelleren;
- melismatische passages moeten in [VSA](@) soms explicieter worden gespecificeerd dan in historische bronnen.

[VSA](@) moet worden gezien als een geformaliseerde afleiding van deze historische praktijknotatie, niet als een exacte reproductie ervan.
