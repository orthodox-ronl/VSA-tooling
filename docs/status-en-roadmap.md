# Status en roadmap

Dit document is het actuele kompas voor VSA-tooling. Historische stapdocumenten blijven in `docs/architecture/`, maar dit bestand vat samen wat nu werkt, wat beperkt werkt en wat de nuttigste volgende stappen zijn.

## Korte samenvatting

VSA-tooling is in de fase van werkende engine naar bruikbaar authoring- en publicatiegereedschap.

De parser, validator, SVG-renderer, MusicXML-export en Hugo-buildketen zijn aanwezig. De belangrijkste resterende waarde zit in workflow-afwerking: duidelijker documenteren, document-directives beslissen, randgevallen expliciet specificeren en de parochie-/bronpublicatie gladder maken.

## Werkt nu

| Onderdeel                   | Status                | Opmerking                                                                                                                                                    |
| --------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| VSA parser                  | Werkend               | Ondersteunt tekst, scopes, modifiers en hoogte-markeringen.                                                                                                  |
| Syntaxvalidatie             | Werkend               | Meldt meerdere fouten waar mogelijk.                                                                                                                         |
| Semantische validatie       | Werkend               | Onder andere modifier-aantallen en hoogte-marker-controles; het bekende voorbeeld met een foute laatste marker wordt gedetecteerd.                           |
| Meerdere hoogte-markeringen | Werkend               | Parser, validator en SVG-rendering ondersteunen dit.                                                                                                         |
| SVG-rendering               | Werkend               | Inclusief multiline/wrapping, spacingbeleid en regressietests.                                                                                               |
| MusicXML/MXL-export         | Werkend               | Beschikbaar via `vsa musicxml`; profielen voor playback/engraving.                                                                                           |
| Audio-export (preview)      | Werkend               | `vsa audio` / `mvsa audio` → ``.mp3`` via MuseScore; site-knop is consumer.                                                                                  |
| Markdown VSA-blokken        | Werkend               | `::: vsa-notatie` wordt gevonden, gevalideerd en verwerkt.                                                                                                   |
| Hugo build-markdown         | Werkend               | Genereert Markdown en SVG-assets voor Hugo.                                                                                                                  |
| `:::include`                | Werkend               | Ondersteunt markdown, VSA, assets en exporttypes `svg`, `coria`, `mxl`.                                                                                      |
| `:::coria`                  | Werkend               | Blijft ondersteund als build-time directive/alias.                                                                                                           |
| Print/web directives        | Werkend met beperking | `web-only`, `print-only`, `keep-together`; nesting is nog niet toegestaan.                                                                                   |
| Parochie-lokaal model       | Werkend in demo       | `lokaal/`, manifeststructuur en voorbeeldincludes zijn aanwezig.                                                                                             |
| Catalogus-resolutie         | Werkend               | `vsa resolve-catalogus` zet `zoek=` om naar `bron:` of `lokaal:`.                                                                                            |
| Hugo-demo                   | Werkend als testbed   | Combineert praktijkmateriaal, documentatie, layouts en publicatieketen.                                                                                      |
| mvsa (draft)                | Werkend conversies    | `mvsa`/`vsa mvsa`: validate, normalize, musicxml, mscz, pdf, audio, import; backlog: [specification-mvsa/open-points.md](specification-mvsa/open-points.md). |

## Beperkt of kwetsbaar

| Onderdeel             | Status                | Waarom dit aandacht vraagt                                                                              |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------- |
| README/projectingang  | Verbeterd, maar jong  | De README is nu herschreven; hij moet actueel blijven bij workflow-keuzes.                              |
| Roadmap               | Nieuw gecentraliseerd | Dit document vervangt nog niet automatisch alle oude todo's.                                            |
| Directive-nesting     | Open besluit          | `web-only` binnen `keep-together` faalt nu bewust; praktijkmateriaal wil dit soms wel.                  |
| Commentaar in VSA     | Deels opgelost        | HTML-commentaar en comment-only regels zijn aangepakt, maar een compleet commentaarmodel is nog nuttig. |
| VSA-blok-afbakening   | Authoring-usability   | Vergeten `::: vsa-notatie` of afsluitende `:::` moet vroeg en duidelijk worden gemeld.                  |
| `bron:` met Coria/MXL | Beperkt               | SVG op `bron:` werkt; Coria/MXL buiten `content-root` is nog niet glad.                                 |
| AST/source maps       | Later                 | Nodig voor betere foutposities, editor-integratie en eventueel roundtrip tooling.                       |
| Editor-ondersteuning  | Niet aanwezig         | VS Code highlighting en foutmarkering zouden dagelijks gebruik veel prettiger maken.                    |

## Open ontwerpbesluiten

### 1. Geneste document-directives

Nu is nesting verboden. Dat voorkomt ambiguiteit, maar botst met natuurlijke authoring, bijvoorbeeld een Coria-link of `web-only` content binnen een `keep-together` blok.

Feitelijk vraagt dit om goed na te denken over `exports` en waarvoor ze dienen. Daarbij moet niet zozeer gekeken worden naar formaten (web, pdf, print, ...), maar eerst naar het soort gebruik dat wordt voorzien, en op basis daarvan kijken welke formaten daarbij nodig zijn, en wat daar dan in gaat moeten. 

Het kan dus zomaar zijn dat document-directives helemaal op de schop moeten en daar is nesting dan een onderdeel van.

### 2. Commentaarmodel

Gebruikers moeten foutieve of experimentele VSA kunnen bespreken zonder dat validatie stukloopt op voorbeeldtekst.

Te beslissen:

- Welke regelcommentaar-syntax hoort bij VSA?
- Is blokcommentaar nodig?
- Wordt commentaar bewaard in AST/source maps of volledig genegeerd?
- Hoe gedragen comments zich binnen Markdown VSA-blokken?

### 3. Control tokens

Tokens zoals `[/]`, `[*]`, `[/?]` en `[*?]` zijn gespecificeerd als toekomstige syntax voor frasegrenzen en adempauzes, maar nog niet ondersteund als volwaardige renderer-directives.

Te beslissen:

- Welke abstracte betekenissen zijn definitief?
- Wat doen SVG en MusicXML per token?
- Welke configuratie is nodig per renderer?
- Hoe blijven bestaande hoogte-markeringen eenduidig gescheiden van control tokens?

### 4. Parochie-/bronworkflow

De richting is duidelijk: sjabloon of sessie met `zoek=`, resolver, validatie, build-markdown, Hugo, print/web-output. De praktische workflow kan nog eenvoudiger.

Te beslissen:

- Wanneer gebeurt `resolve-catalogus`: apart commando, automatisch, of beide?
- Waar komt resolved output te staan?
- Hoe gaan we om met ambiguiteit: strict fout, lijst, of interactieve keuze?
- Hoe worden `bron:` assets voor Coria/MXL beschikbaar gemaakt?

## Nuttigste volgende stappen

### Stap 1: nadenken over het gebruik van exports

Doel: het specificeren van de soorten van gebruik die we willen ondersteunen, en op basis daarvan beslissen

- welke soorten `exports` daarbij nodig zijn,
- welke bestandsformaten of presentaties (web, papier, ...) daarvoor ondersteund gaan worden
- hoe deze moeten worden samengesteld, en welke directives of andere syntax daarbij nodig is.

Uitgangspunt voor dragers: [gebruikseisen-dragers.md](plans/gebruikseisen-dragers.md);
implementatie-/exportplan: [uitgaveprofielen.md](plans/uitgaveprofielen.md).

Ook is een onderdeel om bestaande directives te reviewen om vast te stellen of ze behouden, gewijzigd of verwijderd moeten worden.

Waarom: deze keuze bepaalt hoe auteurs echte liturgische documenten schrijven.

Resultaat:

- Een korte exportspecificatie: gebruiksdoelen, exporttypes en beoogde outputvormen.
- Een besluit over de rol van bestaande directives (`web-only`, `print-only`, `keep-together`, `include`, `coria`).
- Update van `docs/specification/directives.md` (en gerelateerde guides).
- Pas daarna tests en eventuele implementatie-aanpassingen.

### Stap 2: parochie-workflow glad maken

Doel: van sjabloon/sessie naar preview/print zonder handmatige tussenstappen die makkelijk fout gaan.

Waarom: hier zit de meeste praktische waarde voor dagelijks gebruik.

Resultaat:

- Heldere voorbeeldworkflow in docs.
- Betere checks op open `zoek=`.
- Duidelijke outputlocatie voor resolved bestanden.
- Indien nodig: helper-script voor resolve + validate + build.

### Stap 3: commentaarmodel afronden

Doel: veilige commentaarvormen voor uitleg, voorbeeldfouten en tijdelijke notities in VSA-bronnen.

Waarom: auteurs moeten kunnen documenteren zonder validatie te saboteren.

Resultaat:

- Specificatie in `docs/spec/vsa-comments.md`.
- Validator/parser-regels.
- Regressietests voor comments met anders ongeldige VSA.

### Stap 4: hoogte-marker randgevallen expliciet specificeren

Doel: vastleggen dat de eerste hoogte-marker de beginhoogte is en dat een blok met maar een marker geen eindcontrole heeft.

Waarom: de validator werkt voor meerdere markers, maar de randgevallen moeten in de specificatie even helder zijn als in de code.

Resultaat:

- Specificatie of gebruikersdocumentatie bijwerken.
- Regressietest toevoegen of aanwijzen voor het bekende voorbeeld met een foute laatste marker.
- Eventueel `docs/to-do-van-mij.md` verder opschonen zodra het persoonlijke todo-bestand wordt geconsolideerd.

### Stap 5: authoring-fouten rond VSA-blokken expliciet maken

Doel: vergeten `::: vsa-notatie` of afsluitende `:::` in Markdown vroeg herkennen en met een duidelijke melding teruggeven.

Waarom: dit zijn typische schrijffouten bij auteurs; zonder gerichte diagnose lijkt de build of parser dan onverklaarbaar stuk te lopen.

Resultaat:

- Specificeren hoe Markdown met ontbrekende VSA-openings- of sluitingsdirective wordt herkend.
- Duidelijke foutmelding met bestand, regel en herstelhint.
- Regressietests voor ontbrekende opening en ontbrekende afsluiting.

### Stap 6: editor-ondersteuning voorbereiden

Doel: syntax highlighting en later foutmarkering voor VSA in VS Code.

Waarom: dit verlaagt de invoerdrempel sterk.

Resultaat:

- TextMate grammar of VS Code extension-skelet.
- Highlighting voor scopes, hoogte-markeringen, modifiers, comments en directives.
- Eventueel later: CLI diagnostics naar editor diagnostics.

## Later

| Onderwerp                               | Waarom later                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------ |
| AST-formalisering met spans/source maps | Belangrijk, maar pas echt nodig voor editor tooling en complexere refactors.         |
| Roundtrip parsing                       | Waardevol voor automatische transformaties, niet nodig voor huidige publicatieketen. |
| AI-versnelde invoer met ` | `-scheidingen | Interessant, maar afhankelijk van stabiele notatie- en validatieregels. |
| SATB/beginakkoord-rendering           | Muzikaal nuttig, maar vraagt eerst een duidelijk model en renderersemantiek. |
| Volledige TEv2-conceptuele integratie | Eerst demo-ervaring opdoen en bepalen welke terminologie echt helpt.         |

## Relatie tot oude todo's

- `docs/todo.md` blijft de geconsolideerde historische todo-lijst.
- `docs/to-do-van-mij.md` blijft persoonlijke input en ruwe signalen bevatten.
- `docs/architecture/` blijft de implementatiegeschiedenis bewaren.
- Dit document is leidend voor actuele prioriteit en projectstatus.

Als een oud todo-punt opnieuw actief wordt, hoort het hier in een van deze categorieen terecht te komen: `werkt nu`, `beperkt`, `open besluit`, `nuttigste volgende stappen` of `later`.

