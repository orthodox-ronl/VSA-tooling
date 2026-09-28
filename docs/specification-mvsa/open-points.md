# Open punten (mvsa) — centrale backlog

**Canonieke plek** voor restpunten rond mvsa (syntax, tooling, docs,
conversies). Voorheen verspreid over deze pagina,
`examples/mvsa/ISSUES.md` en `examples/mvsa/TOPICS.md`.

Conversiematrix en afgeronde slices:
[`docs/plans/mvsa-conversions.md`](../plans/mvsa-conversions.md).
Werkplan-restpunten syntax (geschiedenis):
[`docs/plans/mvsa-v0-syntax.md` §10](../plans/mvsa-v0-syntax.md).

---

## Nu (eerstvolgende tooling)

*(leeg — volgende werk uit [Backlog](#backlog-bewust-later))*

Lokaal bouwen van voorbeelden (validate / normalize / mxl / mscz / pdf):
`examples/mvsa/make.cmd` (PDF via `mvsa pdf`).

---

## Backlog (bewust later)

### Syntax en semantiek

| Punt                                    | Toelichting                                                                    | Richting                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| Speelplan fase 2c                       | D.S. al Coda / geneste jumps; verfijnen expand-heuristiek                      | Na volta + D.S. al Fine ([speelplan.md](speelplan.md))                         |
| Blokhergebruik                          | Secties of stemmen hergebruiken (`@voices`, deelbereiken)                      | Experiment: `examples/mvsa/trisagion-8a-slav-hemelum.mvsa`                     |
| Overlays t.o.v. S                       | A/T/B als afwijking van de sopraan                                             | Later                                                                          |
| Zichtbare vs. structurele standaardtoon | Oude polyfonie-`~`/`-`-glyph; mag niet opnieuw `~` heten                       | Later                                                                          |
| Batch-tekst buiten bestand              | Veel teksten op één stemgrid                                                   | Alleen als corpuswerk het vraagt                                               |
| Chromatische `+` in eenstemmige VSA-EHM | Los van mvsa-laddergraden (waar `+` = octaaf)                                  | Via VSA 1.0-spec                                                               |

### Markdown-pipeline en fences

| Punt                              | Toelichting                                                                                                                                                          | Richting                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `::: mvsa-notatie` / `::: mvsa`   | Markdown-blok met mvsa; aliases `::: vsa` / `::: mvsa`; sluitende `:::` = sectie-einde zoals EOF; tekst tussen laatste maatstreep en `:::` = warning/fout            | Spec + parse + `build-markdown` / includes    |
| `::: vsa-notatie` in `.vsa`       | Optioneel fence in `.vsa`: zonder fence = kale VSA (nu); mét fence = buiten fence in principe commentaar (later metadata)                                            | Eenstemmige VSA-tooling                       |

### Tooling / conversies

| Punt                 | Toelichting                                                                                                                                | Richting                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Kuiser-tool          | **Gedrag** staat in [syntax](syntax.md) / [semantiek](semantics.md); **implementatie** nog niet                                            | Tool boven `normalize` / `align_mvsa_columns`                                                                   |
| Bibliotheek-id API   | Consumer bepaalt de id; tooling moet een **expliciete** optie bieden om id in colofon/meta te zetten (pad-sniffen is hoogstens hulpmiddel) | CLI/export-API; zie [reuse — ownership](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer)           |
| MSCZ-layoutprofielen | Meerdere layouts/conventies → **benoemde, gedocumenteerde** keuzes; tools naleven die                                                      | CLI-keuze + docs ([mscz-leesbaarheid](../formats/mscz-leesbaarheid.md))                                         |
| MIDI-export          | `.mvsa` (en evt. andere bronnen) → `.mid` / `.midi` voor afspelen                                                                          | [formats/midi.md](../formats/midi.md); CLI-naam nog open                                                        |
| Exports / gebruik    | Gebruikseisen-dragers → welke exportvormen (web, print, …) voor litanie-/samenstellingsdocumenten                                          | [status-en-roadmap](../status-en-roadmap.md) stap 1; [gebruikseisen-dragers](../plans/gebruikseisen-dragers.md) |
| TEv2 docs-opschonen  | TermRefs / glossaries van de grond af opschonen en bijwerken                                                                               | Apart traject; geen ad-hoc fixes in mvsa-PRs                                                                    |

---

## Klaar (niet opnieuw openen)

| Punt             | Stand                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| Parser / CLI     | Top-level `mvsa` / `mxl` / `mscz` + `vsa mvsa …` (conversions stap 5)                               |
| Conversieslices  | normalize, mscz-export, import, bron-commands — zie conversions-plan                                |
| `mvsa pdf`       | `.mvsa`/`.mscz` → MuseScore-PDF; `make.cmd` gebruikt `mvsa pdf`                                     |
| Validate-output  | Succes → één `OK` (geen per-bestand `…: OK`); zoals `vsa validate`                                  |
| Sectie-einde     | Bij EOF / nieuwe `@sectie` / (later) fence: laatste maatstreep = einde; geen `MVSA-SECTIE-IMPLICIT` |
| Experiment-PDF   | Checklist P1–P5; copyright-footer P4 blijft “later”                                                 |

---

## Wrappers en andere repo's

- Windows: `scripts\mvsa.cmd`, `scripts\mxl.cmd`, `scripts\mscz.cmd` (blijven).
- Consumer-install + ownership (tooling vs product/CI):
  [reuse-vsa-tooling](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).
- **bibliotheek** (en andere consumers): geen fork van tooling-scripts; dunne
  wrappers die de gepubliceerde CLI aanroepen. Productpipelines en Hugo-site-CI
  horen in die repo’s, niet hier.
