# mvsa schrijven 101

!!! note "Voor wie / wanneer"
    **Voor:** wie een meerstemmig zangstuk in `.mvsa` wil typen (uit bladmuziek,
    uit eenstemmige VSA, of vanaf nul).
    **Wanneer:** je de draft-spec nog niet uit je hoofd kent, maar wél iets
    werkends wilt opschrijven en valideren.
    **Niet:** de volledige formele grammatica — die staat in
    [specification-mvsa](../specification-mvsa/README.md).

**Antwoord in het kort:** een `.mvsa`-bestand is een tekstpartituur: eerst
lyrics (`L:`), daaronder stemhoogten (`S:` / `A:` / `T:` / `B:`), met optionele
`@`-regels voor toonsoort en schrijfoctaaf. Je houdt L en stemmen **synchroon**
op lettergrepen/slots; daarna `vsa mvsa validate` en eventueel export naar
MusicXML of MuseScore.

## Leeswijzer

| Hoofdstuk                                                 | Als je wilt …                                      |
| --------------------------------------------------------- | -------------------------------------------------- |
| [Minimaal bestand](#1-minimaal-bestand)                   | meteen iets zien dat valideert                     |
| [`@`-woorden](#2--woorden-die-je-het-meest-nodig-hebt)    | toonsoort, octaaf, secties, cues begrijpen         |
| [L-regels](#3-l-regels-schrijven)                         | tekst, duur, recite, melisma typen                 |
| [Stemregels](#4-stemregels-vsa-doremi-of-ag)              | notatie kiezen en mixen                            |
| [Octaven](#5-octaven-oct-do-octaaf-en-cijfers)            | `@oct`, kale a–g, bladcijfers                      |
| [Ankers](#6-ankers-begin-en-eind)                         | pitch-markers aan begin/eind van een systeem       |
| [Taak: bladmuziek → mvsa](#7-taak-bladmuziek--mvsa)       | partituur of MusicXML omzetten                     |
| [Taak: VSA meerstemmig](#8-taak-vsa-meerstemmig-maken)    | eenstemmige VSA uitzetten naar SATB                |
| [Controleren en exporteren](#9-controleren-en-exporteren) | validate / mxl / mscz                              |

Volledige keyword-lijst: [Keywords (`@…`)](../specification-mvsa/keywords.md).
Voorbeelden in de repo: [`examples/mvsa/`](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa).

---

## 1. Minimaal bestand

```text
@do F4
@mode major

@sectie voorbeeld
L: Hei_ li_ ge_ ||
S: do   re   mi ||
A: la-  ti-  do ||
T: fa-  so-  la- ||
B: do-  re-  mi- ||
```

Elk **LSATB-systeem** is één blok: `L:` plus de stemregels die bij die frase
horen, afgesloten met dezelfde maatstrepen (`|` of `||`) op alle regels.
Zet **geen lege regel** tussen `L:` en de stemmen — een lege regel **eindigt**
het systeem. Tussen twee systemen: een **lege regel** (voorkeur), of
een `@-` directive, zoals `@---` met commentaar.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa validate examples\mvsa
```

---

## 2. `@`-woorden die je het meest nodig hebt

Een `@`-regel begint (na spaties) met `@` + keyword + argumenten. Zulke regels
horen **vóór** of **tussen** LSATB-systemen — niet tussen `L:` en `S:`.

| Keyword          | Doet kort gezegd                                                         | Default / tip        |
| ---------------- | ------------------------------------------------------------------------ | -------------------- |
| `@do`            | Grondtoon van de do-context (`F4`, `G4`, …)                              | `F4`                 |
| `@mode`          | `major` of `minor`                                                       | `major`              |
| `@oct`           | Schrijfoctaaf per stem (`S=0 A=0 T=-1 B=-1`)                             | overal `0`           |
| `@sectie`        | Label voor een stuk (export `--section`); **niet** bij `@speelplan`      | —                    |
| `@blok`          | Speelblok-id voor `@speelplan` (één plan per bestand)                    | zie speelplan-spec   |
| `@speelplan`     | Klinkende volgorde van blokken (Coria uitgeschreven; blad compact)       | hoogstens één/file   |
| `@start`         | Beginanker (EHM) per stem; liever vaak `S-:` / `T\6:` op de stemregel    | —                    |
| `@tekst`         | Cue / systeembrontekst (priesterregel, …) boven het volgende systeem     | —                    |
| `@title`         | Titel van het zangstuk (MusicXML `<work-title>`, MuseScore-titel)        | bestandsnaam         |
| `@bron`          | Bron van de partituur (boek/koormap); MusicXML `<source>`, Coria-info    | —                    |
| `@composer` e.d. | Metadata (componist, copyright, ondertitel, …)                           | zie keywords-lijst   |

Sticky: `@do` / `@mode` / `@oct` gelden vanaf het **eerstvolgende** LSATB-systeem
tot je ze opnieuw zet. Systemen scheiden doe je met een **lege regel**; `@---`
is alleen nodig als je commentaar op die scheidingsregel wilt.

??? tip "Voorbeeld: typische SATB-kop"
    ```text
    @title "Alleluia - Toon 1"
    @bron "koormap Hemelum"
    @do F4
    @mode major
    @oct S=0 A=0 T=-1 B=-1

    @sectie alleluia
    L: (Al-le-lu-ia)-le ||
    S: fa            so- ||
    …
    ```

Complete lijst (wel/niet gebruiken, vorm, onbekende keywords):
[Keywords (`@…`)](../specification-mvsa/keywords.md). Speelplan en bladvorm:
[Speelplan](../specification-mvsa/speelplan.md) — één `@speelplan` per
`.mvsa`; `@sectie` alleen in bestanden zonder speelplan.

---

## 3. L-regels schrijven

De `L:`-regel is de **telling**: lettergrepen, ELM-duur, recite en melisma.
Stemregels moeten daar **slot voor slot** op aansluiten.

| Op de L-regel              | Betekenis                                              |
| -------------------------- | ------------------------------------------------------ |
| `Hei` / `li-ge`            | lettergreep; `-` = woordstreepje tussen lettergrepen   |
| `_` `=` `__` `~` …         | ELM (duur) direct na lettergreep of na `)`             |
| `( … )`                    | recite-groep (meerdere lettergrepen, één toonhoogte)   |
| `&`                        | melisma: extra toon op dezelfde lettergreep            |
| `\|` / `\|\|` / `\|:` …    | maatstreep (zelfde vorm op alle stemregels)            |

### Sync L ↔ stemmen

1. Tel op de L-regel de **slots** (lettergrepen + melisma-`&`-stukken).
2. Zet op elke stemregel **evenveel** hoogte-stukken (gescheiden door spaties).
3. Zet op elke regel dezelfde maatstrepen op dezelfde plekken.
4. Spaties mogen kolommen uitlijnen; `vsa mvsa kuiser` (of `normalize`) helpt
   bij uitlijning en eenduidige maatstrepen.

??? example "Recite + melisma (schets)"
    ```text
    L: (Al-le-lu-ia, Al)-le-lu_&-&-&_ i_ a__ ||
    S: Bb                c  a&f&g&a   Bb a  ||
    ```

    De haakjes `( … )` markeren recite. Op S staat één toon (`Bb`) voor de hele
    recite-groep; daarna `c`, dan een melisma `a&f&g&a`, enz.

Handige check:

```cmd
vsa mvsa validate pad\naar\lied.mvsa
```

Uitlijnen en kuiser-toleranties (in-place; behoud spelling):

```cmd
vsa mvsa kuiser pad\naar\lied.mvsa
```

Alleen kolomuitlijning / pitch-herschrijf (schrijft default
`<stem>.normalized.mvsa`):

```cmd
vsa mvsa normalize pad\naar\lied.mvsa -o pad\naar\lied.mvsa
```

---

## 4. Stemregels: vsa, doremi of a–g

Op `S:` / `A:` / `T:` / `B:` schrijf je **hoogte**. Drie stijlen mogen door
elkaar (per frase één stijl is leesbaarder).

| Stijl         | Voorbeelden                         | Wanneer handig                                      |
| ------------- | ----------------------------------- | --------------------------------------------------- |
| **doremi**    | `do` `re` `fa#` `so-`               | denken in ladder t.o.v. `@do`                       |
| **a–g**       | `f` `bb` `c` of `bb4` `c5`          | dicht bij bladmuziek; kale letter = do-octaaf       |
| **vsa (EHM)** | `/` `\2` `-` `#\`                   | stappen t.o.v. de lopende toon (relatief typen)     |

### CLI-namen (`--pitch`)

Bij `import` / `normalize` kies je een **doelspelling**:

| `--pitch`    | Schrijft …                                              |
| ------------ | ------------------------------------------------------- |
| `doremi`     | laddergraden                                            |
| `a-g`        | toonnamen met **wetenschappelijk cijfer** (`bb4`, `c5`) |
| `vsa`        | eerste toon absoluut, daarna EHM                        |
| `preserve`   | (alleen normalize) bronspelling behouden — **default**  |

`abc` blijft een **alias** van `a-g` (oude scripts).

```cmd
vsa mvsa import lied.mxl -o lied.mvsa --pitch doremi
vsa mvsa normalize lied.mvsa --pitch a-g -o lied.ag.mvsa
```

### Handige mix: anker absoluut, sprongen in EHM

Begin met een vaste toon (doremi of a–g), ga daarna relatief verder:

```text
S: Bb /  \2 / - ||
```

Of met regelidentifier als beginanker:

```text
S-: / \2 / fa ||
```

`S-:` zet de lopende toon op “zelfde toon als schrijf-do-anker `-`”; daarna
EHM’s. Zie [Semantiek — absolute en relatieve hoogte](../specification-mvsa/semantics.md#absolute-en-relatieve-hoogte).

??? tip "Welke stijl kiezen?"
| Situatie                         | Suggestie                                      |
| -------------------------------- | ---------------------------------------------- |
| Overname van MuseScore / MXL     | import `--pitch doremi` of `a-g` (cijfers)     |
| Liturgische ladder / toon        | doremi + `@oct`                                |
| Snelle schets, bekende melodie   | a–g zonder cijfer (do-octaaf) of mix + EHM     |
| Lange stapsgewijze frase         | EHM na één absoluut anker                      |

---

## 5. Octaven: `@oct`, do-octaaf en cijfers

### Schrijfoctaaf (`@oct`)

`@oct T=-1 B=-1` verschuift het **schrijf-do** van tenor/bas. Je typt dan `re`
i.p.v. `re-`. Suffix `-` / `+` telt **extra** t.o.v. dat schrijfoctaaf.

Typisch SATB in F:

```text
@do F4
@oct S=0 A=0 T=-1 B=-1
```

### Do-octaaf (doremi én kale a–g)

Zonder cijfer liggen laddergraden **en** kale toonnamen a–g in het
**do-octaaf**: halfopen interval vanaf het schrijf-do tot één octaaf hoger.

Bij `@do F4` (schrijfoctaaf 0):

| doremi | a–g (kale letter) | Klinkend |
| ------ | ----------------- | -------- |
| `do`   | `f`               | F4       |
| `re`   | `g`               | G4       |
| `mi`   | `a`               | A4       |
| `fa`   | `bb` / `Bb`       | Bb4      |
| `so`   | `c`               | **C5**   |
| `la`   | `d`               | D5       |
| `si`   | `e`               | E5       |

**Belangrijk:** kale `c` is C5 (= `so`), **niet** C4. De wrap ligt bij **do**,
niet bij de wetenschappelijke C. Zo blijven `so` en `c` pitch-equivalent.

### Wetenschappelijk cijfer (bladcijfers)

`bb4`, `c5`, `g3` zijn absoluut (wrap bij **C**) en **negeren** `@oct`. Handig
bij overname van bladmuziek. `c4` is C4; `c` zonder cijfer blijft C5.

??? example "Zelfde bas, twee schrijfwijzen"
    Met `@oct B=-1`:

    ```text
    B: g  g  e- f&d-&c-&f g a ||
    ```

    Met bladcijfers (geen `@oct` nodig voor die tonen):

    ```text
    B: g3 g3 e3 f3&d3&c3&f3 g3 a3 ||
    ```

Uitgebreider: [Semantiek — schrijfoctaaf](../specification-mvsa/semantics.md#schrijfoctaaf)
en [Syntax — toonnamen (a–g)](../specification-mvsa/syntax.md#toonnamen-ag).

---

## 6. Ankers: begin en eind

| Plaats                          | Rol                                      | Voorbeeld        |
| ------------------------------- | ---------------------------------------- | ---------------- |
| EHM in regelidentifier          | **zet** beginanker                       | `S-:`, `T\6:`    |
| `@start S=- …`                  | zelfde als identifier, sticky            | `@start S=-`     |
| Laddergraad / toonnaam in regel | zet lopende toon                         | `… mi \|`        |
| Token **aan** de maatstreep     | **checkt** alleen (wijzigt niet)         | `\|mi`, `\|/`    |

Gebruik eindankers om vergissingen te vangen: als de lopende toon niet matcht,
faalt validate.

```text
S: fa so- mi&do&re&mi fa mi ||mi
```

---

## 7. Taak: bladmuziek → mvsa

**Doel:** een bestaande partituur (MusicXML / MuseScore) als tekstbron.

1. Exporteer of bewaar als `.mxl` / `.mscz`.
2. Importeer naar `.mvsa` met een pitch-vorm:
   ```cmd
   cd /d C:\Git\orthodox-ronl\VSA-tooling
   vsa mvsa import bron.mxl -o lied.mvsa --pitch doremi
   ```
   Of `--pitch a-g` als je bladcijfers wilt (`bb4`, `c5`).
3. Zet bovenaan `@do` / `@mode` / `@oct` goed (import vult dit grotendeels in).
4. Controleer L-tekst (import kan lelijk syllabificeren) en sync.
5. `vsa mvsa validate lied.mvsa`
6. Optioneel opnieuw kuisen: `vsa mvsa kuiser lied.mvsa`

Referentie-voorbeeld (bladcijfers):
[`kleine-intocht-zondag-hemelum.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/kleine-intocht-zondag-hemelum.mvsa).

??? tip "Van MuseScore-scherm naar tekst"
    - Noteer per stem de **reeks tonen** en markeer recite/melisma op de tekst.
    - Kies één octaafstijl per frase: of `@oct` + kale doremi/a–g, of overal
      cijfers — mix in één frase mag, maar is lastiger te lezen.
    - Lange recite (`n ≥ 6`) wordt bij partituur-export automatisch
      1–(n−2)–1 geprint; in de `.mvsa`-bron schrijf je gewoon één toon per
      lettergreep in de recite-groep.

---

## 8. Taak: VSA meerstemmig maken

**Doel:** een eenstemmige `.vsa`-melodie uitzetten naar L + SATB.

1. Zet de VSA-tekst om naar een `L:`-regel (lettergrepen, ELM, recite-haakjes).
2. Zet de sopraanmelodie op `S:` — vaak eerst absoluut (doremi of a–g), of
   relatief met `S-:` + EHM’s zoals in de VSA-hoogtemarkers.
3. Vul A/T/B in (harmonie). Gebruik `@oct` zodat bas/tenor comfortabel typen.
4. Houd maatstrepen en slot-telling gelijk aan L.
5. Valideer; exporteer een sectie om te beluisteren:
   ```cmd
   vsa mvsa mscz lied.mvsa -o generated\lied.mscz --section mijn-sectie
   ```

Pitch-equivalentie tussen stijlen kun je afdwingen door te normaliseren en te
vergelijken (MusicXML-pitches moeten gelijk blijven):

```cmd
vsa mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch doremi -o generated\a.doremi.mvsa
vsa mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\a.ag.mvsa
```

Voorbeeld met meerdere equivalente schetsen:
[`alleluia-toon-8.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/alleluia-toon-8.mvsa).

---

## 9. Controleren en exporteren

| Stap               | Commando (voorbeeld)                                      |
| ------------------ | --------------------------------------------------------- |
| Valideren          | `vsa mvsa validate lied.mvsa`                             |
| MusicXML           | `vsa mvsa musicxml lied.mvsa -o generated\lied.mxl`       |
| MuseScore          | `vsa mvsa mscz lied.mvsa -o generated\lied.mscz`          |
| Eén sectie         | voeg `--section sectie-id` toe                            |
| Uitlijnen / kuisen | `vsa mvsa kuiser lied.mvsa`                               |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa validate examples\mvsa\alleluia-toon-8.mvsa
vsa mvsa musicxml examples\mvsa\alleluia-toon-8.mvsa --section schets3-oct-ag -o generated\alleluia-ag.mxl
```

CLI-detail: [mvsa-referentie](../reference/cli/mvsa.md). Formaten-hub:
[Formaten & CLI](../formats/index.md).

---

## Veelgemaakte beginnersfouten

| Fout                                      | Wat er misgaat                         | Richting                                      |
| ----------------------------------------- | -------------------------------------- | --------------------------------------------- |
| `@do` tussen `L:` en `S:`                 | keyword midden in systeem              | `@`-regels vóór of tussen systemen            |
| Lege regel tussen `L:` en `S:`            | systeem eindigt te vroeg               | geen lege regels binnen één LSATB-blok        |
| Kale `c` verwachten als C4 bij `@do F4`   | do-octaaf → C5                         | schrijf `c4` of `c-` / `so-` voor C4          |
| Verschillende maatstrepen op L vs S | sync-fout | zelfde ` | ` / ` |     | ` op alle regels |
| Recite zonder `( … )`        | elke lettergreep aparte toon nodig | haakjes om de recite-groep |
| `+` als kruis op laddergraad | `+` = octaaf                       | schrijf `fa#` of `fis`     |
| `b` voor Bes                 | `b` = toonnaam B                   | Bes = `bb` / `Bb` / `bes`  |

---

## Zie ook

| Pagina                                                                                      | Rol                 |
| ------------------------------------------------------------------------------------------- | ------------------- |
| [specification-mvsa](../specification-mvsa/README.md)                                       | Normatieve draft    |
| [Keywords](../specification-mvsa/keywords.md)                                               | Alle `@`-regels     |
| [Syntax](../specification-mvsa/syntax.md) · [Semantiek](../specification-mvsa/semantics.md) | L, stemmen, octaven |
| [mvsa-conversies](../plans/mvsa-conversions.md)                                             | import / normalize  |
| [`.mvsa` formaat](../formats/mvsa.md)                                                       | Korte formaatpagina |
| [CLI-taken](cli-taken.md)                                                                   | Welk `vsa`-commando |
