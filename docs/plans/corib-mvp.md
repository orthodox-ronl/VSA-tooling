# CoriB MVP — oefenspeler op Score-IR + OSMD (plan)

| Veld            | Waarde                                                                                                                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan; **niet normatief**; stap 0 (inventaris + dit document) klaar; M1–M4 nog open                                                                                                        |
| **Doel**        | Coria-vervanger / oefenspeler (**CoriB**): partij mute/solo, cursor, tempo — op dezelfde schermbrug als koormap                                                                               |
| **Branch**      | Productwerk op **`corib`** (Cursor-regel `.cursor/rules/branch-afstemming.mdc`); PR-richting → `development`                                                                                  |
| **Gerelateerd** | [partituur-ir](partituur-ir.md) §7–§8, [kale-muziek §4](kale-muziek-svg-en-uitgaven.md), [osmd-s8-recite](osmd-s8-recite.md) (afgerond), [gebruikseisen-dragers](gebruikseisen-dragers.md) §5 |

---

## 0. Antwoord eerst

**CoriB** is de oefenspeler die Coria moet vervangen. CoriB tekent niet met
MuseScore en niet met catalogus-Coria-`.mxl`. CoriB gebruikt het afgesproken
schermpad:

```text
.mvsa  →  Score-IR (JSON)  →  MusicXML (uit IR)  →  OSMD (tekenen + oefenen)
```

MVP-kern: **mute/solo per partij**, **cursor** (positie tijdens afspelen),
**tempo** (regelaar + Score-IR/`<sound tempo>`). Eén partituurbeeld; oefenen =
highlight/mute op voices, geen tweede tekenmodel ([partituur-ir](partituur-ir.md)
§3 / §7).

Deze run (stap 0) is alleen inventaris + plan. Geen productcode of UI.

---

## 1. Inventaris (wat al klaar is)

| Bouwsteen                             | Stand                                                                                         | Bron / bewijs                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Score-IR v0.1 + exporter              | gedaan                                                                                        | `mvsa score-ir`; [partituur-ir](partituur-ir.md)                              |
| MusicXML uit Score-IR (from-ir)       | gedaan                                                                                        | `vsa.score_ir_musicxml`; sibling `*.from-ir.musicxml`                         |
| Browser-OSMD (tekenen)                | spike gedaan                                                                                  | `examples/spikes/partituur-browser/`                                          |
| Headless OSMD-SVG                     | spike + CLI                                                                                   | `examples/spikes/partituur-osmd-svg/`; `mvsa svg --engine osmd`               |
| S8-scherm (spacer-marker + adapter)   | afgerond in tooling + bibliotheek                                                             | [osmd-s8-recite](osmd-s8-recite.md)                                           |
| Productiescherm koormap               | from-ir → OSMD voor canonieke `.mvsa`                                                         | [kale-muziek §4](kale-muziek-svg-en-uitgaven.md)                              |
| Style-CLI MuseScore / cue-width       | print/blad; **niet** OSMD-pad                                                                 | MuseScore Style; checklist C6                                                 |
| CoriB-speler (mute/solo/cursor/tempo) | **nog niet**                                                                                  | partituur-ir §8 stap 9                                                        |

**Les uit Coria (M-reeks):** Coria mute/solo werkt op **vier aparte parts**
(checklist M2). Partituur-IR/OSMD tekent **twee balken × twee voices** (S-reeks).
CoriB moet mute/solo dus mappen op OSMD-voices/staves uit from-ir — niet op
Coria-playback-parts.

**Les uit S8:** print-collapse blijft in Score-IR/from-ir; scherm-adapter
verbergt spacer-koppen. Afspelen mag later een andere timingkeuze vragen
(open vraag Q3) — dat is géén reden om terug te vallen op Coria-`.mxl`.

---

## 2. Doelen (MVP)

| Id  | Doel                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------------------- |
| D1  | Laden van Score-IR + from-ir MusicXML in OSMD (zelfde brug als §7)                                            |
| D2  | **Mute** en **solo** per partij S / A / T / B (oefenen één stem tegen de rest)                                |
| D3  | **Cursor**: zichtbare afspeelpositie die meeloopt met de noten/maten                                          |
| D4  | **Tempo**: regelaar; startwaarde uit Score-IR-meta / from-ir `<sound tempo>` waar aanwezig                    |
| D5  | Geluid standaard uit of expliciet starten (geen verrassing; zie [gebruikseisen](gebruikseisen-dragers.md) §5) |

Succes voor “MVP klaar genoeg”: een beheerder kan één bekend `.mvsa`-voorbeeld
(bijv. `1a-vredeslitanie`) openen in een oefen-spike, één partij solo zetten,
tempo wijzigen, en de cursor zien meelopen — zonder MuseScore en zonder
Coria-app.

---

## 3. Non-goals

| Niet in CoriB-MVP                                              | Waarom / waar wel                                                                             |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| MuseScore als scherm- of afspeelmotor                          | Print/blad blijft MuseScore; scherm = OSMD ([kale-muziek §4](kale-muziek-svg-en-uitgaven.md)) |
| Tweede tekenmodel of apart `profile: "oefen"`-JSON als eis     | Zelfde partituurbeeld; oefenen = view op voices (§3 partituur-ir)                             |
| Coria-playback-`.mxl` als broncontract                         | Legacy oefenpad; CoriB voedt zich uit Score-IR (§7)                                           |
| Product-UI in bibliotheek/koormap in dezelfde run als M1       | Eerst spike in tooling; host later (M4)                                                       |
| Pixel-pariteit OSMD ↔ MuseScore-SVG                            | Geen eis (D2-spike toonde al “goed genoeg” voor lyrics/cues)                                  |
| Style-CLI (afstand/fonts/measure-spacing) op OSMD              | MuseScore-printpad; OSMD heeft eigen layout                                                   |
| Catalogus-bulk, `.vsa` zonder Score-IR, cue-SVG-pariteit       | Open rest kale-muziek §4; niet CoriB-MVP                                                      |
| Volledige Coria-featurepariteit (alle workarounds M17–M20)     | Die constraints verdwijnen juist door van Coria af te stappen                                 |
| Native app / offline-bundle                                    | Buiten scope; zie gebruikseisen §3                                                            |

---

## 4. Architectuur (vast uit eerdere plannen)

```text
.mvsa
  → Score-IR  (format score-ir, version 0.1, profile partituur)
  → from-ir MusicXML  (*.mvsa.from-ir.musicxml)
  → OSMD tekenen
  → CoriB: Playback + mute/solo + cursor + tempo
```

| Laag              | Repo / plek (voorstel)                         | Doet                                          |
| ----------------- | ---------------------------------------------- | --------------------------------------------- |
| IR + from-ir      | **VSA-tooling** (bestaand)                     | Contract + export; geen speler-UI             |
| Oefen-spike M1–M3 | **VSA-tooling** `examples/spikes/…`            | Bewijs mute/solo/cursor/tempo                 |
| S8 A1-adapter     | **bibliotheek** + `scripts/osmd-svg`           | Spacer-koppen verbergen; product-CLI én embed |
| Product-host M4   | **open** (bibliotheek / aparte pagina / embed) | Keuze na werkende spike                       |

Versiepoort: onbekende `format` / major `version` weigeren (partituur-ir §7).

Terminologie: `zangstuk-id` → `variant-id` → `uitvoeringsvorm-id` →
`representatie-id`. Schrijf **uitvoeringsvorm** uit (geen afkorting `uv` in
nieuwe docs).

---

## 5. Mijlpalen M1–M4

Eén run = één mijlpaal. Geen MuseScore + OSMD + bibliotheek + CoriB tegelijk.

### M1 — Kleinste werkende oefen-spike

**Doel:** browser-spike die from-ir MusicXML in OSMD laadt **én** afspeelt met
minstens **mute van één partij** (bijv. alleen S hoorbaar of S gedempt).

**In scope:** uitbreiding van of sibling naast
`examples/spikes/partituur-browser/`; één vast voorbeeldstuk; knoppen
play/stop + één mute; korte README.

**Niet in M1:** solo-alle-combinaties, tempo-UI, cursor-graphics, bibliotheek-
embed, S8-adapter-port, audio-polish.

**Acceptatie:** lokaal `python -m http.server` (of gelijkwaardig); hoorbaar
verschil met/zonder mute; statusregel noemt Score-IR-titel.

**Goedkoper formuleren:** «op `corib` — alleen M1 oefen-spike mute; geen
tempo/cursor/bibliotheek».

### M2 — Mute/solo SATB + tempo

**Doel:** mute **en** solo voor S/A/T/B; tempo-regelaar; starttempo uit
Score-IR-meta / from-ir sound-tempo.

**Niet in M2:** cursor meelopen; seek over maten; product-host.

**Acceptatie:** solo A dempt S/T/B; tempo ×0,5 / ×1 / ×1,5 hoorbaar anders;
geen crash op voorbeeld zonder tempo-meta (default vastleggen).

### M3 — Cursor + basis seek

**Doel:** cursor/highlight volgt afspeelpositie; klik of knop naar maat
(minimaal: naar begin maat *n*).

**Niet in M3:** volledige speelplan-navigatie (D.S./coda) tenzij gratis via
bestaande from-ir marks; bibliotheek-productpagina.

**Acceptatie:** bij play beweegt de cursor synchroon genoeg om mee te zingen;
seek naar maat 1 en een latere maat werkt op het voorbeeldstuk.

### M4 — Productgrens + hergebruik

**Doel:** vastleggen waar CoriB woont (spike → herbruikbare module → host in
bibliotheek of aparte oefenpagina); S8 A1-adapter meenemen waar recite speelt;
docs/cross-links; eventueel eerste embed-contract.

**Niet in M4:** catalogus-brede rollout; Coria-export afschaffen; printketen
wijzigen.

**Acceptatie:** één zin “waar draait CoriB in productie?” + werkende koppeling
op één catalogusstuk of demo-host; plan-status bijgewerkt.

---

## 6. Open vragen

| Id  | Vraag                                                                                         | Wanneer beslissen       |
| --- | --------------------------------------------------------------------------------------------- | ----------------------- |
| Q1  | Welke audio-API? (OSMD PlaybackManager / Web Audio / Tone.js / MIDI-out)                      | vóór of in M1           |
| Q2  | Hoe mappen S/A/T/B op OSMD staff/voice in from-ir MusicXML? (regressietest vastleggen)        | M1 (mute) / M2 (solo)   |
| Q3  | Afspelen van S8-recite: print-collapse-timing of lettergreep-per-noot zoals Coria M10?        | vóór M3 op S8-stukken   |
| Q4  | Host van product-CoriB: bibliotheek-oefenmodus, aparte URL, of npm-achtige embed?             | M4                      |
| Q5  | Blijft Coria-`.mxl`-export (M-reeks) tijdens transitie, of alleen Score-IR-pad documenteren?  | M4 / org-besluit        |
| Q6  | Is `profile: "oefen"` ooit een apart Score-IR-document, of blijft het een view-flag?          | later (partituur-ir §9) |
| Q7  | Instrumentklank: piano-default (M8-gewoonte) of neutrale toon?                                | M1 defaults             |

---

## 7. Gefaseerde opdrachtregels (na OK)

| Stap | Opdrachtzin (voorbeeld)                                                                 |
| ---- | --------------------------------------------------------------------------------------- |
| 0    | ~~alleen inventaris + `docs/plans/corib-mvp.md`~~ (deze run)                            |
| M1   | «op `corib` — alleen M1 oefen-spike: OSMD + play + één mute; geen tempo/cursor»         |
| M2   | «op `corib` — alleen M2: mute/solo SATB + tempo; geen cursor/host»                      |
| M3   | «op `corib` — alleen M3: cursor + maat-seek op de spike»                                |
| M4   | «op `corib` — alleen M4: productgrens + één host-koppeling; geen catalogus-bulk»        |

---

## 8. Docs bij deze stap

| Document                         | Actie in stap 0                                      |
| -------------------------------- | ---------------------------------------------------- |
| `docs/plans/corib-mvp.md`        | **nieuw** (dit plan)                                 |
| `docs/plans/README.md`           | rij CoriB-MVP                                        |
| `mkdocs.yml`                     | nav-item onder Plannen                               |
| `docs/plans/partituur-ir.md` §8  | stap 9 → link naar dit plan                          |

Geen man-pagina’s of format-hubs tot er CLI-/productgedrag verandert (M1+).
