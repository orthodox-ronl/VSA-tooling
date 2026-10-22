# Score-IR / partituur-IR — contract (stap 1)

| Veld            | Waarde                                                                                                                                                           |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan; **niet normatief**; stap 1–5 gedaan (IR, OSMD-via-IR, score-ir, koormap-SVG)                                                                            |
| **Doel**        | Vastleggen wat het JSON-achtige tussenmodel bevat dat schermrenderer (koormap-SVG) én CoriB voedt — zonder MuseScore als schermmotor                             |
| **Eigenaar**    | Export uit `.mvsa` → IR: [VSA-tooling](@bron); consumptie: bibliotheek (shortcode `muziek`) + CoriB                                                              |
| **Gerelateerd** | [canonical-checklists](../formats/canonical-checklists.md) (S-reeks = layoutdoel), [uitvoeraanwijzingen](../specification-mvsa/uitvoeraanwijzingen.md), `@tekst` |

Contract + [`vsa mvsa score-ir`](../reference/cli/mvsa.md#vsa-mvsa-score-ir). Schema-validator en schermrenderer: later.

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
- Geen speelplan-navigatie als verplicht veld (mag later).
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

| Regel              | Eis                                                                             |
| ------------------ | ------------------------------------------------------------------------------- |
| Balken             | Twee: boven = S+A (G), onder = T+B (F)                                          |
| Voices             | Per balk twee: S/T stok omhoog, A/B omlaag                                      |
| Lyrics             | Primair tussen de balken (niet 4× herhaald)                                     |
| `@tekst`           | Boven het systeem, geankerd aan de **gecue-de maat**                            |
| Recite (scherm v1) | Eén klinkende noot per lettergreep is genoeg; print-collapse is optioneel later |

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
  cues: [ Cue, … ]              # @tekst die bij déze maat hoort (vaak 0 of 1)
  lyrics: [ LyricPos, … ]       # gedeelde L-lijn voor partituur
  voices: { S, A, T, B }        # elk: [ VoiceEvent, … ] synchroon in de maat
```

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
  duration: { type, dots?, divisions? }   # of canonieke ELM-token
  lyricIndex?: number                     # index in measure.lyrics (eerste noot van melisma)
  melisma?: { extend: bool, slur?: bool, tie?: bool }
  recite?: bool
  marks?: { … }                           # stubs ok in v0.1
```

`hold` = continue toon zonder nieuwe aanslag (mvsa `-` op stem). Melisma-tekst alleen op het event met `lyricIndex`.

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
vsa mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o generated\score-ir\1a-vredeslitanie.score-ir.json
```

Default sibling-naam: `lied.mvsa.score-ir.json`. Module: `vsa.score_ir`.

---

## 6. Relatie tot bestaande exports

| Pad                         | Rol t.o.v. Score-IR                                            |
| --------------------------- | -------------------------------------------------------------- |
| `.mvsa` → partituur-`.mxl`  | Blijft MuseScore-import / tijdelijke schermbron                |
| `.mvsa` → `.mscz` / PDF     | Blad / bewerken; niet de gedeelde schermmotor                  |
| `.mvsa` → Score-IR          | **`vsa mvsa score-ir`** (v0.1 partituur); input voor SVG/CoriB |
| Coria-playback-`.mxl`       | Legacy oefenpad; niet het partituur-IR-model                   |

Hulptekst: in IR als lyric-laag `"2"` (later); **niet** als nep-extra-stemparts.

---

## 7. Volgende stappen

1. ~~IR-contract + voorbeeld~~
2. ~~Spike: partituur-MXL in de browser + cues~~ (`examples/spikes/partituur-browser/`)
3. ~~Exporter `.mvsa` → Score-IR v0.1~~ (`vsa mvsa score-ir`, tests)
4. ~~Koormap-SVG (MuseScore-brug)~~ — [`vsa mvsa svg`](../reference/cli/mvsa.md#vsa-mvsa-svg) / [mvsa-svg](../formats/mvsa-svg.md)
5. ~~Score-IR → MusicXML → OSMD~~ — `vsa.score_ir_musicxml`, spike `examples/spikes/partituur-browser/`, CLI ``--musicxml``
6. CoriB-MVP (speler op Score-IR / OSMD-brug) — later

---

## 8. Open punten

- Duurencoding: **ELM-tokens** gekozen in v0.1 (`duration.elm`).
- Recite-print-collapse in IR of alleen in print-profiel?
- Meerdere cues op één maat; cues midden in een maat (nu: alleen measure-start).
- Of `profile: "oefen"` een apart document is of een view-flag op hetzelfde bestand.
