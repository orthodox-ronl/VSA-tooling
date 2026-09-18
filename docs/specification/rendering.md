# Rendering en export

Dit document consolideert het rendering- en exportcontract voor [VSA](@).

Het omvat de algemene renderingregels uit de hoofdspecificatie en de latere SVG-, glyph-, layout- en configuratiespecificaties.
Onder renderen verstaan we het omzetten van gevalideerde [VSA-notatie](@bron) naar een ander weergave- of uitwisselingsformaat.

Deze specificatie behandelt twee doelen:

1. **SVG**: visuele weergave van tekst met VSA-glyphs boven en onder de tekst.
2. **MusicXML**: symbolische muziekrepresentatie met melodie, ritme en tekstkoppeling.

### SVG-rendering

#### Algemeen model

Een [zangstuk](@bron) wordt visueel in zijn geheel gerenderd naar SVG.

De invoer wordt behandeld als Unicode NFC. Dit maakt gebruik mogelijk voor teksten in onder meer Nederlands, Duits, Engels, Russisch, Grieks en Roemeens.

Een [zangelement-scope](@) wordt gerenderd op een grid met `N` kolommen en drie rijen:

| Rij           | Inhoud           |
| ------------- | ---------------- |
| Bovenste rij  | EHM-glyphs       |
| Middelste rij | [zangelement](@) |
| Onderste rij  | ELM-glyphs       |

Elke kolom representeert één [muzikale positie](@).

Implementaties mogen daarnaast een lineair overlaymodel gebruiken waarbij tekst links wordt uitgelijnd en [muzikale posities](@) progressief naar rechts worden geplaatst, overeenkomstig historische Liturgikon-praktijken.

#### Aantal kolommen

Het aantal [muzikale posities](@) van een [modifier](@) is gelijk aan het aantal enkelvoudige [modifiers](@) waaruit deze bestaat.

Regels:

- als hoogte- en [lengte-modifier](@) beide aanwezig zijn, moeten zij evenveel posities bevatten;
- als slechts één [modifier](@) aanwezig is, bepaalt die [modifier](@) `N`;
- de ontbrekende [modifier](@) wordt aangevuld met `~`;
- als beide [modifiers](@) ontbreken, is `N = 1`.

#### Toonhoogte-markering

Een [toonhoogte-markering](@) van de vorm:

```text
[<hoogte-modifier>:]
```

wordt gerenderd als een horizontale streep rond het verticale midden van de tekstregel, met daarboven de rendering van de opgegeven [hoogte-modifier](@). Als geen [hoogte-modifier](@) aanwezig is, wordt alleen de horizontale streep weergegeven.

Absolute toonhoogten worden niet in [toonhoogte-markeringen](@) opgenomen en worden dus ook niet als onderdeel daarvan gerenderd.

#### Kolombreedtes en rijhoogtes

Voor elke kolom `i` wordt een minimale kolombreedte `W[i]` bepaald.

`W[i]` is de grootste van:

- de minimale breedte die nodig is om `EHM[i]` volledig te renderen;
- de minimale breedte die nodig is om `ELM[i]` volledig te renderen.

Laat `TB` de minimale tekstbreedte van het [zangelement](@) zijn.

De totale gridbreedte is:

```text
W = max(TB, Σ W[i])
```

Als `TB > Σ W[i]`, worden de kolommen proportioneel verbreed totdat de totale breedte gelijk is aan `TB`.

Als `TB < Σ W[i]`, behoudt het [zangelement](@) standaard zijn normale typografische breedte en wordt het gecentreerd in de middelste rij. Als daardoor storende witruimte ontstaat, wordt het [zangelement](@) links uitgelijnd en de resterende ruimte rechts opgevuld met een horizontale lijn overeenkomstig de Liturgikon-voorbeelden.

#### Render-eenheid

Alle glyph-afmetingen worden uitgedrukt in een basiseenheid `U`.

`U` is gelijk aan de hoogte van een EHM-streep.

| Eigenschap                                    | Waarde |
| --------------------------------------------- | ------ |
| lengte van schuine streep                     | `U`    |
| lijndikte                                     | `U/8`  |
| verticale afstand tussen gestapelde elementen | `U`    |
| diameter van een punt                         | `U/4`  |

#### Rendering van EHMs

Een schuine streep omhoog wordt gerenderd als een lijnsegment met:

| Eigenschap | Waarde |
| ---------- | ------ |
| hoek       | `+45°` |
| lengte     | `U`    |
| lijndikte  | `U/8`  |

Een schuine streep omlaag wordt gerenderd als een lijnsegment met:

| Eigenschap | Waarde |
| ---------- | ------ |
| hoek       | `-45°` |
| lengte     | `U`    |
| lijndikte  | `U/8`  |

Gestapelde strepen worden verticaal boven elkaar geplaatst. De verticale afstand tussen twee gestapelde strepen is gelijk aan `U`.

#### Rendering van ELMs

Een underscore (`_`) wordt gerenderd als een horizontale lijn.

De lijn:

- vult de volledige breedte van de kolom;
- wordt gecentreerd binnen de kolom;
- heeft dezelfde lijndikte als een EHM-streep.

Bij meerdere underscores worden de lijnen verticaal gestapeld.

Een punt (`.`) wordt gerenderd als een gevulde cirkel. De diameter van de cirkel bedraagt `U/4`.

Meerdere punten worden verticaal gestapeld.

`-.` en `~.` worden gerenderd als één horizontale lijn over de **linkerhelft** van de kolom (zelfde y als `_`, tot het kolommidden). Beide tokens hebben dezelfde glyph.

### MusicXML-export

> **Implementatiestatus:** geïmplementeerd in `vsa-tool` als [`vsa musicxml`](../reference/cli/musicxml.md).
> Zie `src/vsa/musicxml_renderer.py`, `src/vsa/pitch_resolver.py` en
> `src/vsa/duration_model.py`.

#### Doel

Export naar MusicXML is bedoeld als een lossless of near-lossless vertaling van de muzikale structuur van [VSA](@) naar een gestandaardiseerd muziekuitwisselingsformaat.

MusicXML representeert hierbij:

- melodie;
- ritme;
- tekstkoppeling per noot;
- melismatische tekstverdeling.

#### Uitgangspunten

MusicXML-export gebruikt dezelfde defaults als de Hugo [blokmetadata](@) in [Syntax](syntax.md#hugo-markdown-bloksyntax), tenzij het blok expliciet andere waarden opgeeft.

| Aspect                  | Default                |
| ----------------------- | ---------------------- |
| `do`                    | `F4`                   |
| `mode`                  | `major`                |
| `tempo`                 | `120 BPM`              |
| `duration-model`        | `default`              |
| `validate-ending`       | `true`                 |
| `reciting-mode`         | `quarters`             |
| `musicxml-profile`      | `playback`             |
| `part-name`             | `Vocal`                |
| `midi-sound`            | `keyboard.piano.grand` |
| `typografie.lyric-font` | `Source Sans 3`        |
| `typografie.lyric-size` | `13` pt                |
| `typografie.word-font`  | `Source Sans 3`        |
| `typografie.word-size`  | `12` pt                |

Maatsoort wordt niet uit [VSA](@) afgeleid. Als een MusicXML-export maatsoort nodig heeft, moet die als aanvullende blokparameter worden opgegeven, bijvoorbeeld `meter="4/4"`.

#### Absolute toonhoogtebepaling

De absolute toonhoogte voor MusicXML-export wordt bepaald vanuit de Hugo [blokmetadata](@), niet vanuit [toonhoogte-markeringen](@).

Voorbeeld:

```markdown
::: vsa-notatie
do="C4"
mode="major"
:::
```

De effectieve starttoonhoogte wordt bepaald door:

1. de `do`-parameter lezen;
2. de `mode`-parameter lezen;
3. eventuele beginmarkering toepassen als relatieve [hoogte-modifier](@);
4. het resultaat gebruiken als actuele toonhoogte voor de daaropvolgende [muzikale posities](@).

Als geen `do`-parameter aanwezig is, wordt de default `F4` gebruikt.

#### Toonhoogteberekening per noot

Elke [muzikale positie](@) correspondeert met één MusicXML `<note>`.

De absolute toonhoogte volgt twee lagen (zelfde model als
[Interpretatie van EHMs](semantics.md#interpretatie-van-ehms)):

1. **Diatonische cursor** — alleen basisbewegingen (`/`, `\`, `-`, `~`, …)
   verplaatsen de laddergraad t.o.v. `do` / modus (`-`/`~` = nul stappen).
2. **Klinkende toon** — halftoon-prefix zet MusicXML `<alter>` op díe noot;
   `~`/`-` zonder nieuwe prefix, en ongescopte recite, herhalen de vorige
   klinkende toon (inclusief alter). Een latere ladderstap gebruikt weer de
   natuurlijke graad tenzij die EHM zelf een prefix heeft.
3. **Zichtbaar voorteken** — als de klinkende alteratie afwijkt van de
   toonsoort of van een eerder voorteken op dezelfde nootletter in dezelfde
   maat, schrijft de exporter `<accidental>` (`sharp`, `flat`, of
   `natural` als herstelteken). Herhaalde zelfde alteratie in dezelfde maat
   krijgt geen tweede zichtbaar teken.

```text
cursor₀ = beginmarkering t.o.v. do
klank₀ = laddertoon(cursor₀)
voor elke EHMₙ:
    cursor ← cursor + ladderstappen(EHMₙ)
    als ladderstappen=0 en geen nieuwe prefix:
        pitchₙ ← klankₙ₋₁          # zelfde toon voor de zanger
    anders:
        pitchₙ ← laddertoon(cursor) + alter(prefix)
    klankₙ ← pitchₙ
```

Daarbij worden [EHMs](@) geïnterpreteerd binnen de [do-context](@) en modus.

#### Ritme en duur

Elke [ELM](@) binnen een [lengte-modifier](@) bepaalt de duur van een [muzikale positie](@). Als geen [lengte-modifier](@) aanwezig is, wordt `~` gebruikt.

Mapping naar MusicXML bij `duration-model="default"`:

| [ELM](@) | MusicXML-duur         |
| -------- | --------------------- |
| `~`      | kwartnoot             |
| `-`      | kwartnoot             |
| `-.`     | gepunteerde kwartnoot |
| `~.`     | gepunteerde kwartnoot |
| `_`      | halve noot            |
| `_.`     | gepunteerde halve noot |
| `__`     | hele noot             |
| `.`      | achtste noot          |
| `..`     | zestiende noot        |

Andere duration-modellen mogen hiervan afwijken. Als meerdere [ELMs](@) aanwezig zijn binnen één [zangelement-scope](@), krijgt elke [muzikale positie](@) haar eigen duurwaarde.

#### Melismatische mapping

Als een [zangelement](@) meerdere [muzikale posities](@) bevat, wordt dit in MusicXML weergegeven als één tekstfragment dat over meerdere noten wordt verdeeld.

Conceptueel:

```text
1 VSA-zangelement met N muzikale posities
→
N MusicXML note-elementen met gekoppelde lyric-informatie
```

De exacte MusicXML-encoding van `syllabic`, `extend` en lyric-herhaling hangt af
van het gekozen exportprofiel ([MusicXML-exportprofielen](#musicxml-exportprofielen)). In beide profielen geldt: één
tekstfragment op de eerste noot van het melisma; vervolgnoten dragen geen
aparte syllabe-tekst.

#### Ongescopte tekst (reciteertoon)

Tekst buiten [zangelement-scopes](@) heeft in [VSA](@) geen eigen toonhoogte of duur. Bij
MusicXML-export wordt zulk tekstmateriaal omgezet naar **reciteertoon**: noten
op de laatst bekende toonhoogte.

Parameter `reciting-mode` (in [blokmetadata](@) of YAML-frontmatter onder `muziek`):

| Waarde               | Gedrag                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `quarters` (default) | één kwartnoot per woord of lettergreep                                                                                                     |
| `whole`              | bij ≥4 opeenvolgende woorden één hele noot met alle woorden als lyric (psalm/reciteerstijl; kan in MuseScore tot verschoven lyrics leiden) |

**Lettergrepen met koppelteken**

In ongescopte tekst mag een `-` woorden in lettergrepen splitsen, bijvoorbeeld
`{//he}mel-se en {\aard}se`. Elk deel krijgt een eigen kwartnoot; de lyric
volgt de gangbare notatie (`mel-` + `se`, met MusicXML `syllabic`
`begin`/`end`). Dit geldt alleen voor `-` in platte tekst tussen [scopes](@), niet
binnen `{...}`-scopes (daar is `-` een [ELM](@)).

Leestekens (`,`, `.`, `:`, …) worden aan het voorafgaande woord of de
voorafgaande noot geplakt.

Barline-markeringen `*`, `/` en `//` in platte tekst sluiten de huidige maat
af.

#### Conversieregel per muzikale positie

Voor elke [muzikale positie](@) geldt:

| [VSA](@)                                      | MusicXML                   |
| --------------------------------------------- | -------------------------- |
| [muzikale positie](@)                         | één `<note>`               |
| [EHM](@)                                      | laddergraad-cursor + optioneel `<alter>` |
| [ELM](@)                                      | duration                   |
| [zangelement](@)                              | lyric                      |
| meerdere posities binnen één [zangelement](@) | melisma                    |

#### Foutafhandeling bij export

MusicXML-export moet worden geweigerd of als ongeldig gemarkeerd wanneer:

- EHM- en ELM-aantallen inconsistent zijn;
- een onbekende [modifier](@) voorkomt;
- geen geldige toonhoogte kan worden afgeleid;
- een chromatische alteratie (halftoon-prefix) die de implementatie of modus niet toestaat;
- de implementatie geen mappingstrategie heeft voor de gekozen modus.

In alle gevallen moet een foutmelding minimaal bevatten:

- wat er fout is;
- bestand, regelnummer en positie;
- een voorstel voor oplossing.

#### Typografie

De optionele `typografie`-sectie in YAML-frontmatter ([YAML frontmatter in `.vsa`-bestanden](syntax.md#yaml-frontmatter-in-vsa-bestanden)) of de equivalente
[blokparameters](@) worden bij MusicXML-export **alleen in het `engraving`-profiel**
([MusicXML-exportprofielen](#musicxml-exportprofielen)) vertaald naar `<defaults>`-elementen:

| Metadata                | MusicXML                       |
| ----------------------- | ------------------------------ |
| `typografie.lyric-font` | `<lyric-font font-family="…">` |
| `typografie.lyric-size` | `<lyric-font font-size="…">`   |
| `typografie.music-font` | `<music-font font-family="…">` |
| `typografie.music-size` | `<music-font font-size="…">`   |
| `typografie.word-font`  | `<word-font font-family="…">`  |
| `typografie.word-size`  | `<word-font font-size="…">`    |

Grootte-eenheden zijn **punten** (pt), conform MusicXML.

Standaard typografie ([YAML frontmatter](syntax.md#yaml-frontmatter-in-vsa-bestanden)):

| Veld                    | Default         |
| ----------------------- | --------------- |
| `typografie.lyric-font` | `Source Sans 3` |
| `typografie.lyric-size` | `13`            |
| `typografie.word-font`  | `Source Sans 3` |
| `typografie.word-size`  | `12`            |

Notenkoppen (`music-font`, `music-size`) hebben geen VSA-default; de
doelrenderer (bijv. MuseScore) gebruikt zijn eigen notatiefont.

> **Beperking:** programma's als MuseScore importeren font-hints uit MusicXML
> in hun stijlsysteem. De uiteindelijke weergave kan door de gebruiker of door
> partituuropmaak-instellingen worden overschreven. In het `playback`-profiel
> worden typografie-hints niet geëmitteerd (conform MuseScore-roundtrip).

#### MusicXML-exportprofielen

MusicXML kan op verschillende manieren worden geëncodeerd terwijl dezelfde
muzikale inhoud behouden blijft. `vsa-tool` ondersteunt twee profielen,
selecteerbaar via `musicxml-profile` in [blokmetadata](@), YAML-frontmatter
(`muziek.musicxml-profile`) of CLI (`--musicxml-profile`).

| Profiel     | Doel                                                                                                    | Default |
| ----------- | ------------------------------------------------------------------------------------------------------- | ------- |
| `playback`  | Afspelen in webviewers (bijv. [Coria](https://coria.nl)), MuseScore-import zonder handmatige opschoning | **ja**  |
| `engraving` | Partituurbewerking met expliciete maatstrepen, typografie-hints en gedetailleerde melisma-extend        | nee     |

##### Gemeenschappelijk gedrag

Ongeacht profiel geldt pitch-resolutie, [ELM](@)→duur, reciteertoon,
syllabische splitsing met `-`, slur over melisma, barlines op `*`, `/`, `//` en
formele [control tokens](@), en conditionele tempo-markering (alleen bij expliciet
`tempo` in [metadata](@)).

##### Profiel `playback`

Geoptimaliseerd voor compatibiliteit met MuseScore-roundtrip en Coria. Het
volgt structureel het patroon van door MuseScore opgeslagen MusicXML 4.0
partwise-bestanden.

| Aspect                 | Gedrag                                                                                                         |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| `<part-list>`          | `score-instrument`, `midi-device`, `midi-instrument` (General MIDI)                                            |
| `<defaults>`           | **niet** geëmitteerd                                                                                           |
| `<encoding><supports>` | `accidental`, `beam`, `stem` = yes; `print` new-page/new-system = no                                           |
| `<note>`               | `<voice>1</voice>`, `<stem>up</stem>` op elke noot                                                             |
| Beaming                | Automatisch voor opeenvolgende `eighth`- en `16th`-noten in één maat                                           |
| Melisma-lyrics         | Alleen op eerste noot: `<text>` + `<extend/>` (zonder `type`); midden- en eindnoten **geen** `<lyric>`         |
| Slur                   | `type="start"` met `orientation="over"` en `placement="above"`; `type="stop"` op laatste noot                  |
| Maatstrepen            | Alleen `light-light` (dubbele streep `//`) en `light-heavy` (slot); **geen** expliciete `regular` tussen maten |
| `xml:lang` op lyrics   | niet geëmitteerd                                                                                               |

MIDI-parameters ([blokmetadata](@) / `muziek`-sectie):

| Veld           | Default                | MusicXML-locatie     |
| -------------- | ---------------------- | -------------------- |
| `part-name`    | `Vocal`                | `<part-name>`        |
| `midi-sound`   | `keyboard.piano.grand` | `<instrument-sound>` |
| `midi-channel` | `1`                    | `<midi-channel>`     |
| `midi-program` | `1`                    | `<midi-program>`     |
| `midi-volume`  | `78.7402`              | `<volume>`           |
| `midi-pan`     | `0`                    | `<pan>`              |

> **Opmerking:** `keyboard.piano.grand` is de default omdat MuseScore-roundtrip
> en Coria daarmee zijn getest. Voor koorklank kan `voice.choir.aahs` worden
> ingesteld.

##### Profiel `engraving`

Geoptimaliseerd voor partituurweergave en handmatige nabewerking in MuseScore.

| Aspect                 | Gedrag                                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `<part-list>`          | Alleen `<part-name>` (geen MIDI)                                                                                         |
| `<defaults>`           | Pagina-/systeemlayout + typografie ([Typografie](#typografie))                                                           |
| `<encoding><supports>` | niet geëmitteerd                                                                                                         |
| `<note>`               | Geen `<voice>`, `<stem>` of `<beam>`                                                                                     |
| Melisma-lyrics         | Eerste noot: `<extend type="start">`; midden: `<extend type="continue">`; laatste: `<extend type="stop">` (zonder tekst) |
| Maatstrepen            | Expliciete `regular` op elke enkele streep; `light-light` en `light-heavy` waar van toepassing                           |
| `xml:lang`             | Op lyrics wanneer `identificatie.language` is gezet                                                                      |

##### Validatie

Automatische regressietests vergelijken nootstructuur (pitch, duur, lyric-tekst)
tegen [fixture-bestanden](@) die het **`engraving`-profiel** beschrijven. Coria-
compatibiliteit van het **`playback`-profiel** wordt structureel getest (MIDI,
voice/stem, beaming, melisma-encoding) maar vereist handmatige verificatie in
Coria of MuseScore voor volledige garantie.

##### Uitvoerformaat: `.mxl` (default) en `.musicxml`

[`vsa musicxml`](../reference/cli/musicxml.md) schrijft standaard **Compressed MusicXML** (`.mxl`). Met
`--format musicxml` of een uitvoerpad dat op `.musicxml` eindigt, wordt
ongekomprimeerde MusicXML geschreven.

| Bestand in ZIP (`.mxl`)  | Inhoud                                    |
| ------------------------ | ----------------------------------------- |
| `META-INF/container.xml` | Verwijzing naar `score.xml`               |
| `score.xml`              | Dezelfde partwise-XML als bij `.musicxml` |

Bij map-export is `.mxl` eveneens de default. Geen extra afhankelijkheden
(stdlib `zipfile`).

##### Coria-integratie (Hugo)

In **content-source** gebruik je de build-time directive:

```markdown
:::coria "tropaar-zondag-toon-3.vsa" label="Oefenen in Coria":::
:::include coria "corpus/T4-11-nicolaas-van-myra.mxl" label="Oefenen in Coria":::
```

Padregels zijn identiek aan `:::include`. Implementatie:
`src/vsa/markdown_coria.py`, `src/vsa/content_assets.py`.

[Coria](https://coria.nl) publicatiewijzen:

**1. Coria-export-HTML (aanbevolen voor koorleden)**

Sibling `{stem}.coria.html` naast de bron (`.vsa` of native MusicXML) in
content-source. Build kopieert naar `static/coria/…/{stem}.html`. Directive
emitteert `{{< coria-html >}}`.

**2. Deep-link naar MusicXML (`play_from_url`)**

Fallback wanneer geen `.coria.html` aanwezig is.

- Uit een vsa-bestand: afgeleide MXL onder `static/vsa/mxl/…` (apart
  gegenereerd via [`vsa musicxml`](../reference/cli/musicxml.md)).
- Native `.mxl` / `.musicxml`: het bronbestand zelf, gekopieerd naar
  `static/mxl/…` (andere URL-prefix, zodat beide naast elkaar kunnen).

Directive emitteert `{{< coria >}}`.

Site-build: `build-markdown` (directive + `.coria.html`-kopie) vóór
[`vsa musicxml`](../reference/cli/musicxml.md) (MXL-generatie). Lokaal (`baseURL /`) werkt `play_from_url`
niet: Coria haalt het bestand server-side op.

### Geïntegreerde partituur-export (HTML/PDF) — voorziene uitbreiding

> **Implementatiestatus:** nog niet geïmplementeerd.

Naast losse SVG-tekst ([SVG-rendering](#svg-rendering)) en MusicXML voor bewerking ([MusicXML-export](#musicxml-export)) is een
**geïntegreerde partituur-export** gepland: een [renderer](@) die [VSA](@) omzet naar
HTML en/of PDF waarin **notenbalk en lyrics tegelijk** voorkomen.

Doelgroep: **koorzangers** die niet alleen van de notenbalk kunnen zingen en
behoefte hebben aan de volledige VSA-visuele taal in de lyric-regel:

- [hoogte-modifiers](@) ([EHM](@)) boven tekst;
- [lengte-modifiers](@) ([ELM](@)) onder tekst;
- [toonhoogte-markeringen](@) (`[:]`, `[//:]`, …);
- configureerbare typografie via dezelfde `typografie`-frontmatter.

```text
.vsa + frontmatter
       ├── vsa musicxml   →  MusicXML / MuseScore (bewerken, afspelen)
       ├── vsa svg        →  tekst + VSA-glyphs (web, Hugo)
       └── vsa score      →  HTML/PDF: notenbalk + VSA-lyrics   [gepland]
```

Dit pad volgt de layoutlogica van de SVG-renderer waar mogelijk, aangevuld met
een notenbalkcomponent. [EHMs](@)/[ELMs](@) en [pitch-markers](@) horen **niet** in MusicXML
te worden gerepliceerd; daarvoor is deze export bedoeld.

Open ontwerpbesluiten (voor implementatie):

- keuze notatie-engine voor de balk (bijv. Verovio, LilyPond, eigen SVG);
- paginaformaat en regelafbreking (systeem-indeling);
- synchronisatie tussen reciteertoon-noten op de balk en VSA-glyphs in lyrics.

---




---

## Bron: `docs/spec/vsa-svg-rendering-spec.md`

# VSA SVG Rendering Specification (Draft 2)

## Doel en scope

Dit document beschrijft de SVG-rendering van [VSA-notatie](@bron).

De VSA-taalspecificatie (deze map) definieert:

* syntax;
* semantiek;
* validatie.

Dit document definieert uitsluitend:

* visuele presentatie;
* layout;
* typografie;
* glyph-rendering;
* rendering-configuratie.

De rendering-specificatie bepaalt niet de betekenis van VSA-constructies.

---

# Rendering-principes

## Algemene principes

SVG-rendering moet:

* goed leesbaar zijn;
* muzikaal scanbaar zijn;
* compact maar luchtig ogen;
* schaalbaar zijn naar verschillende schermgroottes;
* geschikt zijn voor zowel schermweergave als print.

## Layoutfilosofie

Default rendering gebruikt:

* links uitgelijnde regels;
* natuurlijke tekstspatiëring;
* compacte muzikale [glyphs](@);
* consistente verticale uitlijning.

Alle regeluitlijningen zijn toegestaan:

* links uitlijnen;
* rechts uitlijnen;
* centreren;
* uitvullen.

Links uitlijnen is de default.

---

# Glossary

| Term             | Betekenis                                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| Render-run       | Een visueel opeenvolgend rendering-element zoals vrije tekst, een [zangelement](@) of een [pitch-marker](@) |
| Zangelement      | Een `{...}` constructie met gezongen tekst en eventuele [modifiers](@)                                      |
| Glyph            | Een grafisch teken dat een muzikale eigenschap weergeeft                                                    |
| Bovenglyph       | Glyph boven de tekst                                                                                        |
| Onderglyph       | Glyph onder de tekst                                                                                        |
| Pitch-marker     | Constructie zoals `[:]`                                                                                     |
| Alignment-marker | Het `&`-teken dat [modifiers](@) visueel koppelt                                                            |
| Wrapping         | Het afbreken van regels                                                                                     |
| Layout-engine    | Het onderdeel dat bepaalt waar elementen worden geplaatst                                                   |
| Renderer         | Het onderdeel dat SVG genereert                                                                             |

---

# Layoutmodel

## Rendering-eenheden

Een VSA-regel wordt gerenderd als een reeks render-runs.

Voorbeelden van render-runs:

* vrije tekst;
* [zangelementen](@);
* [pitch-markers](@);
* whitespace.

## Regeluitlijning

De [renderer](@) ondersteunt:

* left;
* right;
* center;
* justify.

Default:

* left.

## Regelbreedte

De [renderer](@) gebruikt een maximale regelbreedte.

Wanneer een regel te breed wordt:

* wordt afgebroken op natuurlijke grenzen;
* blijven [zangelementen](@) zoveel mogelijk intact.

## Natuurlijke afbreekpunten

Default wrapping gebruikt:

1. expliciete regeleinden;
2. whitespace;
3. interpunctie;
4. grenzen tussen render-runs;
5. optionele interne zangelement-grenzen.

De [renderer](@) mag:

* geen [modifiers](@) scheiden van hun tekst;
* geen glyphgroepen splitsen.

## Woordverbindingen en wrapping

Een expliciete woordverbindingsmarkering verhindert automatische wrapping tussen gekoppelde render-runs.

Voorbeeld:

```text
[:] Heer, {\ont}-{/ferm} U [:]
```

Hier vormt:

```text
{\ont}-{/ferm}
```

één visuele woordgroep.

Automatische wrapping is daarom niet toegestaan:

* tussen `{\ont}` en `-`;
* tussen `-` en `{/ferm}`.

Wel toegestaan:

* na `Heer,`;
* vóór `{\ont}`;
* na `{/ferm}`.

## Expliciete wrapcontrole

Naast natuurlijke afbreekpunten kan de gebruiker wrapping expliciet beïnvloeden.

Wrapcontrole moet configureerbaar zijn. Dat betekent:

* de standaardtokens zijn door de [renderer](@) gedefinieerd;
* een project mag andere tokens configureren;
* configuratie moet vóór gebruik gevalideerd worden;
* ongeldige configuratie mag niet leiden tot parserfouten of ambigu gedrag.

De [renderer](@) moet wraptokens herkennen vóór reguliere VSA-parsing of via een aparte preprocessorlaag.

## Forced line break

Een forced line break dwingt een nieuwe renderregel af.

Standaard voorgestelde syntax:

```text
[/]
[*]
```

Voorbeeld:

```text
[:] Eerste regel [/] tweede regel [:]
```

Betekenis:

* render vóór `[/]`;
* start daarna een nieuwe SVG-regel;
* `[/]` zelf wordt niet zichtbaar gerenderd.

Alternatief:

```text
[:] Eerste regel [*] tweede regel [:]
```

`[/]` en `[*]` zijn beide forced line break markers.

Het verschil tussen beide markers kan later renderer- of exportafhankelijk worden gebruikt.

Voor MusicXML-rendering kan dit bijvoorbeeld relevant zijn:

* `[/]` = systeem-/regelbreuk;
* `[*]` = sterker structureel breekpunt;
* mapping naar maatstrepen of systeemindeling wordt later gespecificeerd.

## Preferred breakpoint

Een preferred breakpoint geeft aan waar de [renderer](@) bij voorkeur mag afbreken als wrapping nodig is.

Standaard voorgestelde syntax:

```text
[/?]
[*?]
```

Voorbeeld:

```text
[:] Dit is een lange zin [/?] met een voorkeurspunt [:]
```

Betekenis:

* [renderer](@) mag hier afbreken als dat nodig is;
* als afbreken niet nodig is, blijft `[/?]` onzichtbaar.

`[*?]` kan worden gebruikt als sterker preferred breakpoint dan `[/?]`.

Voorbeeld:

```text
[:] Eerste frase [/?] vervolg [*?] nieuw tekstdeel [:]
```

Mogelijke interpretatie:

* `[/?]` = gewoon voorkeursbreekpunt;
* `[*?]` = sterk voorkeursbreekpunt.

De exacte prioriteitsweging is renderer-configuratie.

## Waarom niet `[:]`

`[:]` wordt niet gebruikt als standaard wraptoken.

Reden:

* `[:]` is al een [pitch-marker](@);
* toekomstige [pitch-markers](@) kunnen mogelijk ook midden in een muziekstuk voorkomen;
* hergebruik van dezelfde tokenvorm voor wrapping zou parserambiguïteit veroorzaken.

Daarom gebruiken wraptokens expliciet herkenbare vormen zoals:

```text id="l0umsv"
[/]
[*]
[/?]
[*?]
```

Deze zijn:

* visueel onderscheidbaar;
* semantisch expliciet;
* uitbreidbaar voor toekomstige [renderers](@).

---

## Non-breaking group

Een non-breaking group voorkomt automatische wrapping binnen een groep.

Standaard voorgestelde syntax:

```text id="ux4x0q"
[= ... =]
```

Voorbeeld:

```text id="lixr7x"
[:] [= Heer, {\ont}-{/ferm} U =] [:]
```

Betekenis:

* de inhoud binnen `[= ... =]` blijft op één renderregel;
* als de groep te breed is, mag de [renderer](@) pas buiten de groep wrappen;
* de markers `[=` en `=]` worden niet zichtbaar gerenderd.

Non-breaking groups zijn bedoeld voor:

* korte vaste tekstgroepen;
* samengestelde woorden;
* woordgroepen die visueel bij elkaar moeten blijven;
* constructies met zichtbare woordverbindingen zoals `{\ont}-{/ferm}`.

---

## Zichtbare woordverbindingen

Een zichtbare woordverbindingsmarkering zoals `-` legt standaard een non-breaking relatie tussen omliggende render-runs.

Voorbeeld:

```text id="r3x4y4"
[:] Heer, {\ont}-{/ferm} U [:]
```

Hier vormt:

```text id="scy4w0"
{\ont}-{/ferm}
```

één visuele woordgroep.

Automatische wrapping is daarom niet toegestaan:

* tussen `{\ont}` en `-`;
* tussen `-` en `{/ferm}`.

Wel toegestaan:

* na `Heer,`;
* vóór `{\ont}`;
* na `{/ferm}`.

Als een gebruiker toch expliciet na een zichtbaar koppelteken wil afbreken, kan dat met een forced line break:

```text id="u9okbh"
[:] Heer, {\ont}-[/]{/ferm} U [:]
```

De forced line break marker wordt niet zichtbaar gerenderd.

---

## Configuratie van wraptokens

Wraptokens moeten configureerbaar zijn.

Voorbeeld:

```toml id="z0v6lg"
[rendering.svg.wrapping.tokens]
forced-line-break = ["[/]", "[*]"]
preferred-break = ["[/?]", "[*?]"]
nonbreaking-start = "[="
nonbreaking-end = "=]"
```

Configuratieregels:

* tokens mogen niet leeg zijn;
* tokens mogen elkaar niet ambigu overlappen;
* tokens mogen bestaande VSA-syntax niet breken;
* tokens moeten vóór gebruik gevalideerd worden;
* bij ongeldige configuratie stopt de [renderer](@) met een duidelijke configuratiefout.

---

## Geldige uitbreidbare tokenvormen

Uitbreidbare tokens moeten:

* syntactisch duidelijk herkenbaar zijn;
* niet conflicteren met bestaande VSA-constructies;
* parserambiguïteit vermijden;
* toekomstvast zijn.

Aanbevolen strategie:

* gebruik bracket-gebaseerde tokens;
* gebruik expliciete prefixsymbolen;
* reserveer bestaande VSA-tokenfamilies.

Goede voorbeelden:

```text id="x4kgv8"
[/]
[*]
[/?]
[*?]
[= ... =]
```

Minder geschikte voorbeelden:

```text id="6q2t4r"
[:]
[?]
[-]
```

omdat deze:

* lijken op bestaande of toekomstige [pitch-markers](@);
* semantisch onvoldoende onderscheidend zijn;
* ambigu kunnen worden bij uitbreiding van de taal.

---

## Vooruitblik: uitbreidbare layout- en exporttokens

Dezelfde uitbreidingsprincipes moeten later ook gelden voor:

* MusicXML-layouttokens;
* editor directives;
* exporthints;
* interactieve rendering;
* synchronisatie-aanwijzingen;
* multi-voice layout.

Voorbeelden van toekomstige toepassingen:

* systeemafbrekingen;
* maatstructuurhints;
* frasegrenzen;
* repetitiemarkeringen;
* layoutprioriteiten.

Daarom moeten tokens worden behandeld als een uitbreidbaar namespace-systeem en niet als losse ad-hoc markeringen.

De exacte formele uitbreidingsregels worden later apart gespecificeerd.

---

# Tekst en spacing

## Basisafstand

Tussen render-runs moet een minimale horizontale afstand bestaan.

Doel:

* voorkomen dat tekst en [glyphs](@) tegen elkaar aan staan;
* visuele rust creëren.

## Whitespace

Normale spaties in vrije tekst blijven behouden.

Extra renderer-spacing komt bovenop de tekstuele spacing.

## Zangelementen

Een [zangelement](@) bestaat visueel uit:

* gezongen tekst;
* bovenglyphs;
* onderglyphs.

De tekst vormt altijd het visuele ankerpunt.

## Smalle tekst versus brede muzikale structuur

Als:

```text
TB < Σ W[i]
```

waarbij:

* `TB` = tekstbreedte;
* `Σ W[i]` = totale breedte van de [muzikale posities](@);

dan behoudt het [zangelement](@) standaard zijn normale typografische breedte.

Default gedrag:

* tekst wordt gecentreerd;
* resterende ruimte wordt rechts opgevuld met een horizontale lijn.

Alternatieve configureerbare strategieën:

* fill-line;
* left-align;
* center-no-fill;
* stretch-text;
* proportional-spacing.

Default:

* fill-line.

---

# Pitch-markers

## Algemene vorm

Pitch-markers worden compact weergegeven.

De horizontale markerlijn:

* is korter dan de volledige positiebreedte;
* oogt als een kleine muzikale markering;
* staat los van de tekst.

## Spacing

Pitch-markers krijgen extra ruimte:

* vóór de volgende tekst;
* na voorafgaande tekst.

Pitch-markers mogen niet “vastplakken” aan woorden.

## Eind-pitch-markers

Eind-pitch-markers gebruiken dezelfde visuele stijl als begin-pitch-markers.

---

# Hoogte- en lengteglyphs

## Bovenglyphs

Bovenglyphs:

* zijn compact;
* lijken visueel op kleine accenttekens;
* staan dicht boven de tekst.

Bovenglyphs mogen niet:

* extreem breed zijn;
* te hoog boven de tekst zweven.

## Onderglyphs

Onderglyphs:

* functioneren visueel vergelijkbaar met underlines;
* staan dicht onder de tekst;
* kruisen geen letterstaarten.

Onderglyphs hoeven niet de volledige positiebreedte te beslaan.

## Configureerbare glyphs

Gebruikers moeten glyph-rendering kunnen aanpassen.

Voorbeelden:

* breedte;
* hoogte;
* offsets;
* lijnstijl;
* kleur;
* SVG-shapes;
* alternatieve glyphsymbolen.

De [renderer](@) moet daarom werken met een abstract [glyphmodel](@) en niet met hardcoded vormen.

## Alignment-markers

Het `&`-teken is een alignment-marker.

Alignment-markers koppelen [modifiers](@) visueel aan elkaar zodat:

* muzikale continuïteit zichtbaar wordt;
* glyphgroepen als één geheel ogen;
* [muzikale posities](@) optisch uitgelijnd blijven.

Voorbeelden:

* verbonden stijgende lijnen;
* doorlopende lengte-indicatoren;
* gekoppelde accentgroepen.

De exacte visuele interpretatie is renderer-afhankelijk.

---

# Verticale layout

## Regelafstand

Regelafstand moet configureerbaar zijn.

De regelafstand moet:

* voldoende ruimte geven voor bovenglyphs;
* voorkomen dat [glyphs](@) tussen regels botsen.

## Verticale offsets

Boven- en onderglyphs gebruiken configureerbare verticale offsets.

---

# Typografie

## Fonts

De [renderer](@) ondersteunt configureerbare fonts.

De default-font moet:

* goed leesbaar zijn;
* Unicode ondersteunen;
* geschikt zijn voor liturgische tekst.

## Fontgrootte

Tekstgrootte moet configureerbaar zijn.

Glyphgroottes schalen relatief mee.

---

# Kleuren

## Defaults

Default rendering:

* bovenglyphs zwart;
* onderglyphs rood;
* tekst zwart.

## Configureerbaarheid

Kleuren moeten configureerbaar zijn.

---

# Configuratie

## Configuratiebron

SVG-rendering-configuratie wordt opgenomen in `vsa.toml`.

## Default-configuratie

De [renderer](@) levert een ingebouwde default-configuratie.

## User overrides

Gebruikers mogen:

* een eigen configbestand opgeven;
* alleen specifieke waarden overriden;
* meerdere configuratielagen combineren.

Configuratie werkt volgens cascading overrides:

1. ingebouwde defaults;
2. projectconfig;
3. user-config;
4. CLI-overrides.

## Voorbeeldconfiguratie

```toml
[rendering.svg]
alignment = "left"
font-family = "Noto Serif"
font-size = 24
line-gap = 18
text-gap = 6
max-line-width = 900

[rendering.svg.pitch-marker]
dash-width-factor = 0.55
gap-before-text = 10

[rendering.svg.glyphs]
upper-color = "black"
lower-color = "red"
upper-width-factor = 0.65
lower-width-factor = 0.80
upper-offset = -8
lower-offset = 5

[rendering.svg.layout]
narrow-text-strategy = "fill-line"
```

---

# Responsiveness

SVG-rendering moet:

* schaalbaar zijn;
* mobiel bruikbaar blijven;
* horizontale overflow minimaliseren.

SVG-output moet correct functioneren op:

* desktop;
* tablet;
* telefoon;
* smalle foldable schermen.

---

# Open ontwerpvragen

Nog nader te bepalen:

* exacte glyphvormen;
* automatische wrapping-strategieën;
* printoptimalisatie;
* multi-voice rendering;
* interactieve SVG-functionaliteit;
* zoomgedrag;
* exportprofielen.

## Prioriteit

De volgende onderwerpen moeten relatief vroeg worden uitgewerkt:

* wrapping-strategieën;
* [glyphmodel](@);
* configuratie-architectuur.

De overige onderwerpen kunnen later worden uitgewerkt.



---

## Bron: `docs/spec/vsa-glyph-model.md`

# VSA Glyph Model Specification (Draft 1)

## Doel

Dit document beschrijft het abstracte [glyphmodel](@) voor VSA-rendering.

Het [glyphmodel](@) vormt de brug tussen:

* de VSA-semantiek;
* layoutberekening;
* concrete SVG-rendering;
* toekomstige exportformaten zoals MusicXML.

Het [glyphmodel](@) definieert:

* glyph-typen;
* positionering;
* metriek;
* anchors;
* verbindingen;
* schaalgedrag;
* theming;
* configuratie.

Het [glyphmodel](@) definieert niet:

* parsergedrag;
* syntax;
* semantische validatie.

Zie:

* [Specificatie — index](README.md)
* Historische brondocumenten (alleen in git-history / `docs/history/`)

---

# Architectuur

## Drie renderlagen

De [renderer](@) bestaat conceptueel uit drie lagen:

```text id="a7zqfc"
VSA AST
→ abstract glyph layout
→ concrete SVG primitives
```

### Laag 1 — Semantische representatie

De [parser](@) en [AST](@) kennen alleen muzikale intentie.

Voorbeelden:

* stijgend;
* dalend;
* vlak;
* verlengd;
* verbonden;
* pitch-referentie.

Deze laag kent geen:

* pixels;
* SVG paths;
* kleuren;
* fonts.

---

### Laag 2 — Abstract glyphmodel

De [renderer](@) vertaalt semantiek naar abstracte glyph-objecten.

Voorbeelden:

* `UpperGlyph`
* `LowerGlyph`
* `ConnectorGlyph`
* `PitchMarkerGlyph`

Deze laag definieert:

* vormcategorieën;
* metriek;
* anchors;
* verbindingen;
* layoutgedrag.

---

### Laag 3 — Concrete rendering

Pas in deze laag ontstaan concrete SVG-elementen zoals:

```text id="3rm2ti"
<line>
<path>
<polyline>
<circle>
```

Deze laag is renderer-specifiek.

---

# Muzikale posities

## Basisprincipe

De [renderer](@) werkt primair met [muzikale posities](@) en niet met letters.

Voorbeeld:

```text id="f8x1n7"
{/He_}
```

heeft:

* één [muzikale positie](@);
* een tekstbreedte;
* een glyphstructuur.

---

## Positie-eenheden

Elke [muzikale positie](@) heeft:

* een horizontale breedte;
* een center-anchor;
* een optische bounding box.

Positiebreedte hoeft niet gelijk te zijn aan tekstbreedte.

---

## Positiegroepen

Verbonden glyphgroepen kunnen meerdere [muzikale posities](@) omvatten.

Voorbeeld:

```text id="yxq3u3"
{/&/&\He_&_&_}
```

vormt één verbonden glyphgroep.

---

# Glyphfamilies

## Upper glyphs

Upper [glyphs](@) representeren:

* stijging;
* daling;
* vlakke beweging;
* korte ornamenten.

Bronsymbolen:

* `/`
* `\`
* `-`
* `~`

Visuele eigenschappen:

* compact;
* accentachtig;
* dicht boven de tekst.

---

## Lower glyphs

Lower [glyphs](@) representeren:

* lengte;
* duur;
* onderstructuren.

Visuele eigenschappen:

* underline-achtig;
* compact;
* dicht onder de tekst.

Lower [glyphs](@) mogen:

* korter zijn dan de volledige positiebreedte;
* afgeronde uiteinden gebruiken;
* variabele diktes gebruiken.

---

## Connector glyphs

Connector [glyphs](@) ontstaan uit alignment-markers (`&`).

Connector [glyphs](@):

* verbinden omliggende [glyphs](@);
* creëren visuele continuïteit;
* beïnvloeden layout.

Connector [glyphs](@) zijn geen zelfstandige [muzikale posities](@).

Voorbeeld:

```text id="1o4h5l"
{/&/&\He_&_&_}
```

Hier ontstaan:

* meerdere upper [glyphs](@);
* meerdere lower [glyphs](@);
* connectorlijnen tussen de [glyphs](@).

---

## Structural glyphs

Structural [glyphs](@) representeren:

* [pitch-markers](@);
* wraptokens;
* layoutmarkeringen;
* toekomstige exporthints.

Voorbeelden:

* `[:]`
* `[/]`
* `[/?]`

Niet alle structural [glyphs](@) hoeven zichtbaar te renderen.

---

# Glyph anchors

## Doel

Glyphs worden relatief gepositioneerd via anchors.

Dit voorkomt:

* hardcoded pixelplaatsing;
* typografische inconsistentie;
* schaalproblemen.

---

## Standaard anchors

De [renderer](@) ondersteunt minimaal:

| Anchor          | Betekenis                         |
| --------------- | --------------------------------- |
| baseline        | tekstbaseline                     |
| text-top        | bovenkant van tekst               |
| text-bottom     | onderkant van tekst               |
| position-center | centrum van [muzikale positie](@) |
| glyph-center    | centrum van [glyph](@)            |
| upper-anchor    | default anchor voor bovenglyphs   |
| lower-anchor    | default anchor voor onderglyphs   |

---

## Anchor-relaties

Glyphs worden relatief geplaatst ten opzichte van anchors.

Voorbeeld:

```text id="mqzq6j"
upper-glyph.y = text-top + upper-offset
```

---

# Glyphmetriek

## Relatieve metriek

Glyphs gebruiken relatieve metriek.

Niet aanbevolen:

* vaste pixels;
* absolute SVG-afstanden.

Aanbevolen:

* relatieve schaalfactoren;
* font-gerelateerde units;
* renderer-scalars.

---

## Glyph properties

Elke [glyph](@) kan eigenschappen hebben zoals:

```text id="jj8h6f"
width
height
stroke-width
offset-x
offset-y
opacity
join-style
cap-style
```

---

## Voorbeeldconfiguratie

```toml id="q1ovql"
[rendering.svg.glyphs.upper.rise]
width-factor = 0.65
height-factor = 0.80
stroke-width = 1.2
offset-y = -7
```

---

# Glyphlayout

## Layoutfasen

Glyphlayout gebeurt in meerdere fasen:

```text id="3ncl1p"
AST
→ musical positions
→ glyph grouping
→ anchor resolution
→ spacing
→ SVG output
```

---

## Optische compensatie

De [renderer](@) mag optische compensatie toepassen.

Voorbeelden:

* iets bredere [glyphs](@) bij kleine fonts;
* verticale correctie bij cursieve fonts;
* smallere connectors bij dichte tekst.

---

## Compactheid

Glyphlayout moet:

* compact blijven;
* visueel luchtig blijven;
* niet botsen met omliggende regels.

---

# Scaling

## Schaalgedrag

Glyphs schalen relatief mee met:

* font-size;
* DPI;
* exportresolutie;
* viewportgrootte.

---

## Minimumgroottes

Renderers mogen minimale:

* lijndiktes;
* glyphgroottes;
* offsets;

afdwingen om leesbaarheid te behouden.

---

# Theming

## Renderer-themes

Dezelfde VSA-inhoud moet met verschillende renderstijlen gerenderd kunnen worden.

Voorbeelden:

* classic;
* minimal;
* liturgikon;
* debug;
* high-contrast.

---

## Theme-inhoud

Een theme kan bepalen:

* glyphvormen;
* kleuren;
* spacing;
* offsets;
* stroke-stijlen;
* connectorgedrag;
* pitch-markerstijl.

---

## Theme-overrides

Themes mogen:

* defaults leveren;
* gedeeltelijk overridden worden;
* gecombineerd worden met user-config.

---

# Configureerbaarheid

## Configuratieprincipes

Glyphrendering moet configureerbaar zijn.

Gebruikers moeten onder andere kunnen aanpassen:

* breedte;
* hoogte;
* offsets;
* kleuren;
* lijnstijlen;
* connectorstijl;
* glyphvormen.

---

## Geldige configuratie

Glyphconfiguratie moet:

* vóór gebruik gevalideerd worden;
* parserambiguïteit vermijden;
* rendercrashes voorkomen;
* consistente anchors behouden.

Bij ongeldige configuratie moet:

* een duidelijke configuratiefout ontstaan;
* rendering stoppen;
* de foutlocatie vermeld worden.

---

## SVG-shape overrides

Renderers mogen alternatieve SVG-vormen ondersteunen.

Voorbeelden:

* custom SVG paths;
* alternatieve lijnvormen;
* ornamentsets;
* kalligrafische [glyphs](@).

Dit vereist een abstract [glyphmodel](@) en geen hardcoded SVG-primitives.

---

# Toekomstige uitbreidingen

## MusicXML

Het [glyphmodel](@) moet later gekoppeld kunnen worden aan:

* MusicXML;
* maatstructuren;
* frasegrenzen;
* systeemindeling.

Daarom moeten [glyphs](@) semantisch interpreteerbaar blijven.

---

## Multi-voice rendering

Toekomstige [renderers](@) kunnen:

* meerdere stemmen;
* syncgroepen;
* gedeelde [muzikale posities](@);

ondersteunen.

---

## Interactieve rendering

Toekomstige SVG-renderers kunnen:

* hoverinformatie;
* debugging overlays;
* clickable [glyphs](@);
* synchronized playback;

ondersteunen.

Het [glyphmodel](@) moet dit niet blokkeren.

---

# Open ontwerpvragen

Nog nader te bepalen:

* exacte glyphvormen;
* connectoralgoritmen;
* automatische optische compensatie;
* glyphcollision-resolutie;
* printoptimalisatie;
* kalligrafische rendering;
* MusicXML-mappingdetails;
* SATB-layoutregels.



---

## Bron: `docs/spec/vsa-glyph-layout-rules.md`

# VSA Glyph Layout Rules (Draft 2)

## Doel

Dit document beschrijft de layoutregels voor VSA-glyphs.

Het document vult aan:

- `vsa-svg-rendering-spec.md`
- `vsa-glyph-model.md`
- `vsa-spec-v1.md`

De regels in dit document zijn bedoeld als directe basis voor SVG-rendering.

De focus ligt op:
- duidelijke leesbaarheid;
- bruikbaarheid op scherm;
- bruikbaarheid op enige afstand;
- robuuste automatische layout;
- configureerbare stijl.

Deze specificatie is niet bedoeld voor professionele drukwerktypografie.

---

# Glossary

| Term             | Betekenis                                                                    |
| ---------------- | ---------------------------------------------------------------------------- |
| [VSA](@)         | De tekstuele notatie voor zangtekst, pitchmarkers en muzikale [modifiers](@) |
| Renderer         | Het onderdeel dat [VSA](@) omzet naar zichtbare output, bijvoorbeeld SVG     |
| SVG              | Scalable Vector Graphics; het uitvoerformaat voor schaalbare tekeningen      |
| Glyph            | Een zichtbaar teken of vormpje dat door de [renderer](@) wordt getekend      |
| [EHM](@)         | Een elementaire hoogtemodifier, bijvoorbeeld `/`, `\` of `///`               |
| [ELM](@)         | Een elementaire lengtemodifier, bijvoorbeeld `_`                             |
| Bovenglyph       | Een [glyph](@) boven de gezongen tekst                                       |
| Onderglyph       | Een [glyph](@) onder de gezongen tekst                                       |
| Pitchmarker      | Een constructie zoals `[:]`, `[/:]` of `[\\:]`                               |
| Zangelement      | Een VSA-constructie tussen `{` en `}`, bijvoorbeeld `{/Heer_}`               |
| Render-unit      | Een ondeelbaar visueel element voor layout en wrapping                       |
| Glyphgroep       | Een groep [glyphs](@) die samen bij één render-unit horen                    |
| Alignment-marker | Het `&`-teken dat [glyphs](@) binnen een [zangelement](@) visueel koppelt    |
| Baseline         | De denkbeeldige lijn waarop tekst rust                                       |
| Text box         | De visuele ruimte die de tekst inneemt                                       |
| Collision        | Een botsing of overlap tussen tekst, [glyphs](@) of render-units             |
| Wrapping         | Het afbreken van render-units naar een volgende regel                        |
| Overflow         | Situatie waarin een render-unit breder is dan de beschikbare regelbreedte    |

---

# Visuele uitgangspunten

De VSA-rendering volgt het compacte karakter van Liturgikon-achtige voorbeelden.

Daarin staan hoogte- en lengtemarkeringen:
- dicht bij de tekst;
- compact;
- optisch licht;
- duidelijk gekoppeld aan de betreffende lettergreep of tekstpositie.

Glyphs moeten de tekst ondersteunen, niet domineren.

De belangrijkste visuele prioriteiten zijn:
1. tekst blijft goed leesbaar;
2. [glyphs](@) zijn duidelijk herkenbaar;
3. [glyphs](@) zitten dicht genoeg op de tekst om erbij te horen;
4. [glyphs](@) overlappen niet;
5. de layout blijft compact.

---

# Coordinate system en anchors

## Praktische keuze

De [renderer](@) gebruikt een baseline-gebaseerd coordinate system.

Elke renderregel heeft:
- een baseline;
- een text-top;
- een text-bottom;
- een line-box.

Dit is voldoende nauwkeurig voor de huidige toepassing en voorkomt onnodige typografische complexiteit.

## Anchors

Glyphs worden relatief aan tekst-anchors geplaatst.

Minimale anchors:

| Anchor          | Betekenis                                       |
| --------------- | ----------------------------------------------- |
| baseline        | lijn waarop tekst rust                          |
| text-top        | bovenkant van de tekst-box                      |
| text-bottom     | onderkant van de tekst-box                      |
| position-center | horizontaal midden van de [muzikale positie](@) |
| unit-left       | linkerrand van de render-unit                   |
| unit-right      | rechterrand van de render-unit                  |

## Bovenglyph-positionering

Bovenglyphs worden geplaatst:
- boven de tekst-box;
- dicht bij de tekst;
- relatief aan `text-top`.

Default:

```toml
[rendering.svg.glyphs.upper]
offset-y = -0.30
```

`offset-y` is relatief aan de fontgrootte.

Negatieve waarden staan boven de tekst.

## Onderglyph-positionering

Onderglyphs worden geplaatst:
- onder de tekst;
- dicht bij de baseline;
- zonder letterstaarten te kruisen.

Default:

```toml
[rendering.svg.glyphs.lower]
offset-y = 0.18
```

De [renderer](@) mag de onderglyph iets lager plaatsen als het font veel descenders heeft.

---

# Render-units

Voor layout gebruikt de [renderer](@) ondeelbare render-units.

Voorbeelden:

```text
vrije tekst
zangelement met glyphs
pitchmarker
non-breaking group
wraptoken
```

Een [zangelement](@) met [glyphs](@) is één render-unit.

Voorbeeld:

```text
{/ver}
```

mag niet over twee regels worden verdeeld.

Ook een complex [zangelement](@) blijft ondeelbaar:

```text
{\&/&/trou-.&.&_}
```

Pitchmarkers zijn ook ondeelbare render-units.

Voorbeeld:

```text
[/:]
```

mag niet gesplitst worden.

---

# Muzikale positie

## Renderingdefinitie

Voor SVG-rendering is een [muzikale positie](@) de horizontale plaats waarop één [glyph](@) of glyphgroep wordt gecentreerd ten opzichte van tekst.

Een [muzikale positie](@) is dus een layoutbegrip.

Het is niet noodzakelijk hetzelfde als:
- een letter;
- een lettergreep;
- een MusicXML-noot;
- een toekomstige SATB-syncpositie.

## Waarvoor gebruikt de renderer muzikale posities?

De [renderer](@) gebruikt [muzikale posities](@) om te beslissen:
- waar bovenglyphs komen;
- waar onderglyphs komen;
- hoe breed een [zangelement](@) minimaal moet zijn;
- waar alignment-groepen optisch worden geplaatst;
- of [glyphs](@) elkaar raken;
- of een render-unit te breed wordt voor de regel.

## Breedte van een muzikale positie

De breedte van een [muzikale positie](@) wordt bepaald door:

```text
max(tekstdeelbreedte, glyphbreedte + minimale marge)
```

Dus:
- korte tekst met brede [glyph](@) krijgt extra ruimte;
- lange tekst met smalle [glyph](@) wordt niet samengedrukt;
- [glyphs](@) mogen niet overlappen.

## Breedte van een render-unit

De breedte van een [zangelement](@) is de som van de benodigde [muzikale posities](@).

Als de glyphstructuur breder is dan de tekst:
- wordt de render-unit breder;
- blijft de tekst leesbaar;
- wordt wrapping toegepast als de render-unit niet meer op de regel past.

---

# Wrapping

De [renderer](@) mag afbreken tussen render-units volgens de wrapping-regels uit de SVG-rendering-spec.

Een render-unit wordt niet intern gesplitst.

Als een render-unit te breed is voor de resterende regelruimte, wordt deze naar de volgende regel verplaatst.

Als een render-unit op zichzelf breder is dan de maximale regelbreedte, gebruikt de [renderer](@) fallbackgedrag.

Default fallback:

```text
overflow toestaan + warning diagnostic
```

Andere mogelijke fallbackstrategieën:
- schaalreductie;
- overflow-indicator;
- debugmelding;
- expliciete foutmelding.

---

# Glyph-overlap

Glyphs mogen standaard niet overlappen.

Dit geldt voor:
- bovenglyphs onderling;
- onderglyphs onderling;
- bovenglyphs en tekst;
- onderglyphs en tekst;
- pitchmarkers en tekst;
- [glyphs](@) van aangrenzende render-units.

Als overlap dreigt, probeert de [renderer](@) in deze volgorde:

1. compacte glyphmetriek toepassen;
2. horizontale spacing binnen de render-unit vergroten;
3. render-unit naar de volgende regel verplaatsen;
4. fallbackgedrag toepassen.

De [renderer](@) mag [glyphs](@) niet laten samenvallen om ruimte te besparen.

---

# Elementaire hoogtemodifiers en stacking

## Eén EHM is één glyph

Een [EHM](@) wordt als één [glyph](@) gerenderd.

Voorbeeld:

```text
/
```

is één [glyph](@).

Ook dit is één [EHM](@) en dus één [glyph](@):

```text
///
```

Het is dus niet een stack van drie losse [glyphs](@).

## Leesbaarheid

Een [glyph](@) voor `///` moet duidelijk herkenbaar zijn, ook op enige afstand.

Default rendering mag bestaan uit drie duidelijk onderscheidbare schuine streepjes.

Toekomstige themes mogen alternatieve glyphvormen gebruiken.

Voorbeeld van een mogelijk alternatief:

```text
/3
```

of een compactere gestileerde vorm.

Deze alternatieven zijn niet voor de eerste [renderer](@) vereist, maar het [glyphmodel](@) mag ze niet blokkeren.

## Geen whitespace-stacking

Een constructie zoals:

```text
~~~
```

wordt niet als zinvolle EHM-stack beschouwd.

Als `~` later een betekenis heeft, moet die betekenis afzonderlijk worden gespecificeerd.

Voor nu geldt:
- `///` kan één samengestelde EHM-glyph zijn;
- `~~~` is geen stapel van whitespace-glyphs.

---

# Gekoppelde glyphs en alignment-markers

## Betekenis van `&`

Alignment-markers (`&`) koppelen [glyphs](@) visueel.

Default betekent `&`:

```text
compacte gekoppelde glyphgroep
```

Niet:

```text
teken altijd een expliciete connectorlijn
```

## Visueel gedrag

Gekoppelde [glyphs](@):
- blijven afzonderlijk herkenbaar;
- staan compact bij elkaar;
- vormen één optische groep;
- worden samen gewrapped;
- worden samen gecontroleerd op collisions.

Gekoppelde [glyphs](@) mogen niet:
- volledig samenvallen;
- versmelten tot één onleesbare lijn;
- visueel losraken van hun groep.

## Voorbeeld

```text
{\&/ver}
```

bevat gekoppelde hoogte-informatie.

```text
{\&/&/trou-.&.&_}
```

bevat meerdere gekoppelde [glyphs](@) die als groep moeten ogen, maar waarvan de afzonderlijke glyphposities zichtbaar blijven.

## Connectorvorm

De default connectorvorm is impliciet.

Dat wil zeggen:
- de verbinding ontstaat door nabijheid, gedeelde uitlijning en compacte spacing;
- er wordt standaard geen zware expliciete verbindingslijn getekend.

Themes mogen later expliciete connectorlijnen toevoegen.

---

# Bovenglyphs

Bovenglyphs staan dicht boven de tekst.

Visuele regels:
- ze hebben het karakter van kleine accenttekens;
- ze zijn korter dan de volledige tekstbreedte;
- ze zweven niet hoog boven de tekst;
- samengestelde bovenglyphs blijven compact;
- onderscheidbaarheid gaat vóór extreme compactheid.

Default richtwaarden:

```toml
[rendering.svg.glyphs.upper]
width-factor = 0.60
offset-y = -0.30
stroke-width-factor = 0.055
```

Waarbij waarden relatief zijn ten opzichte van de fontgrootte of positiehoogte.

---

# Onderglyphs

Onderglyphs staan dicht onder de tekst.

Visuele regels:
- ze lijken op onderstreping;
- ze kruisen geen letterstaarten;
- ze zijn korter dan de volledige positiebreedte;
- ze blijven optisch verbonden met de tekst.

Default richtwaarden:

```toml
[rendering.svg.glyphs.lower]
width-factor = 0.80
offset-y = 0.18
stroke-width-factor = 0.055
```

De [renderer](@) mag onderglyphs iets lager plaatsen bij fonts met lange descenders.

---

# Pitchmarkers

## Rendering

Pitchmarkers worden gerenderd als compacte tekstachtige symbolen.

Een pitchmarker bestaat visueel uit:
- een korte horizontale markerlijn;
- optioneel een EHM-glyph erboven.

Voorbeeld:

```text
[:]
```

is een compacte horizontale marker.

Voorbeeld:

```text
[/:]
```

bestaat uit:
- horizontale marker;
- bovenglyph voor `/`.

## Positionering

De EHM-glyph van een pitchmarker staat lateraal en verticaal zoals een bovenglyph, maar hoort bij de pitchmarker zelf.

De EHM-glyph van een pitchmarker komt visueel later dan de bovenglyphs boven gewone tekst.

Dat betekent:
- pitchmarker-glyphs mogen iets hoger of anders gecentreerd worden;
- ze blijven compact;
- ze mogen niet vastplakken aan tekst.

## Context

Pitchmarkers kunnen in verschillende contexten verschillende semantische betekenis hebben.

Voor SVG-rendering geldt:
- als er een pitchmarker staat, render dan het compacte symbool;
- interpreteer niet de volledige muzikale betekenis;
- laat validatie aan validatorregels;
- laat MusicXML-betekenis aan MusicXML-exportregels.

## Spacing

Pitchmarkers zijn ondeelbare render-units.

Default spacing:

```toml
[rendering.svg.pitch-marker]
gap-before = 0.35
gap-after = 0.35
dash-width-factor = 0.45
```

De horizontale markerlijn is compact.

---

# Spacing tussen render-units

De [renderer](@) gebruikt minimale horizontale spacing tussen render-units.

Default:

```toml
[rendering.svg.spacing]
text-gap = 0.20
scope-gap = 0.12
pitch-marker-gap = 0.35
```

Deze waarden zijn relatief ten opzichte van de fontgrootte.

Spacing mag worden vergroot om overlap te voorkomen.

Spacing mag niet worden uitgerekt om regels tweezijdig uit te vullen, tenzij expliciet geconfigureerd.

---

# Regelafstand

Regelafstand moet voldoende ruimte bieden voor:
- bovenglyphs;
- onderglyphs;
- samengestelde [glyphs](@);
- pitchmarkers.

Default:

```toml
[rendering.svg.lines]
line-gap = 1.35
min-line-gap = 1.15
```

De regelafstand is configureerbaar.

---

# Layoutprioriteiten

Bij conflicten gebruikt de [renderer](@) deze prioriteit:

1. syntax correct renderen;
2. tekst leesbaar houden;
3. [glyphs](@) niet laten overlappen;
4. render-units ondeelbaar houden;
5. compacte layout behouden;
6. regelbreedte respecteren.

Dit betekent dat de [renderer](@) liever een regel eerder afbreekt dan [glyphs](@) laat overlappen.

---

# Debug rendering

Een debug-theme mag tonen:
- render-unit boundaries;
- [glyph](@) bounding boxes;
- anchors;
- collision boxes;
- wrap candidates;
- overflow;
- [muzikale posities](@).

Dit is bedoeld voor ontwikkeling en correctie van praktijkvoorbeelden.

---

# Configuratie

Glyph-layout wordt configureerbaar via `vsa.toml`.

Voorbeeld:

```toml
[rendering.svg]
font-size = 24
alignment = "left"
max-line-width = 900

[rendering.svg.spacing]
text-gap = 0.20
scope-gap = 0.12
pitch-marker-gap = 0.35

[rendering.svg.lines]
line-gap = 1.35
min-line-gap = 1.15

[rendering.svg.glyphs.upper]
width-factor = 0.60
offset-y = -0.30
stroke-width-factor = 0.055
color = "black"

[rendering.svg.glyphs.lower]
width-factor = 0.80
offset-y = 0.18
stroke-width-factor = 0.055
color = "red"

[rendering.svg.pitch-marker]
gap-before = 0.35
gap-after = 0.35
dash-width-factor = 0.45
```

---

# Config-validatie

Renderingconfiguratie moet vóór gebruik worden gevalideerd.

Ongeldig zijn bijvoorbeeld:
- negatieve glyphbreedtes;
- lege kleurwaarden;
- onbekende alignment-waarden;
- niet-numerieke offsets;
- line-gap kleiner dan minimum;
- [glyphs](@) met nulbreedte;
- tokens die VSA-syntax breken.

Bij ongeldige configuratie stopt rendering met een duidelijke configuratiefout.

---

# Open ontwerpvragen

Nog nader uit te werken:
- exacte defaultwaarden na visuele test;
- fallback bij extreem brede render-units;
- debug-theme;
- relatie met MusicXML-layout;
- printprofiel;
- alternatieve glyphvormen per theme.



---

## Bron: `docs/spec/vsa-layout-algorithm.md`

# VSA Layout Algorithm Specification (Draft 1)

## Doel

Dit document beschrijft het formele layout-algoritme voor VSA-rendering.

Het algoritme beschrijft de stap van:

```text
VSA AST
→ render-units
→ muzikale posities
→ glyphlayout
→ wrapping
→ SVG-output
```

Dit document vult aan:

- `vsa-svg-rendering-spec.md`
- `vsa-glyph-model.md`
- `vsa-glyph-layout-rules.md`
- `vsa-svg-dom-structure.md`
- `vsa-rendering-config-model.md`

De focus ligt op een praktische, goed leesbare [renderer](@) voor scherm en website.

---

# Hoofdprincipes

De [renderer](@) moet:

- tekst leesbaar houden;
- [glyphs](@) dicht bij de tekst plaatsen;
- [glyphs](@) niet laten overlappen;
- render-units ondeelbaar houden;
- links uitlijnen als default;
- deterministic output geven;
- configuratie vóór rendering valideren.

De [renderer](@) is niet bedoeld als professionele drukwerk-engine.

---

# Renderpipeline

De [renderer](@) doorloopt conceptueel deze fasen:

```text
1. Config laden en valideren
2. AST ontvangen
3. Render-units bouwen
4. Muzikale posities bepalen
5. Tekst meten
6. Glyphgroepen bouwen
7. Minimale breedtes bepalen
8. Anchors oplossen
9. Collisiondetectie uitvoeren
10. Wrapping toepassen
11. Regels positioneren
12. SVG-DOM genereren
```

Elke fase mag extra debug-informatie produceren als een debug-theme actief is.

---

# Fase 1: config laden en valideren

Voor rendering begint, wordt de effectieve configuratie bepaald.

Volgorde:

```text
ingebouwde defaults
→ theme
→ projectconfig
→ user override
→ CLI override
```

De effectieve configuratie wordt gevalideerd.

Ongeldige configuratie stopt rendering met een duidelijke configuratiefout.

Voorbeelden van ongeldige configuratie:

- negatieve glyphbreedte;
- onbekende alignmentwaarde;
- lege kleurwaarde;
- wraptoken dat bestaande VSA-syntax breekt;
- line-gap kleiner dan minimum;
- [glyph](@) met nulbreedte.

---

# Fase 2: AST ontvangen

De [renderer](@) werkt niet rechtstreeks op ruwe tekst, maar op de geparseerde VSA-structuur.

De [AST](@) bevat betekenisvolle constructies zoals:

- vrije tekst;
- [zangelement](@);
- pitchmarker;
- [modifiers](@);
- alignment-markers.

De [renderer](@) mag geen syntax herstellen.

Syntaxfouten horen vóór rendering te zijn afgehandeld door [parser](@) en [validator](@).

---

# Fase 3: render-units bouwen

Een render-unit is een ondeelbaar visueel layout-element.

Voorbeelden:

```text
vrije tekst
zangelement met glyphs
pitchmarker
non-breaking group
wraptoken
```

Render-units worden niet intern gesplitst tijdens wrapping.

Voorbeeld:

```text
{/ver}
```

blijft altijd één render-unit.

Ook dit blijft één render-unit:

```text
{\&/&/trou-.&.&_}
```

---

# Fase 4: muzikale posities bepalen

Voor SVG-rendering is een [muzikale positie](@) een horizontale plaats waarop één [glyph](@) of glyphgroep wordt gecentreerd.

De [renderer](@) gebruikt [muzikale posities](@) voor:

- bovenglyphplaatsing;
- onderglyphplaatsing;
- collisiondetectie;
- minimale breedte van [zangelementen](@);
- alignment-groepen;
- toekomstige MusicXML- en polyfonievoorbereiding.

Een [muzikale positie](@) is niet noodzakelijk hetzelfde als:

- een letter;
- een lettergreep;
- een MusicXML-noot;
- een toekomstige SATB-syncpositie.

---

# Fase 5: tekst meten

De [renderer](@) meet tekst met:

- actief font;
- actieve font-size;
- actuele renderer-context.

Tekstmeting moet deterministic zijn binnen dezelfde omgeving.

De [renderer](@) mag ligatures standaard uitschakelen om voorspelbare meting te krijgen.

Fallbackfonts moeten expliciet in de configuratie kunnen worden opgenomen.

---

# Fase 6: glyphgroepen bouwen

Modifiers worden vertaald naar abstracte glyphgroepen.

Voorbeelden:

| [VSA](@) | Renderbetekenis                    |
| -------- | ---------------------------------- |
| `/`      | bovenglyph voor stijgende beweging |
| `\`      | bovenglyph voor dalende beweging   |
| `///`    | één samengestelde EHM-glyph        |
| `_`      | onderglyph / lengte-indicatie      |
| `&`      | alignmentrelatie binnen glyphgroep |

Alignment-markers creëren standaard geen zware verbindingslijn.

Defaultinterpretatie:

```text
& = compacte gekoppelde glyphgroep
```

Gekoppelde [glyphs](@) blijven afzonderlijk herkenbaar.

---

# Fase 7: minimale breedtes bepalen

De minimale breedte van een [muzikale positie](@) is:

```text
max(tekstdeelbreedte, glyphbreedte + marge)
```

De minimale breedte van een [zangelement](@) is de som van de benodigde posities.

Gevolgen:

- tekst wordt niet samengedrukt;
- [glyphs](@) overlappen niet;
- brede glyphstructuren kunnen een [zangelement](@) breder maken dan de tekst;
- wrapping gebeurt tussen render-units als de unit niet meer past.

---

# Fase 8: anchors oplossen

Elke renderregel heeft:

- baseline;
- text-top;
- text-bottom;
- line-box.

Glyphs worden geplaatst ten opzichte van anchors.

Minimale anchors:

| Anchor          | Betekenis                                    |
| --------------- | -------------------------------------------- |
| baseline        | lijn waarop tekst rust                       |
| text-top        | bovenkant tekst-box                          |
| text-bottom     | onderkant tekst-box                          |
| position-center | horizontaal midden van [muzikale positie](@) |
| unit-left       | linkerrand render-unit                       |
| unit-right      | rechterrand render-unit                      |

---

# Fase 9: collisiondetectie

Collisiondetectie controleert dat tekst, [glyphs](@) en units elkaar niet visueel hinderen.

Verboden overlap:

- [glyph](@) met [glyph](@);
- [glyph](@) met tekst;
- [glyph](@) met pitchmarker;
- aangrenzende render-units;
- [glyphs](@) tussen regels.

Als collision dreigt, gebruikt de [renderer](@) deze volgorde:

```text
1. compacte glyphmetriek toepassen
2. spacing binnen render-unit vergroten
3. render-unit naar volgende regel verplaatsen
4. overflow fallback toepassen
```

---

# Fase 10: wrapping

Wrapping gebeurt alleen tussen render-units.

Prioriteiten:

```text
forced break
→ non-breaking group
→ preferred break
→ natuurlijke afbreekpunten
→ overflow fallback
```

Forced breaks winnen altijd van automatische layout.

Non-breaking groups worden niet intern gesplitst.

Als een non-breaking group breder is dan de maximale regelbreedte, gebruikt de [renderer](@) overflow fallback.

---

# Fase 11: regels positioneren

Default regeluitlijning:

```text
left
```

Optioneel:

- right;
- center;
- justify.

Bij justify mogen alleen inter-unit gaps worden uitgerekt.

Niet uitrekken:

- glyphgroepen;
- pitchmarkers;
- interne glyphspacing;
- tekst binnen [zangelementen](@).

---

# Fase 12: SVG-DOM genereren

De [renderer](@) genereert SVG volgens `vsa-svg-dom-structure.md`.

Minimaal:

```xml
<svg>
  <g class="vsa-score">
    <g class="vsa-line">
      <g class="vsa-unit">
        ...
      </g>
    </g>
  </g>
</svg>
```

Render-units krijgen eigen `<g>`-groepen.

Glyphs krijgen semantische CSS-klassen.

---

# Renderer diagnostics

De [renderer](@) mag [diagnostics](@) produceren.

Voorbeelden:

| Code                           | Betekenis                                      |
| ------------------------------ | ---------------------------------------------- |
| `VSA-RENDER-OVERFLOW`          | render-unit past niet binnen max-line-width    |
| `VSA-RENDER-COLLISION`         | collision kon niet automatisch opgelost worden |
| `VSA-RENDER-UNSUPPORTED-GLYPH` | glyphvorm bestaat niet in theme                |
| `VSA-RENDER-CONFIG-ERROR`      | ongeldige renderingconfiguratie                |

Default:
- overflow is warning;
- configfouten zijn error;
- unsupported [glyph](@) is error of warning afhankelijk van fallback.

---

# Determinisme

Bij gelijke input, configuratie en fontomgeving moet de SVG-output gelijk zijn.

Dat is belangrijk voor:

- CI;
- regressietests;
- Git diffs;
- documentatievoorbeelden.

---

# Open ontwerpvragen

Nog nader uit te werken:

- exacte text measurement API;
- debug-theme;
- overflowvisualisatie;
- caching;
- printprofiel;
- MusicXML-layoutmapping.



---

## Bron: `docs/spec/vsa-svg-dom-structure.md`

# VSA SVG DOM Structure Specification (Draft 1)

## Doel

Dit document beschrijft de SVG-DOM-structuur voor VSA-rendering.

Doelen:

- consistente SVG-output;
- CSS-stylebaarheid;
- debugbaarheid;
- testbaarheid;
- toekomstige editor- en hoverfunctionaliteit.

Dit document definieert geen visuele stijl. Stijl komt uit renderingconfiguratie en themes.

---

# Basisstructuur

Minimale structuur:

```xml
<svg class="vsa-svg" xmlns="http://www.w3.org/2000/svg">
  <g class="vsa-score">
    <g class="vsa-line">
      <g class="vsa-unit">
        ...
      </g>
    </g>
  </g>
</svg>
```

---

# Root `<svg>`

De root bevat:

- `class="vsa-svg"`;
- `xmlns`;
- `viewBox`;
- `width` en/of `height` indien nodig;
- optioneel `role="img"`.

Voorbeeld:

```xml
<svg class="vsa-svg"
     xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 900 120">
</svg>
```

---

# Score group

Alle inhoud staat binnen:

```xml
<g class="vsa-score">
```

Deze groep vertegenwoordigt één gerenderd VSA-document of [VSA-blok](@).

---

# Line groups

Elke renderregel krijgt:

```xml
<g class="vsa-line" data-vsa-line="1">
```

Line groups bevatten render-units.

Line groups mogen via `transform="translate(x y)"` gepositioneerd worden.

---

# Render-unit groups

Elke render-unit krijgt:

```xml
<g class="vsa-unit">
```

Aanbevolen attributen:

```xml
data-vsa-unit="scope"
data-vsa-source-start="..."
data-vsa-source-end="..."
```

Mogelijke unittypes:

| Type                | Betekenis                     |
| ------------------- | ----------------------------- |
| `text`              | vrije tekst                   |
| `scope`             | [zangelement](@)              |
| `pitch-marker`      | pitchmarker                   |
| `wrap-token`        | niet-zichtbare wrapinstructie |
| `nonbreaking-group` | non-breaking group            |

---

# Text nodes

Tekst wordt gerenderd met:

```xml
<text class="vsa-text">...</text>
```

Voor [zangelementen](@) kan de gezongen tekst apart worden geclassificeerd:

```xml
<text class="vsa-sung-text">...</text>
```

Vrije tekst:

```xml
<text class="vsa-free-text">...</text>
```

---

# Glyph groups

Glyphs worden gegroepeerd in:

```xml
<g class="vsa-glyph-group">
```

Specifiek:

```xml
<g class="vsa-upper-glyphs">
<g class="vsa-lower-glyphs">
```

Gekoppelde [glyphs](@) via `&` staan binnen één glyphgroep.

---

# Individual glyphs

Elke [glyph](@) krijgt een semantische klasse.

Voorbeelden:

```xml
<path class="vsa-glyph vsa-upper-glyph vsa-glyph-rise" />
<path class="vsa-glyph vsa-upper-glyph vsa-glyph-fall" />
<line class="vsa-glyph vsa-lower-glyph vsa-glyph-length" />
```

Aanbevolen data-attributen:

```xml
data-vsa-glyph="/"
data-vsa-position="2"
```

---

# Pitchmarkers

Pitchmarkers krijgen:

```xml
<g class="vsa-unit vsa-pitch-marker">
```

Binnen een pitchmarker:

```xml
<line class="vsa-pitch-marker-dash" />
<g class="vsa-pitch-marker-upper-glyph">...</g>
```

`[:]` bevat alleen de compacte markerlijn.

`[/:]` bevat markerlijn plus bovenglyph.

---

# Debug layers

Debug-output mag optionele lagen bevatten:

```xml
<g class="vsa-debug vsa-debug-bounds">
<g class="vsa-debug vsa-debug-anchors">
<g class="vsa-debug vsa-debug-wrap">
```

Debuglagen zijn standaard uitgeschakeld.

---

# CSS-klassen

Minimale CSS-klassen:

```text
vsa-svg
vsa-score
vsa-line
vsa-unit
vsa-text
vsa-free-text
vsa-sung-text
vsa-glyph
vsa-glyph-group
vsa-upper-glyphs
vsa-lower-glyphs
vsa-pitch-marker
vsa-pitch-marker-dash
```

---

# Style strategy

Default mag styling inline zijn voor zelfstandige SVG-output.

Daarnaast moet class-based styling mogelijk blijven.

Aanbevolen:

- geometrie in SVG-attributen;
- kleur/stroke via CSS of theme;
- debugstyling via CSS-klassen.

---

# IDs

Stabiele ids zijn optioneel.

Als ids worden gegenereerd, moeten ze deterministic zijn binnen één rendering.

Aanbevolen vorm:

```text
vsa-line-1
vsa-unit-1-3
vsa-glyph-1-3-2
```

---

# Toekomstige interactiviteit

De structuur moet geschikt blijven voor:

- hover [diagnostics](@);
- source mapping;
- editorselectie;
- synced playback;
- click-to-source;
- debug overlays.

Daarom mogen [renderers](@) data-attributen toevoegen zolang ze geen bestaande output breken.

---

# Open ontwerpvragen

Nog nader uit te werken:

- exacte source-map attributen;
- ARIA/accessible SVG;
- CSS packaging;
- interactive mode;
- debug theme classes.



---

## Bron: `docs/spec/vsa-rendering-config-model.md`

# VSA Rendering Configuration Model (Draft 1)

## Doel

Dit document beschrijft het configuratiemodel voor VSA-rendering.

Het document definieert:

- configuratiebronnen;
- overridevolgorde;
- themes;
- geldigheidscontrole;
- rendererdiagnostics;
- toekomstige uitbreidbaarheid.

---

# Configuratielagen

De effectieve renderingconfiguratie wordt opgebouwd uit lagen.

Volgorde:

```text
1. ingebouwde defaults
2. theme defaults
3. projectconfig
4. user override
5. CLI override
```

Latere lagen overschrijven eerdere lagen.

---

# Ingebouwde defaults

De [renderer](@) bevat ingebouwde defaults voor:

- font;
- font-size;
- line-gap;
- spacing;
- glyphkleuren;
- glyphbreedtes;
- pitchmarkerstijl;
- wrappingtokens;
- fallbackgedrag.

Rendering moet ook zonder configbestand werken.

---

# Themes

Een theme is een benoemde set renderingkeuzes.

Voorbeelden:

```text
default
liturgikon
minimal
debug
high-contrast
```

Themes mogen instellen:

- kleuren;
- glyphvormen;
- spacing;
- line-gap;
- connectorstijl;
- pitchmarkerstijl;
- debugvisualisatie.

Themes mogen niet wijzigen:

- VSA-syntax;
- parsergedrag;
- semantische betekenis.

---

# Projectconfig

Projectconfiguratie staat standaard in:

```text
vsa.toml
```

Voorbeeld:

```toml
[rendering.svg]
theme = "liturgikon"
alignment = "left"
font-family = "Noto Serif"
font-size = 24
max-line-width = 900
```

---

# User override

Een user override is bedoeld voor lokale voorkeuren.

Voorbeelden:

- groter font;
- high contrast;
- andere kleuren;
- debugtheme.

Deze laag hoort niet noodzakelijk in Git.

---

# CLI override

CLI overrides hebben hoogste prioriteit.

Voorbeelden:

```cmd
vsa svg input.vsa output.svg --font-size 28
vsa build-markdown content generated static\vsa --config vsa.toml
```

CLI overrides moeten beperkt blijven tot veelgebruikte opties.

---

# Merge-regels

Configuratie wordt deep-merged.

Voorbeeld:

```toml
[rendering.svg.glyphs.upper]
color = "black"
width-factor = 0.60
```

Een override:

```toml
[rendering.svg.glyphs.upper]
color = "blue"
```

wijzigt alleen `color`.

`width-factor` blijft uit de vorige laag bestaan.

---

# Config-validatie

Voor rendering wordt de effectieve config gevalideerd.

Ongeldig:

- negatieve afstanden;
- nulbreedte [glyphs](@);
- onbekende alignmentwaarden;
- lege fontnaam;
- lege kleurwaarde;
- line-gap kleiner dan minimum;
- wraptokens die VSA-syntax breken;
- overlappende tokens;
- onbekende fallbackstrategie.

Bij fout:

```text
VSA-RENDER-CONFIG-ERROR
```

Rendering stopt.

---

# Voorbeeldconfig

```toml
[rendering.svg]
theme = "liturgikon"
alignment = "left"
font-family = "Noto Serif"
font-size = 24
max-line-width = 900

[rendering.svg.spacing]
text-gap = 0.20
scope-gap = 0.12
pitch-marker-gap = 0.35

[rendering.svg.lines]
line-gap = 1.35
min-line-gap = 1.15

[rendering.svg.glyphs.upper]
color = "black"
width-factor = 0.60
offset-y = -0.30
stroke-width-factor = 0.055

[rendering.svg.glyphs.lower]
color = "red"
width-factor = 0.80
offset-y = 0.18
stroke-width-factor = 0.055

[rendering.svg.pitch-marker]
gap-before = 0.35
gap-after = 0.35
dash-width-factor = 0.45

[rendering.svg.wrapping.tokens]
forced-line-break = ["[/]", "[*]"]
preferred-break = ["[/?]", "[*?]"]
nonbreaking-start = "[="
nonbreaking-end = "=]"
```

---

# Geldige tokenconfiguratie

Wraptokens en toekomstige layouttokens moeten:

- niet leeg zijn;
- uniek zijn;
- niet ambigu overlappen;
- bestaande VSA-syntax niet breken;
- vóór [parser](@)/rendering gevalideerd worden.

Ongeldig:

```toml
[rendering.svg.wrapping.tokens]
forced-line-break = ["[:]"]
```

Omdat `[:]` al een pitchmarker is.

---

# Rendererdiagnostics

Configvalidatie produceert [diagnostics](@).

Voorbeelden:

| Code                       | Betekenis            |
| -------------------------- | -------------------- |
| `VSA-RENDER-CONFIG-ERROR`  | ongeldige config     |
| `VSA-RENDER-UNKNOWN-THEME` | theme bestaat niet   |
| `VSA-RENDER-INVALID-TOKEN` | token breekt syntax  |
| `VSA-RENDER-INVALID-COLOR` | kleurwaarde ongeldig |

---

# Theme inheritance

Themes mogen erven.

Voorbeeld:

```text
liturgikon-high-contrast
→ liturgikon
→ defaults
```

Theme inheritance gebruikt dezelfde deep-merge regels.

Cyclische theme inheritance is ongeldig.

---

# Future-proofing

Het configuratiemodel moet later uitbreidbaar zijn voor:

- MusicXML;
- SATB;
- editorintegratie;
- interactive SVG;
- printprofielen;
- custom glyphsets.

Nieuwe secties mogen worden toegevoegd zonder bestaande config te breken.

---

# Open ontwerpvragen

Nog nader uit te werken:

- locatie van user override;
- distributie van themes;
- schemaformaat;
- JSON-schema of TOML-schema;
- CLI-optiebeleid;
- theme packaging.



---

## Bron: `docs/spec/vsa-height-markers.md`

# VSA hoogte-markeringen

Status: ontwerpbesluit voor opname in de VSA-specificatie.

## Begrip

Een [hoogte-markering](@) is een positionele markering in een `vsa-notatie`blok.

Voorbeelden:

```vsa
[:]
[/:]
[//:]
[\:]
```

De exacte syntaxis van de markering wordt door de VSA-taalspecificatie bepaald.

## Aantal markeringen

Binnen één `vsa-notatie`blok mogen meerdere [hoogte-markeringen](@) voorkomen.

Voorbeeld:

```vsa
::: vsa-notatie
[:] Heer, ontferm U [/:] over ons [\:]
:::
```

Dit is syntactisch geldig.

## Positie ten opzichte van tekst

Er is geen syntactisch voorschrift over de positie van [hoogte-markeringen](@) ten opzichte van gezongen tekst.

Daarom zijn onder meer geldig:

```vsa
::: vsa-notatie
[:] Heer, ontferm U
:::
```

```vsa
::: vsa-notatie
Heer, ontferm U [:]
:::
```

```vsa
::: vsa-notatie
Heer, [:] ontferm U
:::
```

```vsa
::: vsa-notatie
Heer, [:] ontferm [/:] U [\:]
:::
```

Tekst mag dus voorkomen:

- vóór de eerste [hoogte-markering](@);
- tussen [hoogte-markeringen](@);
- na de laatste [hoogte-markering](@).

## Semantiek

De eerste [hoogte-markering](@) in een `vsa-notatie`blok geeft de beginhoogte aan.

Elke latere [hoogte-markering](@) geeft de zanghoogte aan waar de zang op die positie moet zitten.

Hoogte-markeringen zijn daarmee gewone positionele semantische nodes in de documentstroom, met één aanvullende regel:

```text
eerste hoogte-markering = beginhoogte
latere hoogte-markering = lokale hoogte op die positie
```

## Rendering

Voor SVG-rendering worden alle [hoogte-markeringen](@) op dezelfde manier behandeld.

De [renderer](@) maakt dus geen visueel onderscheid tussen:

- eerste [hoogte-markering](@);
- latere [hoogte-markeringen](@);
- eventueel laatste [hoogte-markering](@).

Rendering is positioneel:

```text
hoogte-markering in bron → hoogte-marker-glyph op die renderpositie
```

## Validatie

De [validator](@) mag semantische controles uitvoeren op [hoogte-markeringen](@), maar mag niet eisen dat:

- de eerste [hoogte-markering](@) helemaal aan het begin staat;
- de laatste [hoogte-markering](@) helemaal aan het eind staat;
- er geen tekst vóór de eerste [hoogte-markering](@) staat;
- er geen tekst na de laatste [hoogte-markering](@) staat.

Wel kan de [validator](@) controleren:

- of [hoogte-markeringen](@) syntactisch geldig zijn;
- of de eerste markering als beginhoogte geïnterpreteerd kan worden;
- of latere markeringen betekenisvol zijn binnen de gekozen toon/semantiek;
- of een expliciete eindmarkering overeenkomt met de berekende eindtoon, zodra eindtooncontrole is gespecificeerd.

Een eindmarkering is optioneel. Het ontbreken van een eindmarkering is dus geen semantische fout.

Een eindmarkering `[:]` is niet leeg in semantische zin: zij betekent neutrale hoogte en is equivalent aan `[-:]` c.q. `[~:]`.

## Implementatieconsequenties

### Parser

De [parser](@) moet [hoogte-markeringen](@) representeren als gewone nodes in de documentstroom.

Niet gewenst:

```text
Document(begin_marker, body, end_marker)
```

Wel gewenst:

```text
Document(nodes=[TextNode, HeightMarkerNode, ScopeNode, ...])
```

of equivalent.

### Validator

De [validator](@) moet [hoogte-markeringen](@) verzamelen uit de documentstroom.

Semantiek:

```text
height_markers = alle HeightMarkerNode nodes in bronvolgorde
start_height = height_markers[0] indien aanwezig
local_heights = height_markers[1:]
```

### SVG-renderer

De [renderer](@) behandelt elke [hoogte-markering](@) hetzelfde.

Daarom hoort rendering niet afhankelijk te zijn van:

- `is_start_marker`;
- `is_end_marker`;
- positie aan begin/eind.

### MusicXML

Voor toekomstige MusicXML-export is waarschijnlijk vooral de eerste [hoogte-markering](@) relevant als startinformatie.

Latere [hoogte-markeringen](@) kunnen later worden gebruikt voor:

- controlepunten;
- pitch hints;
- alignment;
- maat-/regelstructuur;
- melodische validatie.
