# `@`-keywords (draft)

**Status:** draft v0.

**Voor wie:** wie een `.mvsa` typt in VSCode (koorpartituur, litanieën,
antwoorden) en wil weten welke `@`-regels bestaan, wat ze doen, en wanneer je
ze wél of juist níet gebruikt.

Een **keyword-regel** is een regel die (na optionele spaties) begint met `@`,
daarna een keyword, daarna spatie, daarna argumenten die bij dat keyword
horen:

```text
@keyword argumenten…
```

Het keyword zelf volgt: eerste teken een letter, daarna letters, `-` of `_`
(`[A-Za-z][A-Za-z-_]*`). Voorbeelden: `@do`, `@oct`, `@tekst`.

| Soort                          | Gedrag                                                                                         |
| ------------------------------ | ---------------------------------------------------------------------------------------------- |
| **Gedefinieerd** (deze pagina) | Tooling kent de betekenis; foute argumenten → **error**                                        |
| **Onbekend** (nog niet hier)   | Mag je gebruiken om te experimenteren; validate meldt een **warning**, geen error              |
| **Ongeldige keyword-vorm**     | Bijv. `@1foo` of `@` alleen → **warning** (geen error); export gaat door                       |
| **`@---`**                     | Optionele no-op-scheider tussen LSATB-systemen (lege regel volstaat); commentaar erna OK       |

Keyword-regels mogen:

- bovenaan het bestand;
- bij het begin van een sectie (vóór of na `@sectie`);
- **tussen** LSATB-systemen van dezelfde sectie.

Ze mogen **niet** midden in een LSATB-systeem (tussen `L:` en `S:`).

Overzicht van de sticky tooncontext (`@do` / `@mode` / `@oct`): ook
[Semantiek](semantics.md#directives-do-mode-oct). Hieronder per keyword:
wat het is, wat je ermee kunt, en wanneer je het wel/niet gebruikt.

---

## `@do`

**Wat het is.** Zet de grondtoon van de
[do-context](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md)
voor het eerstvolgende LSATB-systeem (en verder, tot je `@do` opnieuw zet).

**Vorm.** `@do` + spatie + toonnaam met octaaf, bv. `F4`, `G4`, `Bb3`.

**Wel gebruiken** als het stuk niet in de default F4 staat, of als je midden in
een bestand van toonsoort/grondtoon wisselt vóór een nieuw systeem.

**Niet gebruiken** om per noot te “tunen”: dat doe je met laddergraden of
toonnamen op de stemregels. `@do` is document-/sectie-context, geen lokale
correctie.

**Default** als je `@do` weglaat: `F4`.

```text
@do F4
```

---

## `@mode`

**Wat het is.** Zet de modus (majeur/mineur) die bij de do-context hoort,
geldig vanaf het eerstvolgende LSATB-systeem.

**Vorm.** `@mode major` of `@mode minor`.

**Wel gebruiken** samen met `@do` als je mineur nodig hebt, of als je wilt
vastleggen dat het stuk majeur is (expliciet, voor lezers en export).

**Niet gebruiken** voor kerktoon / toonnummer (“toon 8”): dat is metadata
buiten deze keywords (nog geen apart keyword) of hoort in de bestandsnaam /
catalogus.

**Default:** `major`.

```text
@mode major
```

---

## `@oct`

**Wat het is.** Zet per stem het **schrijfoctaaf**: hoe hoog een laddergraad
zonder octaafsuffix, en een toonnaam a–g **zonder** wetenschappelijk cijfer,
klinkt t.o.v. `@do`. Typisch: bas en tenor één octaaf lager schrijven (`B=-1`,
`T=-1`), zodat je `re` / `d` typt in plaats van `re-` / `d-`.

**Vorm.** `@oct` + spatiescheidende toekenningen `Stem=n`, bv.
`@oct S=0 A=0 T=-1 B=-1`.

**Wel gebruiken** bij SATB met laddergraden of kale a–g, zodat elke stem in een
comfortabel schrijfoctaaf blijft. Kale a–g delen het **do-octaaf**
(`[schrijf-do, +12)`): bij `@do F4` is `c` = C5.

**Niet gebruiken** om één losse noot te verschuiven: gebruik dan een
octaafsuffix op die noot (`so-`, `fa+`, `c+`), of een wetenschappelijke toonnaam
(`g3`, `c5`). Wetenschappelijke cijfers (`g3`) negeren `@oct`.

**Default:** `0` voor elke stem die je niet noemt.

```text
@oct S=0 A=0 T=-1 B=-1
```

Zie [Semantiek — schrijfoctaaf](semantics.md#schrijfoctaaf).

---

## `@start`

**Wat het is.** Zet beginankers (EHM) per stem voor relatieve hoogtestijl,
geldig vanaf het eerstvolgende LSATB-systeem.

**Vorm.** `@start` + toekenningen, bv. `@start S=- A=\3 T=\6 B=\8`.

**Wel gebruiken** als je relatieve (vsa-achtige) hoogte wilt zonder EHM in elke
regelidentifier te herhalen.

**Niet gebruiken** als voorkeur boven de identifier-vorm: `S-:` / `T\6:` op de
stemregel zelf is meestal duidelijker (anker zit bij de stem). `@start` en
`S-:` betekenen voor die stem hetzelfde beginanker; de identifier wint als
beide voorkomen.

---

## `@sectie`

**Wat het is.** Opent een nieuwe **sectie** met een id. Een sectie is een
muzikale eenheid van een of meer LSATB-systemen — in bestanden **zonder**
`@speelplan`.

**Vorm.** `@sectie` + spatie + id: `[a-z][a-z0-9_-]*` (kleine letters).

**Sectie-einde.** Canoniek eindigt de vorige sectie met `||` (of `:||`) op alle
lyrics-/stemregels. Een nieuwe `@sectie` **sluit de vorige sectie ook impliciet
af** als die nog open stond (toegestaan, niet-canoniek — validate mag warnen
met `MVSA-SECTIE-IMPLICIT`). Zelfde warning bij **EOF** van een open sectie of
anonieme sectie. Zie [Syntax — sectie-einde](syntax.md#einde).

**Wel gebruiken** om delen te benoemen die je apart wilt exporteren
(`vsa mvsa musicxml … --section id`) of om schetsen in één experiment-bestand
uit elkaar te houden (couplet / refrein / pitch-variant).

**Niet gebruiken** samen met `@speelplan` (dan: `@blok`). Niet als litanie-cue
(dat is `@tekst`). Niet om meerdere speelplannen in één file te nesten — één
plan = één `.mvsa`.

```text
@sectie openingsfrase
```

---

## `@blok`

**Wat het is.** Opent een **speelblok**: genoemd LSATB-segment voor een
`@speelplan`. Geen “sectie” in de zin van `||`-afsluiting; tussen blokken is
`||` niet verplicht.

**Vorm.** `@blok` + spatie + id: `[1-9][0-9]*` **of** `[a-z][a-z0-9_-]*`.

**Wel gebruiken** wanneer je een speelplan hebt: elk blok één keer, volgorde in
`@speelplan`. Eén speelplan per bestand.

**Niet gebruiken** i.p.v. `@tekst` of `@mscz-newline`; niet i.p.v. `@sectie`
buiten een speelplan-bestand (tenzij je redactioneel een id wilt zonder plan).

Zie [Speelplan](speelplan.md).

```text
@blok 1
```

---

## `@speelplan`

**Wat het is.** Zet de **canonieke klinkende volgorde** van speelblokken.
Bladmuziek (MSCZ) blijft compact (volta / herhaling / D.S. of expand);
MXL-playback schrijft het plan uit.

**Vorm.** `@speelplan` + komma-gescheiden ids (zelfde id-vorm als `@blok`).
Hoogstens **één** per bestand — nest geen plan in `@sectie`.

**Wel gebruiken** bij vaste herhaalpatronen (bijv. alleluia 1-2-1-2-1-3).

**Niet gebruiken** samen met `|:` / `:|` in die speelblokken; niet naast
`@sectie` in hetzelfde bestand.

Zie [Speelplan](speelplan.md).

```text
@speelplan 1, 2, 1, 2, 1, 3
```

---

## `@title`

**Wat het is.** Zet de **titel van het stuk** zoals die op het blad en in
export (MusicXML / MuseScore) verschijnt. Geen staff-tekst bij een systeem,
maar de partituurtitel.

**Vorm.** `@title` + spatie + een string tussen **dubbele** aanhalingstekens
(zelfde stringvorm als `@tekst`):

```text
@title "(1a) Vredeslitanie"
```

**Wel gebruiken** bovenaan het bestand (of bij een duidelijke wissel van stuk)
als de bestandsnaam niet de gewenste titel is. Bij export wint `@title` van de
bestandsnaam als fallback.

**Niet gebruiken** voor:

- cues boven één koorantwoord — dat is `@tekst`;
- sectie-ids voor export (`--section`) — dat is `@sectie`;
- gezongen tekst — dat hoort op `L:`.

Zet je `@title` meer dan eens, dan geldt de **laatste** waarde in het bestand.
Bij export naar `.mscz` zet tooling de titel expliciet als MuseScore-
`workTitle` én als Title-tekst in het kopkader (MusicXML-import laat dat
veld soms leeg).

---

## `@tekst`

**Wat het is.** Zet een **zichtbare tekstregel** boven het **eerstvolgende**
LSATB-systeem. Bij export naar MuseScore (`.mscz`) wordt dat system-tekst
boven de bovenste notenbalk, uitgelijnd aan het begin van die maat
(niet midden boven de eerste noot). Typisch: priestercue of rubriek vóór een
koorantwoord.

**Vorm.** `@tekst` + spatie + een string tussen **dubbele** aanhalingstekens:

```text
@tekst "P: Gezegend … der eeuwen"
```

Binnen de string: `\"` voor een aanhalingsteken, `\\` voor een backslash.

**Wel gebruiken** voor korte cues die op het blad bij dat systeem horen
(litanie: “P: …”, “D: …”, een korte rubriek). Zet de regel **direct boven** het
LSATB-blok waarop de tekst moet verschijnen.

**Niet gebruiken** voor:

- de gezongen tekst — die hoort op de lyrics-regel (`L:`);
- de titel van het hele stuk — gebruik `@title`;
- sticky context zoals toonsoort — gebruik `@do` / `@mode` / `@oct`.

**Gedrag t.o.v. systemen.** `@tekst` is **niet** sticky: de tekst geldt alleen
voor het eerstvolgende LSATB-systeem. Meerdere `@tekst`-regels vóór hetzelfde
systeem worden onder elkaar gezet (zelfde volgorde als in het bestand). Staat
`@tekst` aan het eind zonder volgend systeem → **warning**.

`@tekst` forceert **geen** nieuw MuseScore-systeem. Wil je wél een nieuwe
regel in de partituur, zet dan `@mscz-newline` (eventueel samen met `@tekst`).
De cue staat boven de ge-cue-de maat. Op het **partituur/MSCZ**-pad: als die
maat **niet** het begin van een MuseScore-systeem is, sluit export de vorige
maat af met een **dubbele maatstreep** (behalve als daar al een herhaalstreep
`:|` / `:||` staat — die blijft zichtbaar) en zet de cue als SystemText.
Geen mid-systeem-HBox en geen spacermaat: MuseScore tekent daar een accolade
middenin het systeem of een leeg stuk notenbalk. Wil je wél een duidelijke
regelsprong, gebruik `@mscz-newline`. Canonieke MSCZ-eisen:
[checklist S14–S19](../formats/canonical-checklists.md#checklist-mscz-partituur-musescore)
en [leesbaarheid — cues](../formats/mscz-leesbaarheid.md#c--cues-gaps-hbox-accolade).
Op het **playback/MXL**-pad (Coria): vóór
elke mid-flow `@tekst` (niet de eerste maat van het stuk) komt dezelfde
`[PAUZE]`-maat als na `||` — whole-rest met lyric `[PAUZE]`, cue erboven.
Staat er al een sectie-eindestreep (`||` / `:||`) vóór die cue, dan geen
tweede pauze. Herhaalstrepen (`:|`) blijven intact.

Lange cues met `...` worden op **twee regels** gezet: de tweede regel begint bij `...`. Is de cue breder dan de maat, dan krijgt die maat minstens die breedte (MusicXML `width` / MuseScore-maat).

```text
@mscz-newline
@tekst "P: Laat ons de Heer in vrede bidden"
L:  Heer ont-ferm_ U__  ||
S:  a    -   -     -    ||
A:  f    -   -     -    ||
T:  c    -   -     -    ||
B:  f    -   c     f    ||
```

---

## `@mscz-newline`

**Wat het is.** Geeft aan dat bij **mvsa → `.mscz`**-conversie het
**eerstvolgende** LSATB-systeem als **nieuw MuseScore-systeem** moet beginnen
(nieuwe regelsprong op het blad). Heeft geen effect op de gezongen inhoud;
alleen layout.

**Vorm.** Alleen het keyword, zonder argumenten:

```text
@mscz-newline
```

**Wel gebruiken** als een antwoord, couplet of cue op een **nieuwe regel** van
de partituur moet staan (bijv. litanie-antwoorden onder elkaar, of een
duidelijke visuele breuk vóór een nieuw blok). Vaak samen met `@tekst`:

```text
@mscz-newline
@tekst "P: Gezegend … der eeuwen"
L: A_-men_ |
…
```

**Niet gebruiken** voor:

- cues zonder regelsprong — alleen `@tekst` volstaat (export zet desnoods een
  dubbele maatstreep vóór de cue);
- sectiegrenzen in de bron — dat is `||` / `@sectie`;
- scheiding van vscode-blokken zonder MSCZ-layout — dan volstaat een **lege
  regel** (optioneel `@---` met commentaar).

**Gedrag.** Geldt alleen voor het eerstvolgende LSATB-systeem (niet sticky).
Op het eerste systeem van de partituur is een explicit new-system overbodig
(dat systeem begint al). Staat `@mscz-newline` zonder volgend systeem →
**warning**. Ongeldig met argumenten → **error**.

Op het partituur/MSCZ-pad: export zet `<print new-system="yes"/>` op de eerste
maat van dat systeem. Op playback/MXL is de markering aanwezig maar voor Coria
niet bedoeld als layout-sturing.

---

## Document-metadata (titel, personen, bron)

Deze keywords zetten **partituur-metadata** (bovenaan of in MuseScore-info),
niet cues bij een LSATB-systeem. Vorm steeds: quoted string, laatste waarde in
het bestand wint. `@title` staat hierboven apart uitgelegd; dezelfde stringvorm
geldt voor de keywords hieronder.

### Actief (gaan mee naar MusicXML / MuseScore)

| Keyword         | Voorbeeld                            | MusicXML                      | MuseScore-meta |
| --------------- | ------------------------------------ | ----------------------------- | -------------- |
| `@title`        | `@title "(1a) Vredeslitanie"`        | `<work-title>`                | titel          |
| `@ondertitel`   | `@ondertitel "Litanie van de vrede"` | `<movement-title>`            | `subtitle`     |
| `@composer`     | `@composer "Archimandriet Feofan"`   | `<creator type="composer">`   | `composer`     |
| `@tekstdichter` | `@tekstdichter "…"`                  | `<creator type="lyricist">`   | `lyricist`     |
| `@arrangeur`    | `@arrangeur "bew. Hemelum"`          | `<creator type="arranger">`   | `arranger`     |
| `@vertaler`     | `@vertaler "NL: …"`                  | `<creator type="translator">` | `translator`   |
| `@bron`         | `@bron "Liturgikon, p.147-149"`      | `<source>`                    | `source`       |
| `@copyright`    | `@copyright "CC BY-SA 4.0 — …"`      | `<rights>` (+ footer/colofon) | `copyright`    |

**`@composer`.** Naam of aanduiding van de **componist** (of traditionele
toeschrijving), zoals die rechtsboven op het blad / in MuseScore-info
verschijnt. Gebruik dit **niet** voor het boek of blad waar je uit overneemt —
dat is `@bron`.

```text
@composer "Archimandriet Feofan"
```

**`@bron`.** Referentie naar de **bron van de partituur** (boek, bladzijden,
uitgave), zodat je later terug kunt vinden waar deze notatie vandaan komt.
Gaat mee in **beide** exportpaden:

- MusicXML (playback/Coria én partituur): `<identification><source>…</source>`
- MuseScore/MSCZ: meta-tag `source`

**Op het MSCZ-blad:** MuseScore toont meta `source` niet automatisch in de kop.
Zonder `@tekstdichter` zet de MSCZ-export daarom `@bron` ook als
**lyricist-tekst** in de kop (`bron: …`), zodat de herkomst op papier zichtbaar
is. Heb je wél een echte tekstdichter, dan wint `@tekstdichter` voor die plek;
`@bron` blijft dan alleen in meta/`<source>`.

Optionele schrijfwijze met dubbele punt na het keyword: `@bron: "…"` ≡
`@bron "…"`. Let op: `bron:` *in* een quoted string (bv.
`@tekstdichter "bron: koormap …"`) is gewoon tekst — dat is geen keyword en
geeft geen warning.

```text
@bron "Liturgikon, p.147-149"
```

**`@ondertitel`.** Ondertitel onder de hoofdtitel (bv. liturgische aanduiding).
Gaat mee in partituur/MSCZ (`movement-title` / MuseScore `subtitle`); Coria-
playback behoudt die tag (geen sanitize-strip).

**`@tekstdichter` / `@arrangeur` / `@vertaler`.** Personenrollen naast de
componist; zelfde stringvorm. Alleen zetten als je die rol echt kent.
`@tekstdichter` verschijnt op het MSCZ-blad (lyricist-plek). Wil je daar de
partituurbron tonen, gebruik bij voorkeur alleen `@bron` (zie hierboven); een
expliciete `@tekstdichter "bron: …"` mag nog steeds en wint dan voor die
bladplek.

**`@copyright`.** Bronnotice voor footer (kort) en colofon (volledig) in
`.mscz`, en `<rights>` in MusicXML. Zonder `@copyright` gebruikt MSCZ-export
een default (CC BY-SA 4.0 + eredienst-zin).

Bibliotheek-id komt **niet** uit een `@`-keyword: tooling leidt die af uit het
pad onder `bibliotheek/…` bij export.

### Gereserveerd (nog niet in praktisch gebruik)

Deze keywords mag je al zetten (geen warning); validate controleert alleen de
stringvorm. Export naar MusicXML/MSCZ **negeert** ze voorlopig — zodat de
namen vastliggen voor later gebruik.

| Keyword        | Bedoeling                                                           | Voorbeeld                        |
| -------------- | ------------------------------------------------------------------- | -------------------------------- |
| `@toon`        | Kerktoon / oktoechos-nummer van het zangstuk                        | `@toon "8"`                      |
| `@taal`        | Taal van de gezongen tekst                                          | `@taal "nl"`                     |
| `@genre`       | Soort zangstuk (litanie, tropaar, …) voor catalogus/filters         | `@genre "litanie"`               |
| `@opmerkingen` | Redactionele notities voor de bewerker (niet bedoeld als bladtekst) | `@opmerkingen "nog controleren"` |

**Niet gebruiken** als vervanging van `@tekst` (zichtbare cue) of `#`-commentaar
voor tijdelijke tipjes in de bron — `@opmerkingen` is voor blijvende metadata
zodra tooling die gaat tonen.

---

## `@---`

**Wat het is.** Optionele **no-op** die een LSATB-systeem afbreekt — hetzelfde
effect als een **lege regel**. Voor een gewone scheiding tussen vscode-systemen
volstaat die lege regel; `@---` is vooral handig als je bij de scheiding
**commentaar op dezelfde regel** wilt (`@--- tweede couplet`). Voor een
**nieuwe MuseScore-regel** op het blad: gebruik `@mscz-newline`, niet alleen
`@---` of een lege regel.

**Vorm.** `@---` of `@ ---`. Optioneel **commentaar** erna op dezelfde regel
(wordt genegeerd, geen error/warning), bv. `@--- tweede systeem` of
`@ --- zie Liturgikon p.12`.

**Gewone scheiding** (voorkeur: lege regel):

```text
L: Heer_ … |
S: a     … |

L: Heer_ … ||
S: a     … ||
```

**Wel `@---` gebruiken** als je commentaar wilt meenemen bij de scheiding:

```text
L: Heer_ … |
S: a     … |
…

@--- volgende couplet

L: Heer_ … ||
S: a     … ||
…
```

**Niet gebruiken** als zichtbare inhoud op het blad — daarvoor is `@tekst`.
Ook niet als vervanging van `@mscz-newline` (dat forceert de MSCZ-regelsprong).
Zonder commentaar is `@---` overbodig naast een lege regel.

---

## Onbekende keywords

Alles wat de vorm van een keyword heeft maar **niet** in de lijst hierboven
staat (bijv. `@voices`) mag je zetten om te experimenteren.
`vsa mvsa validate` geeft een **warning** (`MVSA-DIRECTIVE`), geen error:
export en verdere verwerking gaan door. Ongeldige keyword-vormen (bijv.
`@1foo`) geven eveneens een **warning**. Zodra een keyword officieel wordt,
komt het op deze pagina met vaste argumenten en gedrag.
