# Score-IR / partituur-IR — contract (stap 1)

| Veld            | Waarde                                                                                                                                                           |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan; **niet normatief**; stap 1–5 + schermbrug-contract (§7) gedaan; CoriB-MVP en site-embed nog open                                                       |
| **Doel**        | Vastleggen wat het JSON-achtige tussenmodel bevat dat schermrenderer (koormap-SVG) én CoriB voedt — zonder MuseScore als schermmotor                             |
| **Eigenaar**    | Export uit `.mvsa` → IR: [VSA-tooling](@bron); consumptie: bibliotheek (shortcode `muziek`) + CoriB                                                              |
| **Gerelateerd** | [contract-index](../formats/contract-index.md), [canonical-checklists](../formats/canonical-checklists.md) (S-reeks = layoutdoel), [uitvoeraanwijzingen](../specification-mvsa/uitvoeraanwijzingen.md), `@tekst` |

Contract + [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir). Schema-validator en schermrenderer: later.

---

## 0. Wat is IR? (kort)

**IR** = *intermediate representation* = **tussenmodel**.

```text
.mvsa  →  Score-IR (JSON)  →  tekenen / afspelen / SVG
```

| Term             | Betekenis                                                                                                      |
| ---------------- | -------------------------------------------------------------------------------------------------------------- |
| **Score-IR**     | Het bestandsformaat / contract (noten, tekst, cues, …)                                                         |
| **partituur-IR** | Score-IR met layoutbedoeling **partituur**: SA+TB op twee balken, lyrics tussenin, `@tekst` erboven (S-reeks)  |
| **oefen-IR**     | Latere variant/profiel: zelfde noten, andere presentatie (partij-focus); **niet** in stap 1                    |

Bron blijft `.mvsa`. MusicXML/MSCZ blijven exportpaden voor MuseScore/print; Score-IR is het pad voor **gedeelde schermweergave**.

---

## 1. Doelen en non-goals

### Doelen (stap 1)

- Eén machineleesbaar model dat genoeg is om **partituur op scherm** te tekenen.
- `@tekst`-cues als eersteklas ankers (niet alleen MuseScore-SystemText).
- Ruimte laten voor latere hulptekst (lyric-laag 2) en uitvoeraanwijzingen **zonder** het model om te gooien.
- Scheiding: **inhoud** hier; **pagina** (A4, marges, colofon) elders.

### Non-goals (stap 1)

- Geen complete MusicXML-vervanging.
- Geen VSA-glyph-laag op lyrics (later).
- Speelplan-navigatie is optioneel per maat (`ending` / `repeatTimes` /
  `navigation`); aanwezig wanneer bladvorm dat vraagt.
- Geen audio-instrumentatie als kern (CoriB mag defaults kiezen).
- Geen implementatie van exporter of renderer in dit document.

---

## 2. Wat hoort erin / wat niet

| In Score-IR (ja)                          | Niet in Score-IR (nee)                                      |
| ----------------------------------------- | ----------------------------------------------------------- |
| Toonsoort / `@do`-context                 | Paginaformaat, marges, “vul A4”                             |
| Maten + maatstreepstijl                   | Titelblok / copyright / colofon als layout                  |
| Stemevents S/A/T/B (toon, duur, hold)     | Partijnamen op de balk (S-reeks: uit)                       |
| Lyrics per positie (laag 1; laag 2 later) | Print-only recite-truc als *enige* model (`\|\|O\|\|`)      |
| Melisma / extend-info                     | MuseScore-specifieke XML                                    |
| `@tekst` met anker op maat                | Losse “spacer-maten” alleen voor layout                     |
| Optioneel: marks (adem, dyn, …) stubs     | Coria-workaround-parts voor hulptekst                       |

Metadata die wél nuttig is om het stuk te *herkennen* (ids, korte titel voor UI) mag in een `meta`-blok — dat is geen bladlayout.

---

## 3. Layoutprofiel `partituur`

Canonieke schermbedoeling (gelijk aan checklist S2–S5, S15, S19):

| Regel              | Eis                                                                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Balken             | Twee: boven = S+A (G), onder = T+B (F)                                                                                                                             |
| Voices             | Per balk twee: S/T stok omhoog, A/B omlaag                                                                                                                         |
| Lyrics             | Primair tussen de balken (niet 4× herhaald)                                                                                                                        |
| `@tekst`           | Boven het systeem, geankerd aan de **gecue-de maat**                                                                                                               |
| Recite / melisma   | Zelfde **print-eindvorm** als S8/S13: lange recite 1–(n−2)–1; same-pitch melisma compact (gestipt waar kan). Coria-playback (M10) blijft één noot per lettergreep. |

CoriB gebruikt **hetzelfde** partituurbeeld; oefenen = highlight/mute op voices, geen tweede tekenmodel.

---

## 4. Kernstructuur (conceptueel)

Versieveld verplicht zodat CoriB/bibliotheek kunnen weigeren bij onbekende major.

```text
ScoreDocument
  format: "score-ir"
  version: "0.1"
  profile: "partituur"          # later ook "oefen"
  meta: { … }                   # ids, optionele weergavetitel — geen A4-layout
  pitchContext: { do, mode, octaves? }
  measures: [ Measure, … ]
```

### 4.1 Measure

```text
Measure
  id: string                    # stabiel binnen document, bv. "m1"
  bar: { left?, right }         # single | light-light | light-heavy | repeat-…
  ending?: { start?, stop? }    # volta-nummers (MusicXML ``<ending>``)
  repeatTimes?: number          # alleen bij herhaal > 2×
  navigation?: [ string, … ]    # segno | fine | to_coda | coda | ds_al_* | dc_al_*
  cues: [ Cue, … ]              # @tekst die bij déze maat hoort (vaak 0 of 1)
  lyrics: [ LyricPos, … ]       # gedeelde L-lijn voor partituur
  voices: { S, A, T, B }        # elk: [ VoiceEvent, … ] synchroon in de maat
```

Speelplan-bladvorm (volta / herhaal / D.S. / coda) volgt
`docs/specification-mvsa/speelplan.md` en dezelfde helpers als partituur-MusicXML;
from-ir emitteert de navigatiemarkeringen voor OSMD.

**Sync-regel:** binnen één maat is het aantal *lengte-posities* op `lyrics` gelijk aan het aantal events per stem die meezingen (holds/melisma zoals in `.mvsa` / huidige export). Exacte telling volgt de bestaande L↔SATB-validator; IR exporteert al-uitgelijnde events.

### 4.2 Cue (`@tekst`)

```text
Cue
  kind: "tekst"
  text: string                  # bronstring zonder @tekst-syntax
  anchor: "measure-start"       # v0.1: alleen begin van deze maat
```

Geen mid-systeem-HBox, geen spookmaat: anker = maat-id + `measure-start`.

### 4.3 LyricPos

```text
LyricPos
  syllables: [ { text, syllabic } ]   # single|begin|middle|end
  layers?: { "1": …, "2": … }         # v0.1: alleen laag "1" verplicht; "2" = hulptekst later
  marksBefore?: [ MarkRef ]
  marksAfter?: [ MarkRef ]
  recite?: bool
```

### 4.4 VoiceEvent

```text
VoiceEvent
  pitch: { step, alter?, octave } | "rest" | "hold"
  duration: { elm }                       # canonieke ELM-token
  lyricIndex?: number                     # index in measure.lyrics (eerste noot van melisma)
  melisma?: {
    extend?: bool
    slurStart?: bool, slurStop?: bool
    tieStart?: bool, tieStop?: bool
  }
  recite?: bool
  print?: { spacer?: bool, stemless?: bool, breveHead?: bool }  # S8
  marks?: { … }                           # stubs ok in v0.1
```

`hold` = continue toon zonder nieuwe aanslag (mvsa `-` op stem). Melisma-tekst alleen op het event met `lyricIndex`.

**S8 in IR:** na partituur-collapse blijven midden-events met `print.breveHead`
(stokloze `||O||`) en `print.spacer` (onzichtbare kop, zichtbare lyric).
from-ir MusicXML: spacers → `notehead none` + `stem none`; midden →
`notehead breve` + `stem none` (geen `type=breve`). **A1:** `notehead none`
is scherm-**marker** voor de OSMD-adapter; OSMD tekent die kop niet vanzelf
weg — zie [osmd-s8-recite](osmd-s8-recite.md).

**S13 in IR:** same-pitch melisma al als compacte (gestipte) noot waar
representeerbaar — OSMD-eindvorm, niet de MuseScore-import I1-tie-keten.

### 4.5 meta (mag wel / mag niet)

| Veld (voorstel)              | Mag | Opmerking                                      |
| ---------------------------- | --- | ---------------------------------------------- |
| `bibliotheekId` / pad-ids    | ja  | zangstuk / variant / uitvoeringsvorm           |
| `title` (korte UI-string)    | ja  | niet verplicht tekenen als kop op de SVG       |
| `sourceLabel`                | ja  | herkomst; geen colofon-layout                  |
| `page`, `margins`, `colofon` | nee | hoort bij print/compositie in bibliotheek      |

---

## 5. Voorbeeld

Handvoorbeeld (illustratief):

[`examples/mvsa/partituur-ir-mini.example.json`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/partituur-ir-mini.example.json)

CLI-export (zelfde keten als partituur-MusicXML-events):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a-vredeslitanie.score-ir.json
```

Default siblings: `lied.mvsa.score-ir.json`; met ``--musicxml`` ook
`lied.mvsa.from-ir.musicxml`. Module: `vsa.score_ir`.

---

## 6. Relatie tot bestaande exports

| Pad                         | Rol t.o.v. Score-IR                                            |
| --------------------------- | -------------------------------------------------------------- |
| `.mvsa` → partituur-`.mxl`  | Blijft MuseScore-import / tijdelijke schermbron                |
| `.mvsa` → `.mscz` / PDF     | Blad / bewerken; niet de gedeelde schermmotor                  |
| `.mvsa` → Score-IR          | **`mvsa score-ir`** (v0.1 partituur); input voor SVG/CoriB     |
| Coria-playback-`.mxl`       | Legacy oefenpad; niet het partituur-IR-model                   |

Hulptekst: in IR als lyric-laag `"2"` (later); **niet** als nep-extra-stemparts.

---

## 7. Scherm- en CoriB-brug

Gedeelde **productieschermketen** (geen MuseScore als schermmotor):

```text
.mvsa  →  Score-IR (JSON)  →  MusicXML (uit IR)  →  OSMD (tekenen)
```

| Consument                         | Wat laden                                                                 | Tekenen                                      |
| --------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------- |
| Koormap / shortcode `muziek`      | Score-IR **of** MusicXML die uit die Score-IR komt (`--musicxml`)         | OSMD op die MusicXML                         |
| CoriB (later, MVP)                | Zelfde Score-IR als broncontract; tekenen via dezelfde OSMD-brug          | Highlight/mute op voices; geen tweede model  |

**Versiepoort:** weiger onbekende `format` / major van `version` (nu
`format: "score-ir"`, `version: "0.1"`). Zie §4.

**Sibling-artifacts** (canonieke namen naast `lied.mvsa`):

| Bestand                        | Rol                                      |
| ------------------------------ | ---------------------------------------- |
| `lied.mvsa.score-ir.json`      | Score-IR v0.1                            |
| `lied.mvsa.from-ir.musicxml`   | Partituur-MusicXML **uit** die Score-IR  |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir lied.mvsa --musicxml
mvsa score-ir map-met-mvsa --musicxml
```

**Bewijs (spike, geen product-UI):** `examples/spikes/partituur-browser/`
(OSMD in de browser); optioneel headless SVG:
`examples/spikes/partituur-osmd-svg/`.

**Non-goals van deze brug:**

- Geen MuseScore-paginamodel op de site; geen tall MuseScore-scherm-SVG als
  hoofdpad ([kale-muziek §4](kale-muziek-svg-en-uitgaven.md)).
- Geen tweede tekenmodel naast OSMD-uit-IR voor CoriB.
- Geen CoriB-product-UI in VSA-tooling; alleen dit consumptiecontract.
- Print/blad blijft MuseScore (`mvsa svg` bladreeks, MSCZ, pagina-pdf).

**Klaar genoeg voor CoriB later:** Score-IR v0.1 + MusicXML-uit-IR + OSMD is
het afgesproken aansluitpunt; CoriB bouwt speler/oefenen daarop, niet op
catalogus-MXL of MuseScore-SVG.

---

## 8. Volgende stappen

1. ~~IR-contract + voorbeeld~~
2. ~~Spike: partituur-MXL in de browser + cues~~ (`examples/spikes/partituur-browser/`)
3. ~~Exporter `.mvsa` → Score-IR v0.1~~ (`mvsa score-ir`, tests)
4. ~~Koormap-SVG (MuseScore-brug)~~ — [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg) / [mvsa-svg](../formats/mvsa-svg.md)
5. ~~Score-IR → MusicXML → OSMD~~ — `vsa.score_ir_musicxml`, spike `examples/spikes/partituur-browser/`, CLI ``--musicxml``
6. ~~Scherm-/CoriB-brugcontract~~ (§7; richting Score-IR/OSMD vast in
   [kale-muziek §4](kale-muziek-svg-en-uitgaven.md))
7. ~~**Productiescherm** (mvsa / S8)~~ — bibliotheek from-ir → OSMD; S8 A1
   ([osmd-s8-recite](osmd-s8-recite.md)); rest kale-muziek §4 (`.vsa`, CoriB, …)
8. CoriB-MVP (speler op §7-brug) — later

---

## 9. Open punten

- Duurencoding: **ELM-tokens** gekozen in v0.1 (`duration.elm`).
- ~~Recite-print-collapse in IR of alleen in print-profiel?~~ → in IR + from-ir
  (S8/S13; zie §3–§4.4).
- Meerdere cues op één maat; cues midden in een maat (nu: alleen measure-start).
- Of `profile: "oefen"` een apart document is of een view-flag op hetzelfde bestand.
