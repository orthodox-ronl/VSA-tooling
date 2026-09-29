# Open punten (mvsa) — centrale backlog

**Canonieke plek** voor restpunten rond mvsa (syntax, tooling, docs,
conversies). Voorheen verspreid over deze pagina,
`examples/mvsa/ISSUES.md` en `examples/mvsa/TOPICS.md`.

Conversiematrix en afgeronde slices:
[`docs/plans/mvsa-conversions.md`](../plans/mvsa-conversions.md).
Werkplan-restpunten syntax (geschiedenis):
[`docs/plans/mvsa-v0-syntax.md` §10](../plans/mvsa-v0-syntax.md).

Repo-breed kompas (niet alleen mvsa):
[`docs/status-en-roadmap.md`](../status-en-roadmap.md).

---

## Nu (eerstvolgende tooling)

*(leeg — volgende werk uit [Backlog](#backlog-bewust-later))*

Lokaal bouwen van voorbeelden (validate / normalize / mxl / mscz / pdf / audio):
`examples/mvsa/make.cmd` (PDF via `mvsa pdf`; audio via `mvsa audio`).

---

## Backlog (bewust later)

### Syntax en semantiek

| Punt                                    | Toelichting                                                                    | Richting                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| Speelplan: geneste combinatie-jumps     | D.S./D.C. al Coda is klaar; volta+D.S. e.d. zonder één bladpatroon → expand    | [speelplan.md](speelplan.md) «Bewust later»                                    |
| Blokhergebruik                          | Secties of stemmen hergebruiken (`@voices`, deelbereiken)                      | Experiment: `examples/mvsa/trisagion-8a-slav-hemelum.mvsa`                     |
| Overlays t.o.v. S                       | A/T/B als afwijking van de sopraan                                             | Later                                                                          |
| Zichtbare vs. structurele standaardtoon | Oude polyfonie-`~`/`-`-glyph; mag niet opnieuw `~` heten                       | Later                                                                          |
| Batch-tekst buiten bestand              | Veel teksten op één stemgrid                                                   | Alleen als corpuswerk het vraagt                                               |

### Markdown-pipeline en fences

| Punt                              | Toelichting                                                                                                                                                          | Richting                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `::: mvsa-notatie` / `::: mvsa`   | Markdown-blok met mvsa; aliases `::: vsa` / `::: mvsa`; sluitende `:::` = sectie-einde zoals EOF; tekst tussen laatste maatstreep en `:::` = warning/fout            | Spec + parse + `build-markdown` / includes    |
| `::: vsa-notatie` in `.vsa`       | Optioneel fence in `.vsa`: zonder fence = kale VSA (nu); mét fence = buiten fence in principe commentaar (later metadata)                                            | Eenstemmige VSA-tooling                       |

### Tooling / conversies

| Punt                 | Toelichting                                                                                                                                | Richting                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Kuiser-tool          | **Gedrag** staat in [syntax](syntax.md) / [semantiek](semantics.md); **implementatie** nog niet als één CLI (`normalize` + align bestaan)  | Tool boven `normalize` / `align_mvsa_columns`                                                                        |
| Exports / gebruik    | Gebruikseisen-dragers → welke exportvormen (web, print, …) voor litanie-/samenstellingsdocumenten                                          | [gebruikseisen-dragers](../plans/gebruikseisen-dragers.md); repo-backlog `docs/status-en-roadmap.md` (niet op Pages) |
| TEv2 docs-opschonen  | TermRefs / glossaries van de grond af opschonen en bijwerken                                                                               | Apart traject; geen ad-hoc fixes in mvsa-PRs                                                                         |

---

## Klaar (niet opnieuw openen)

| Punt                                  | Stand                                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Parser / CLI                          | Top-level `mvsa` / `mxl` / `mscz` + `vsa mvsa …` (conversions stap 5)                               |
| Conversieslices                       | normalize, mscz-export, import, bron-commands — zie conversions-plan                                |
| `mvsa pdf`                            | `.mvsa`/`.mscz` → MuseScore-PDF; `make.cmd` gebruikt `mvsa pdf`                                     |
| `vsa`/`mvsa audio`                    | Preview-``.mp3`` via MuseScore; zie [formats/audio.md](../formats/audio.md)                         |
| Los MIDI-bestand                      | **Niet gepland** — preview-luisteren dekt de use case; zie [formats/midi.md](../formats/midi.md)    |
| Speelplan volta + D.S. al Fine / Coda | Partituur-nav: volta, D.S./D.C. al Fine, D.S./D.C. al Coda; MXL expansie; tests                     |
| Laddergraad `+`/`-` = octaaf          | Mvsa-keuze vastgelegd (kruis via `#`/`b`); chromatische `+` in eenstemmige VSA-EHM → VSA-spec       |
| Validate-output                       | Succes → één `OK` (geen per-bestand `…: OK`); zoals `vsa validate`                                  |
| Sectie-einde                          | Bij EOF / nieuwe `@sectie` / (later) fence: laatste maatstreep = einde; geen `MVSA-SECTIE-IMPLICIT` |
| MSCZ-layout + id                      | `--layout {partituur,plain}`; `--bibliotheek-id` (expliciet; pad = fallback)                        |
| Experiment-PDF                        | Checklist P1–P5; copyright-footer P4 blijft “later”                                                 |

---

## Wrappers en andere repo's

- Windows: `scripts\mvsa.cmd`, `scripts\mxl.cmd`, `scripts\mscz.cmd` (blijven).
- Consumer-install + ownership (tooling vs product/CI):
  [reuse-vsa-tooling](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).
- **bibliotheek** (en andere consumers): geen fork van tooling-scripts; dunne
  wrappers die de gepubliceerde CLI aanroepen. Productpipelines en Hugo-site-CI
  horen in die repo’s, niet hier. Afspeelknop / `:::include mp3-player` = consumer
  (artefact: `vsa audio`).
