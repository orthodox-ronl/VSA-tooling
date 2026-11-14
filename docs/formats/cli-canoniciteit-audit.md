# CLI-canoniciteit-audit (fase 2)

Inventaris van straat-CLI’s t.o.v. C1–C4
([contract-index §Canoniciteit](contract-index.md#canoniciteit-en-conversiegates-c)).
**Alleen audit** — geen code in deze mijlpaal. Fase 3 na expliciete OK.

## Legenda

| Kolom | Betekenis                                                      |
| ----- | -------------------------------------------------------------- |
| C3 nu | Controleert de CLI dat de **bron** canoniek is vóór conversie? |
| C4 nu | Levert/controleert de CLI een **canonieke doel**?              |
| Gap   | Wat ontbreekt t.o.v. C3/C4                                     |

Waarden C3/C4:

| Waarde     | Betekenis                                                             |
| ---------- | --------------------------------------------------------------------- |
| **n.v.t.** | Geen conversie (validate/inspect/schrijfhulp met uitzonderingsstatus) |
| **ext**    | Alleen straat-extensie / invoerfilter                                 |
| **geen**   | Geen canoniciteitsgate                                                |
| **deel**   | Gedeeltelijk (parse faalt hard; of checklist alleen optioneel/los)    |
| **ja**     | Gate aanwezig                                                         |
| **uitz.**  | Bewuste uitzondering (documenteer in man-page)                        |

Prioriteit fase 3 (uit plan): eerst `products` / `mscz` / `text` / `svg` / `audio`.

---

## `vsa` (bron `.vsa`)

| Subcommando                  | Doel               | C3 nu  | C4 nu  | Uitzondering             | Gap                                                      | Prio     |
| ---------------------------- | ------------------ | ------ | ------ | ------------------------ | -------------------------------------------------------- | -------- |
| `validate`                   | rapport            | n.v.t. | n.v.t. | mag niet-canoniek tonen  | —                                                        | —        |
| `parse` / `blocks`           | inspect            | n.v.t. | n.v.t. |                          | —                                                        | —        |
| `syllabify`                  | bron herschrijven  | uitz.  | uitz.  | mag (on)canoniek maken   | man-page noemt C*                                        | laag     |
| `zoektekst`                  | YAML in bron       | ext    | deel   |                          | bron-canoniciteit vóór write?                            | midden   |
| `svg`                        | `.vsa.svg`         | ext    | geen   |                          | C3 syllabificatie/validate; C4 svg-contract              | **hoog** |
| `text`                       | `.lyrics.txt`      | ext    | deel   | strip soft `-` in export | C3 bron; C4 lyrics-contract expliciet                    | **hoog** |
| `mxl` / `musicxml`           | `.mxl`             | ja     | ja     | `--syllabify`; engraving | C4 steekproef na write (mono); engraving slaat C4 over   | —        |
| `mscz`                       | `.mscz`            | ext    | deel   | via MuseScore-keten      | C3; C4 S*/leesbaarheid                                   | **hoog** |
| `score-ir`                   | IR (+ from-ir)     | ja     | ja     | `--allow-noncanonical`   | C4 structureel+emit; nog geen S8-gate                    | midden   |
| `mp3`/`audio`/`ogg`/`wav`    | audio              | ext    | deel   | A5 trim                  | C3; C4 A*                                                | **hoog** |
| `products`                   | universele set     | ja     | ja     | `--allow-noncanonical`   | C4 op mxl-key; overige keys nog geen aparte C4           | midden   |
| `pdf`                        | partituur-PDF      | ext    | deel   | geen standaardproduct    | C3; C4 P*                                                | midden   |
| `mvsa`                       | schets `.vsa.mvsa` | ext    | deel   | T6 waarschuwingen        | C3; C4 T1–T7                                             | midden   |
| `template validate`          | formule-YAML       | n.v.t. | n.v.t. |                          | —                                                        | —        |
| `process` / `build-markdown` | MD-workflow        | deel   | deel   |                          | per blok; documenteer                                    | laag     |
| `resolve-catalogus`          | paden              | n.v.t. | n.v.t. |                          | —                                                        | —        |

---

## `mvsa` (bron `.mvsa`)

| Subcommando                          | Doel                       | C3 nu  | C4 nu  | Uitzondering                     | Gap                        | Prio     |
| ------------------------------------ | -------------------------- | ------ | ------ | -------------------------------- | -------------------------- | -------- |
| `validate`                           | rapport                    | n.v.t. | n.v.t. |                                  | —                          | —        |
| `syllabify`                          | L-tekst                    | uitz.  | uitz.  |                                  | man-page C*                | laag     |
| `normalize` / `kuiser` / `transpose` | bron herschrijven          | ext    | deel   | normalize = naar canonieke vorm  | C4 expliciet; C3 vooraf?   | midden   |
| `mxl`                                | `.mxl`                     | ja     | ja     | translit-as-parts slaat C4 over  | C4 satb na standaard write | —        |
| `mscz`                               | `.mscz`                    | ext    | deel   | layout flags                     | C3; C4 S*                  | **hoog** |
| `svg`                                | `.svg`                     | ext    | deel   | `--engine osmd`                  | C3; C4 mvsa-svg            | **hoog** |
| `pdf`                                | PDF                        | ext    | deel   |                                  | C3; C4 P*                  | midden   |
| `mp3`/`ogg`/`wav`                    | audio                      | ext    | deel   |                                  | C3; C4 A*                  | **hoog** |
| `score-ir`                           | IR (+ from-ir)             | ja     | ja     | `--allow-noncanonical`           | C4 structureel+emit        | midden   |
| `text`                               | lyrics                     | ext    | deel   | strip                            | C3; C4                     | **hoog** |
| `vsa`                                | `.mvsa.vsa`                | ext    | deel   | E*                               | C3; C4 E1–E6               | midden   |
| `products`                           | universele set + key `vsa` | ext    | deel   |                                  | gebundelde gates           | **hoog** |
| `import`                             | → `.mvsa`                  | uitz.  | uitz.  | werkbank = `mscz`/`mxl mvsa`     | man-page                   | —        |

---

## `mscz` (bron `.mscz`)

| Subcommando        | Doel                 | C3 nu  | C4 nu  | Uitzondering           | Gap                                | Prio     |
| ------------------ | -------------------- | ------ | ------ | ---------------------- | ---------------------------------- | -------- |
| `mvsa` / `import`← | werkbank `.mvsa`     | uitz.  | uitz.  | geen catalogus-eis     | man-page                           | —        |
| `import`→          | `.mscz` uit mvsa/mxl | uitz.  | deel   | destination import     |                                    | midden   |
| `mxl`              | `.mxl`               | ja     | ja     | `--allow-noncanonical` | structurele C3 (zip+mscx); geen S* | —        |
| `svg`              | `.svg`               | ja     | deel   | `--allow-noncanonical` | C4 svg-contract                    | midden   |
| `pdf`              | PDF                  | ja     | deel   | `--allow-noncanonical` | C4 P*                              | midden   |
| `mp3`/`ogg`/`wav`  | audio                | ja     | deel   | `--allow-noncanonical` | C4 A*                              | midden   |
| `score-ir`         | IR (+ from-ir)       | ja     | ja     | `--allow-noncanonical` | C4 structureel+emit                | —        |
| `mscz`             | partituur-sibling    | ja     | deel   | `--allow-noncanonical` | C4 S* harder                       | midden   |
| `normalize`        | layout op bestaand   | ext    | deel   | plain = minder         | C3 structureel?; C4 per layout     | midden   |
| `text`             | lyrics               | ja     | deel   | `--allow-noncanonical` | C4                                 | midden   |
| `compare`          | rapport              | n.v.t. | n.v.t. | SCORE mag MusicXML     | —                                  | —        |
| `products`         | universele set       | ja     | ja     | `--allow-noncanonical` | C4 op mxl; structurele C3 bron     | —        |

---

## `mxl` (bron `.mxl` / `.musicxml`)

| Subcommando | Doel               | C3 nu  | C4 nu  | Uitzondering | Gap                | Prio   |
| ----------- | ------------------ | ------ | ------ | ------------ | ------------------ | ------ |
| `validate`  | M* checklist       | n.v.t. | n.v.t. |              | —                  | —      |
| `normalize` | → playback-profiel | ext    | deel   |              | C4 M* na normalize | midden |
| `mvsa`      | werkbank           | uitz.  | uitz.  |              | man-page           | —      |
| `mscz`      | `.mscz`            | ext    | deel   |              | C3; C4 S*          | midden |

---

## `markdown` (bron `.md`)

| Subcommando | Doel                | C3 nu  | C4 nu  | Uitzondering    | Gap                         | Prio |
| ----------- | ------------------- | ------ | ------ | --------------- | --------------------------- | ---- |
| `pdf`       | `index.md.pdf` e.d. | n.v.t. | deel   | geen notatie-P* | pagina-contract bibliotheek | laag |
| `svg`       | VSA-blok-SVG’s      | deel   | deel   |                 | per blok als `.vsa`         | laag |
| `text`      | platte MD-tekst     | n.v.t. | n.v.t. |                 | —                           | —    |

---

## Samenvatting gaps (fase 3-kandidaten)

1. **Geen automatische C3** op product/export-subs: verkeerde/incomplete
   zing-deling of ongeldige bron wordt vaak pas zichtbaar via los
   `validate`, niet als harde weigering vóór schrijven.
2. **C4** leunt op exportcode + steekproef; zelden `mxl validate` /
   checklist-assert ná schrijven in dezelfde CLI-run.
3. **Uitzonderingen** (`validate`, `syllabify`/`--unsyllabify`,
   `--syllabify` op mxl, `import`/werkbank) staan deels in
   [contract-index](contract-index.md); man-pages moeten C3/C4 + uitz.
   noemen (fase 3 docs-sync).
4. **`products`** is de dichtste hefboom: één gate vóór de set dekt
   mxl/mscz/svg/audio/lyrics/score-ir.

### Status fase 3 (deel gedaan)

1. **Gedaan:** `vsa.canonicity_gate` (non-interactieve C3) +
   `--allow-noncanonical`.
2. **Gedaan:** `{straat} products` voor `.vsa`/`.mvsa` + product-subs
   `text` / `mxl` / `svg` / `mp3`/`audio` / `mscz` (vsa+mvsa).
3. **Gedaan:** C4-steekproef na schrijven van playback-``.mxl`` via
   `export_bron_to_mxl` (products) en `vsa`/`mvsa`/`mscz mxl`
   (translit-/engraving-paden uitgezonderd); tests in
   `tests/test_canonicity_gate.py`.
4. **Gedaan:** structurele C3 voor bron-`.mscz` (zip + leesbare
   ``.mscx``) in `mscz products` + product-subs; nog geen S*-bron-gate.
5. **Gedaan:** C4 structureel + from-ir-emit op Score-IR na schrijven
   (`export_mvsa_path_to_score_ir` / products / `{straat} score-ir`).
6. **Gedaan:** man-page `products` + contract-index §C*.
7. **Open:** overige C4-subs (pdf, …); strengere mscz-C3
   (S*/leesbaarheid) na aparte OK.
8. **Open:** bulk-catalogusnaleving (aparte OK).

---

## Zie ook

- [contract-index](contract-index.md) §C* · §Nieuwe regel · §Dekkingsmatrix
- [syllabificatie](syllabificatie.md) · [products-meta](products-meta.md)
- Man-pages: [CLI-overzicht](../reference/cli/index.md)
