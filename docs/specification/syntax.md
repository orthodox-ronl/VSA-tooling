# Syntax

Dit document beschrijft de normatieve VSA-syntax.

Bronbasis: `docs/spec/vsa-spec-v1.0.1.md`, aangevuld met latere documenten over [control tokens](@), comments en includes waar die syntax uitbreiden.

### Hugo Markdown bloksyntax

VSA-[zangstukken](@bron) worden beschreven in een zo genaamd `Hugo Markdown blok` (zie [EBNF voor Hugo Markdown bloksyntax](#ebnf-voor-hugo-markdown-bloksyntax) voor de formele syntax, en [Semantiek](semantics.md)). We geven hier alvast een voorbeeld:

```markdown
::: vsa-notatie
do="F4"
mode="major"
tempo="120"
validate-ending="true"
duration-model="default"

[:] {/Hei_}{/lig_} is de Heer. [//:]
:::
```

De [blokparameters](@) behoren niet tot de zichtbare [VSA-notatie](@bron), maar leveren context voor validatie, rendering en export. Absolute toonhoogten, modi, tempi e.d. worden als parameters gespecificeerd, en niet in het [zangstuk](@bron) (in het voorbeeld: `[:] {/Hei_}{/lig_} is de Heer. [//:]`). Dit sluit aan bij de praktijk waarin alleen [zangstukken](@bron) op papier staan, en de eigenlijke toon waarop gezongen wordt, de modi en tempi worden aangegeven door de koorleider.

Een aantal parameters van de bloksyntax hebben normatieve defaultwaarde, wat het mogelijk maakt om blokken waarin deze parameters niet zijn gespecificeerd, toch speelbaar te maken. Het gaat om de volgende parameters:

| Parameter         | Default waarde | Betekenis                                                                     |
| ----------------- | -------------- | ----------------------------------------------------------------------------- |
| `do`              | `F4`           | absolute starttoon voor interpretatie en MusicXML-export                      |
| `mode`            | `major`        | modusdefinitie voor toonladderinterpretatie                                   |
| `tempo`           | `120`          | tempo voor MusicXML-export                                                    |
| `validate-ending` | `true`         | controleer een aanwezige eindtoonhoogte-markering tegen de berekende eindtoon |
| `duration-model`  | `default`      | mapping van ELM-duurwaarden naar MusicXML-durationwaarden                     |

Andere parameters mogen eveneens voorkomen, bijvoorbeeld `title`, `subtitle`, `composer`, `language`, `meter`, `tone` of renderer-specifieke [metadata](@). Zie Appendix 3 voor voorbeelden. De [blokmetadata](@) heeft voorrang op implementatie-defaults.

#### EBNF voor Hugo Markdown bloksyntax

```ebnf
vsa-codeblok ::=
    "::: vsa-notatie"
    { newline parameter }
    newline
    zangstuk
    newline
    ":::" ;

parameter ::= bekende-parameter | vrije-parameter ;

bekende-parameter ::=
      do-parameter
    | mode-parameter
    | tempo-parameter
    | validate-ending-parameter
    | duration-model-parameter ;

do-parameter ::= 'do="' absolute-toonhoogte '"' ;

absolute-toonhoogte ::= toonnaam [ alteratie ] octaaf ;
toonnaam ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" ;
alteratie ::= "#" | "♯" | "b" | "♭" ;
octaaf ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" ;

mode-parameter ::= 'mode="' identifier '"' ;
tempo-parameter ::= 'tempo="' integer '"' ;
validate-ending-parameter ::= 'validate-ending="' boolean '"' ;
duration-model-parameter ::= 'duration-model="' identifier '"' ;

vrije-parameter ::= identifier '="' parameter-waarde '"' ;
parameter-waarde ::= ? elk Unicode-karakter behalve '"' en newline ? ;
identifier ::= ? ASCII-letter, gevolgd door ASCII-letters, cijfers of '-' ? ;
integer ::= ? één of meer cijfers ? ;
boolean ::= "true" | "false" ;
```

### YAML frontmatter in `.vsa`-bestanden

Zelfstandige `.vsa`-bestanden (buiten een Hugo Markdown-blok) kunnen dezelfde
[metadata](@) bevatten via een optionele YAML-kop aan het begin van het bestand,
afgebakend door `---`. Dit maakt het mogelijk om `.vsa`-bestanden als
zelfbeschrijvende eenheden te exporteren zonder de rest van een repository.

```yaml
---
muziek:
  do: F4
  mode: major
  tempo: 132
identificatie:
  title: Tropaar van de zondag, toon 1
  composer: Traditioneel
  language: nl
---
[:] Ter{/&/wijl_&_} {\\de} steen ...
```

De `muziek`-sectie bevat dezelfde parameters als de [bloksyntax](#hugo-markdown-bloksyntax). De
`identificatie`-sectie bevat bibliografische [metadata](@) die wordt opgenomen in
het MusicXML `<identification>`-blok (zie [MusicXML-export](rendering.md#musicxml-export)). De optionele `typografie`-
sectie bevat lettertype-instellingen voor export-renderers (zie [Typografie](rendering.md#typografie)).

Toekomstige secties (bijv. `liturgie`, `publicatie`) kunnen worden toegevoegd
zonder de bestaande syntaxis te breken.

| Sectie          | Veld               | Betekenis                                                                                                                  |
| --------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `muziek`        | `do`               | grondtoon, bijv. `F4`                                                                                                      |
| `muziek`        | `mode`             | modus: `major` of `minor`                                                                                                  |
| `muziek`        | `tempo`            | tempo in BPM                                                                                                               |
| `muziek`        | `meter`            | maatsoort, bijv. `4/4` (optioneel)                                                                                         |
| `muziek`        | `reciting-mode`    | ongescopte tekst in MusicXML: `quarters` (default) of `whole`                                                              |
| `muziek`        | `musicxml-profile` | exportprofiel: `playback` (default) of `engraving` (zie [MusicXML-exportprofielen](rendering.md#musicxml-exportprofielen)) |
| `muziek`        | `part-name`        | partijnaam in MusicXML; default `Vocal`                                                                                    |
| `muziek`        | `midi-sound`       | General MIDI-instrument (playback); default `keyboard.piano.grand`                                                         |
| `muziek`        | `midi-channel`     | MIDI-kanaal 1–16; default `1`                                                                                              |
| `muziek`        | `midi-program`     | MIDI-programmanummer; default `1`                                                                                          |
| `muziek`        | `midi-volume`      | MIDI-volume 0–100 (playback); default `78.7402`                                                                            |
| `muziek`        | `midi-pan`         | MIDI-panning −100…100; default `0`                                                                                         |
| `identificatie` | `title`            | titel van het [zangstuk](@bron)                                                                                            |
| `identificatie` | `subtitle`         | ondertitel                                                                                                                 |
| `identificatie` | `composer`         | componist of bewerker                                                                                                      |
| `identificatie` | `lyricist`         | tekstdichter                                                                                                               |
| `identificatie` | `rights`           | auteursrechtinformatie                                                                                                     |
| `identificatie` | `language`         | taalcode, bijv. `nl`                                                                                                       |
| `identificatie` | `tone`             | liturgische toon, bijv. `1`                                                                                                |
| `typografie`    | `lyric-font`       | lettertype voor lyrics; default `Source Sans 3`                                                                            |
| `typografie`    | `lyric-size`       | lettergrootte lyrics in punten; default `13`                                                                               |
| `typografie`    | `music-font`       | lettertype voor notenkoppen (`<music-font>`, optioneel)                                                                    |
| `typografie`    | `music-size`       | lettergrootte noten in punten (optioneel)                                                                                  |
| `typografie`    | `word-font`        | lettertype voor tempo/titel; default `Source Sans 3`                                                                       |
| `typografie`    | `word-size`        | lettergrootte woordtekst in punten; default `12`                                                                           |

De `typografie`-velden zijn optioneel; ontbrekende waarden vallen terug op de
defaults hierboven (ook zonder YAML-frontmatter, via blokmetadata-defaults).
Renderers die een veld niet ondersteunen negeren het. Overschrijven kan in
frontmatter of Hugo-blokmetadata, bijv. `typografie.lyric-size="14"`.

Bestanden zonder `---`-kop worden behandeld als gewone [VSA-tekst](@) zonder
[metadata](@).

### Algemene regels

Een VSA-zangstuk is gewone Unicode-tekst waarin sommige tekstfragmenten worden voorzien van VSA-markering. In een [zangstuk](@bron) kunnen [zangelement-scopes](@) voorkomen. Die zijn van de vorm:

```text
{<hoogte-modifier><zangelement><lengte-modifier>}
```

Daarbij geldt:

- een [scope](@) begint met `{` en eindigt met `}`;
- binnen een [scope](@) mag geen whitespace voorkomen;
- het [zangelement](@) (gezongen tekstframgment) is verplicht;
- de [hoogte-modifier](@) is optioneel;
- de [lengte-modifier](@) is optioneel;
- tekens die als modifierteken worden gebruikt, mogen niet in het [zangelement](@) voorkomen;
- leestekens zoals komma’s, dubbele punten en uitroeptekens horen buiten [scopes](@) te staan.

Voorbeeld:

```text
{/Hei_}{\&/li}{/ge}
```

Tekst buiten [scopes](@) blijft gewone tekst en wordt ongewijzigd weergegeven, behalve dat `{` en `}` daar niet als gewone tekens gebruikt mogen worden.

In ongescopte tekst mag `-` lettergrepen scheiden (bijv. `mel-se`). De
SVG-renderer toont dit als gewone tekst; bij MusicXML-export wordt elk deel een
eigen reciteernoot (zie [Ongescopte tekst (reciteertoon)](rendering.md#ongescopte-tekst-reciteertoon)).

### Enkelvoudige Hoogte-Modifiers (EHMs)

Een [EHM](@) beschrijft één relatieve toonhoogtebeweging of een lege grafische positie. Een [EHM](@) is ofwel een enkelvoudige basisbeweging, ofwel een halftoon-prefix gevolgd door een basisbeweging.

#### Basisbewegingen

| [EHM](@) | Voorbeeld      | Betekenis                 | Visuele rendering ([glyph](@))         |
| -------- | -------------- | ------------------------- | -------------------------------------- |
| `/`      | `{/tekst}`     | één ladderstap omhoog     | één schuine streep omhoog              |
| `//`     | `{//tekst}`    | twee ladderstappen omhoog | twee gestapelde schuine strepen omhoog |
| `///`    | `{///tekst}`   | drie ladderstappen omhoog | drie gestapelde schuine strepen omhoog |
| `////`   | `{////tekst}`  | vier ladderstappen omhoog | vier gestapelde schuine strepen omhoog |
| `/////`  | `{/////tekst}` | vijf ladderstappen omhoog | vijf gestapelde schuine strepen omhoog |
| `-`      | `{-tekst}`     | zelfde toonhoogte         | horizontaal streepje                   |
| `\`      | `{\tekst}`     | één ladderstap omlaag     | één schuine streep omlaag              |
| `\\`     | `{\\tekst}`    | twee ladderstappen omlaag | twee gestapelde schuine strepen omlaag |
| `\\\`    | `{\\\tekst}`   | drie ladderstappen omlaag | drie gestapelde schuine strepen omlaag |
| `\\\\`   | `{\\\\tekst}`  | vier ladderstappen omlaag | vier gestapelde schuine strepen omlaag |
| `\\\\\`  | `{\\\\\tekst}` | vijf ladderstappen omlaag | vijf gestapelde schuine strepen omlaag |
| `~`      | `{~tekst}`     | zelfde toonhoogte         | geen zichtbare [glyph](@)              |

#### Halftoon-prefix

Een halftoon-prefix is een **accidens** op de aankomsttoon van de
basisbeweging: kruis (`#`) of mol (`b`). De prefix staat altijd
onmiddellijk vóór een basisbeweging; een standalone prefix is niet geldig.

De prefix wijzigt **niet** de diatonische cursor. Alleen de basisbeweging
(`/`, `\`, `-`, `~`, …) verplaatst de laddergraad. Zelfde-toon (`~`/`-` of
ongescopte tekst) houdt de vorige **klinkende** toon vast (inclusief
accidens). Een latere ladderstap start vanaf de natuurlijke graad tenzij
opnieuw een prefix. Zie
[Interpretatie van EHMs](semantics.md#interpretatie-van-ehms).

`+` en `♯` zijn spelling/aliassen van `#` (zelfde semantiek). `♭` is een
alias van `b`.

| Prefix | Alias(es) | Semantiek                         | Visuele rendering           |
| ------ | --------- | --------------------------------- | --------------------------- |
| `#`    | `+`, `♯`  | kruis/accidens op aankomsttoon    | `+` links van de basisglyph |
| `b`    | `♭`       | mol/accidens op aankomsttoon      | `♭` links van de basisglyph |

Voorbeelden van gecombineerde [EHMs](@):

| [EHM](@) | Cursor (basis) | Accidens     | Voorbeeld    |
| -------- | -------------- | ------------ | ------------ |
| `#/`     | +1 trede       | kruis        | `{#/tekst}`  |
| `b/`     | +1 trede       | mol          | `{b/tekst}`  |
| `#\`     | −1 trede       | kruis        | `{#\tekst}`  |
| `b\`     | −1 trede       | mol          | `{b\tekst}`  |
| `#-`     | 0 (unisono)    | kruis        | `{#-tekst}`  |
| `b-`     | 0 (unisono)    | mol          | `{b-tekst}`  |
| `#//`    | +2 treden      | kruis        | `{#//tekst}` |
| `b\\`    | −2 treden      | mol          | `{b\\tekst}` |

Alle combinaties van een halftoon-prefix met een basisbeweging zijn
syntactisch geldig. De semantische geldigheid hangt af van de
[do-context](@) en modus (zie
[Geldigheid van halftoon-prefix combinaties](semantics.md#geldigheid-van-halftoon-prefix-combinaties)).

### Enkelvoudige Lengte-Modifiers (ELMs)

Een [ELM](@) beschrijft de duur van één [muzikale positie](@) ten opzichte van de standaardduur.

| [ELM](@) | Voorbeeld   | Duur                | Visuele [glyph](@)                                          |
| -------- | ----------- | ------------------- | ----------------------------------------------------------- |
| `_`      | `{tekst_}`  | 2 × standaardduur   | één horizontale lijn onder het [zangelement](@)             |
| `_.`     | `{tekst_.}` | 3 × standaardduur   | volle lijn boven, halve lijn (linkerhelft) direct daaronder |
| `__`     | `{tekst__}` | 4 × standaardduur   | twee gestapelde horizontale lijnen                          |
| `.`      | `{tekst.}`  | 1/2 × standaardduur | één punt onder het [zangelement](@)                         |
| `..`     | `{tekst..}` | 1/4 × standaardduur | twee gestapelde punten                                      |
| `-`      | `{tekst-}`  | standaardduur       | implementatie-afhankelijke standaardduur-glyph              |
| `~`      | `{tekst~}`  | standaardduur       | geen zichtbare [glyph](@)                                   |
| `-.`     | `{tekst-.}` | 1½ × standaardduur  | halve lijn (linkerhelft) onder het [zangelement](@)          |
| `~.`     | `{tekst~.}` | 1½ × standaardduur  | zelfde glyph als `-.`                                      |

### Samengestelde modifiers

Een samengestelde [modifier](@) bestaat uit twee of meer [EHMs](@) of twee of meer [ELMs](@), gescheiden door `&`.

Voorbeelden:

```text
{/&\tekst}
{tekst_&_}
{/&\&/tekst_&~&~}
```

Elke enkelvoudige [modifier](@) binnen een samengestelde [modifier](@) representeert precies één [muzikale positie](@).

### Toonhoogte-markering

Een [toonhoogte-markering](@) heeft de vorm:

```text
[<EHM>:]
```
Voorbeelden:

```text
[:]
[//:]
```

Elke [toonhoogte-markering](@) geeft een toonhoogte aan ten opzichte van de basistoon
van de [do-context](@).

Voor de eerste [toonhoogte-markering](@) wordt de [do-context](@) extern gespecificeerd: 
- in de praktijk van het zingen door de koorlei(st)er.
- binnen de context van conversies, bijvoorbeeld naar MusicXML, wordt dat gespecificeerd 
door de feitelijke conversie - dat is buiten de scope van de pure [VSA](@).

Elke volgende [toonhoogte-markering](@) geeft aan dat de zang op die positie op die hoogte moet zitten.
Dat betekent
- in de praktijk dat zangers een check hebben of ze daar op de goede hoogte zitten;
- in de context van conversies, bijvoorbeeld naar MusicXML, dat het mogelijk is om een controle uit te voeren op de toonhoogte van het converteerde materiaal.

Het is een gangbare praktijk om zowel voor als na een [zangstuk](@bron) een [toonhoogte-markering](@) te schrijven.
Indien twee [zangstukken](@bron) elkaar opvolgen, kan dat dus ook (vanuit [VSA](@) perspectief) gezien worden
als een enkel [zangstuk](@bron) met tussenliggende [toonhoogte-markeringen](@).

De tekst `:]` is de syntactische afsluiter van een [toonhoogte-markering](@). Hij wordt visueel gerenderd als een horizontale lijn rond het verticale midden van de tekstregel, met daarboven de rendering van de [EHM](@).

### Absolute toonhoogte binnen Hugo blokmetadata

Een absolute toonhoogte bestaat uit:

```text
<toonnaam><optionele alteratie><octaaf>
```

Voorbeelden:

```text
C4
F#3
E♭5
Bb2
```

Ondersteunde toonnamen:

```text
A B C D E F G
```

Ondersteunde alteraties:

```text
#  ♯  b  ♭
```

Ondersteunde octaven:

```text
0 1 2 3 4 5 6 7 8
```

### EBNF

De [VSA](@) grammatica wordt beschreven in ISO-14977 EBNF, aangevuld met informele karakterklassen tussen `? ... ?`.

Betekenis van gebruikte EBNF-notatie:

| Schrijfwijze | Betekenis                   |
| ------------ | --------------------------- |
| `(* ... *)`  | commentaar                  |
| `[ ... ]`    | optioneel, nul of één keer  |
| `{ ... }`    | herhaling, nul of meer keer |
| `( ... )`    | groepering                  |
| `? ... ?`    | informele karakterklasse    |

Let op: in EBNF wordt `\` als escape-teken gebruikt. Om het teken `\` zelf te noteren, wordt het in EBNF verdubbeld.

```ebnf

zangstuk ::=
    { whitespace }
    { toonhoogte-markering | non-scopechar | scope }
    { whitespace } ;

toonhoogte-markering ::=
    "["
    [ EHM ]
    ":]" ;

non-scopechar ::=
    ? elk Unicode-karakter behalve "{" en "}" ? ;

scope ::=
    "{"
    [ hoogte-modifier ]
    zangelement
    [ lengte-modifier ]
    "}" ;

hoogte-modifier ::= EHM { "&" EHM } ;
lengte-modifier ::= ELM { "&" ELM } ;

EHM ::= base-EHM | halftoon-prefix base-EHM ;

halftoon-prefix ::= "#" | "♯" | "+" | "b" | "♭" ;

base-EHM ::=
      "~"
    | "-"
    | "/"
    | "//"
    | "///"
    | "////"
    | "/////"
    | "\\"
    | "\\\\"
    | "\\\\\\"
    | "\\\\\\\\"
    | "\\\\\\\\\\" ;

ELM ::=
      "~"
    | "-"
    | "-."
    | "~."
    | "_"
    | "_."
    | "__"
    | "."
    | ".." ;

zangelement ::=
    zangelement-char
    { zangelement-char } ;

zangelement-char ::=
    ? elk Unicode-karakter behalve
      whitespace,
      "{", "}",
      "&", "~", "+", "-", "\\", "/", "_", "." ? ;
```

Deze grammatica valideert uitsluitend de VSA-inhoud binnen het codeblok. De [blokmetadata](@) wordt apart geparseerd volgens de [EBNF voor Hugo Markdown bloksyntax](#ebnf-voor-hugo-markdown-bloksyntax). Semantische regels worden na het parsen gecontroleerd.

---
