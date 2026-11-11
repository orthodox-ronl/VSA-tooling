# Contract-index (canonieke afspraken)

**Start hier** als je export, normalize, layout, Score-IR/from-ir, OSMD,
**of VSA+template→MVSA** (`vsa mvsa` / mapper / emit) aanraakt. Normatieve
regels staan **alleen** in de hubs hieronder. Elders (man-pages, plans,
bibliotheek-specs) **linken** — niet herformuleren.

## Regels

1. Wijzig een afspraak alleen in de canonieke hub; elders alleen een link.
2. Elke CLI, test of consumer-doc die gedrag raakt noemt het **contract-id**
   (checklistregel of layoutprofiel), niet alleen een vrije samenvatting.
3. Kanalen (Coria-`.mxl`, MuseScore-`.mscz`, Score-IR, from-ir, OSMD) delen
   dezelfde **bedoelde** print-/recite-/melisma-vorm; alleen de *emit* mag
   per kanaal verschillen als de hub dat zo scheidt (bijv. M10 vs R5).
4. `normalize` / `products` / `import` **implementeren** deze hubs; ze
   definiëren geen parallelle norm.
5. Een **standaardproduct** heeft één contract. De **bronstraat** (`vsa` /
   `mvsa` / `mscz`) bepaalt alleen de CLI-prefix en toegestane
   invoerextensie. Elk standaardproduct moet uit elke notatiebron
   (`.vsa` / `.mvsa` / `.mscz`) genereerbaar zijn volgens dat productcontract.
   Partituur-PDF (P*) is **geen** standaardproduct: alleen los gereedschap.

Agent-regel in de repo: `.cursor/rules/contracten-eerst.mdc` (en voor
mvsa-export: `mvsa-export-contracten.mdc`). VSA↔template / `vsa mvsa`:
T-reeks in [vsa-mvsa-contract.md](../specification-vsa-templates/vsa-mvsa-contract.md).

## Hubs (onderwerp → canonieke plek)

| Id / onderwerp                                                            | Canonieke hub                                                                                                                                                                                                                 | Typische CLI / keten                                                |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Kern + M-reeks (Coria / playback-`.mxl`)                                  | [canonical-checklists.md](canonical-checklists.md) §MXL                                                                                                                                                                       | `vsa mxl` / `mvsa mxl` / `mscz mxl` / `mxl normalize`               |
| S-reeks (partituur-`.mscz`)                                               | [canonical-checklists.md](canonical-checklists.md) §MSCZ                                                                                                                                                                      | `mvsa mscz` / layout `partituur`                                    |
| P-reeks (PDF A4 e.d.)                                                     | [canonical-checklists.md](canonical-checklists.md) §PDF                                                                                                                                                                       | los: `vsa`/`mvsa`/`mscz pdf`; site: `markdown pdf` → `index.md.pdf` |
| Bestandsnaamgeving `{stam}.{bron}.{doel}`                                 | [canonical-checklists.md](canonical-checklists.md)#bestandsnaamgeving-conventie                                                                                                                                               | alle exports zonder `-o`                                            |
| MSCZ-leesbaarheid (R*/L*/S* print: melisma, breve, spacers, slurs, cues)  | [mscz-leesbaarheid.md](mscz-leesbaarheid.md)                                                                                                                                                                                  | layoutprofiel `partituur` / `muziek`                                |
| Layoutprofielen `partituur` / `muziek` / `plain`                          | [mscz.md](mscz.md)#layoutprofielen---layout                                                                                                                                                                                   | `mvsa mscz` / `{straat} svg` / `{straat} pdf`                       |
| `.mvsa`-syntax                                                            | [specification-mvsa](../specification-mvsa/README.md)                                                                                                                                                                         | `mvsa validate`                                                     |
| `.mvsa` normaliseren (spelling / pitch-opties)                            | man-page [`mvsa normalize`](../reference/cli/mvsa.md#mvsa-normalize) + conversieplan                                                                                                                                          | `mvsa normalize`                                                    |
| Conversiematrix bron↔doel                                                 | [mvsa-conversions](../plans/mvsa-conversions.md) · [formats-overzicht](index.md)                                                                                                                                              | `mxl mvsa`, `mscz mvsa`, …                                          |
| Score-IR / from-ir (bedoelde printvorm)                                   | [score-ir.md](score-ir.md) · [partituur-ir](../plans/partituur-ir.md)                                                                                                                                                         | `{straat} score-ir` (uit `.vsa`/`.mvsa`/`.mscz`)                    |
| OSMD-scherm (S8 e.d.; emit, zelfde bedoeling)                             | [osmd-s8-recite](../plans/osmd-s8-recite.md) → checklists S8/R3                                                                                                                                                               | from-ir → OSMD                                                      |
| Kale muziek-SVG / scherm vs blad                                          | [mvsa-svg.md](mvsa-svg.md) · [kale-muziek-svg-en-uitgaven](../plans/kale-muziek-svg-en-uitgaven.md)                                                                                                                           | `{straat} svg`                                                      |
| Eenstemmig `.vsa`                                                         | [vsa.md](vsa.md) · [specification](../specification/README.md) · frontmatter (`soort`/`toon`): [bibliotheek](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md)                            | `vsa …`                                                             |
| **VSA + template → MVSA** (T1–T7: template-id, melodiestem, emit, corpus) | [vsa-mvsa-contract.md](../specification-vsa-templates/vsa-mvsa-contract.md) · [conversion-lessons.md](../specification-vsa-templates/conversion-lessons.md) · [mapping-vsa.md](../specification-vsa-templates/mapping-vsa.md) | `vsa mvsa` / `vsa.vsa_mvsa` / template-instance                     |
| MusicXML-exportprofielen (playback e.d.)                                  | [rendering — MusicXML](../specification/rendering.md#musicxml-exportprofielen)                                                                                                                                                | `vsa mxl` / `mvsa mxl` / `mscz mxl`                                 |
| Zoektekst (YAML in bron) / lyrics-product (sibling)                       | [zoektekst.md](zoektekst.md) · [`vsa text`](../reference/cli/text.md)                                                                                                                                                         | `{straat} text` → `*.lyrics.txt`                                    |
| Audio-preview                                                             | [audio.md](audio.md)                                                                                                                                                                                                          | `{straat} mp3` / `ogg` / `wav`                                      |
| Scherm/Download in de **bibliotheek**-site                                | bibliotheek [`schermpartituur.md`](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/schermpartituur.md) — **linkt** hierheen, geen tweede checklist                                                          | Hugo / shortcode `muziek`                                           |
| Products-meta (herkomst-sidecar, schema 2)                                | [products-meta.md](products-meta.md)                                                                                                                                                                                          | `vsa`/`mvsa`/`mscz products`                                        |

## Universele productcatalogus

Een standaardproduct is een afgeleid bestand met **één** contract.
`{straat} products` schrijft de **volledige** standaardset uit elke
notatiebron. De bibliotheek mag per bron kiezen wat zij publiceert.
Straat-CLI’s: [straat-CLIs (plan)](../plans/straat-clis.md).

| Meta-key   | Sibling (voorbeeld)          | Contract (hub)                                   |
| ---------- | ---------------------------- | ------------------------------------------------ |
| `mxl`      | `lied.mvsa.mxl`              | checklists M* (Coria / playback)                 |
| `svg`      | `lied.mscz.svg`              | kale tall compacte SVG — [mvsa-svg](mvsa-svg.md) |
| `mp3`      | `lied.mscz.mp3`              | [audio.md](audio.md) (ogg/wav alleen los)        |
| `lyrics`   | `lied.mscz.lyrics.txt`       | platte tekst — [zoektekst](zoektekst.md) / text  |
| `score-ir` | `lied.mvsa.score-ir.json`    | [score-ir.md](score-ir.md) / partituur-ir        |
| `from-ir`  | `lied.mvsa.from-ir.musicxml` | MusicXML uit IR → OSMD                           |
| `mscz`     | `lied.vsa.mscz`              | checklists S* / leesbaarheid (partituur-`.mscz`) |

**Geen standaardproduct:** partituur-PDF (P*, sibling `{stam}.{bron}.pdf`).
Scherm, download, print en navigatie gebruiken die PDF niet.
Publicatiecontrole eist `.vsa.pdf`, `.mvsa.pdf` en `.mscz.pdf` niet.
Los maken kan nog wel: `vsa pdf`, `mvsa pdf` of `mscz pdf` (checklist P*).
`products` schrijft die bestanden niet en haalt een oude meta-key `pdf`
uit de sidecar. Het pdf-bestand op schijf blijft staan tot je het zelf
wist.

CLI: `{straat} {product}` met alleen de eigen bronextensie
(`.vsa` / `.mvsa` / `.mscz`). Voorbeeld: `mscz score-ir`, `vsa mp3`,
`mvsa lyrics` via `mvsa text`. Batch op een map pikt geen geneste
afgeleiden op (`lied.mvsa.mscz` bij `mscz products`); zie
[input-pad](../reference/cli/input-pad.md#geneste-afgeleiden-batch).

**Zelfde-type:** `.mscz` → product `mscz` = partituur-conform maken
(layout `partituur`), niet overslaan. Bron-`.vsa`/`.mvsa` blijven bron
(geen meta-key voor het brontype zelf).

**Invoer (straat-puur):** product/export-subs weigeren vreemde extensies
met hint naar de juiste straat. Uitzonderingen: `mvsa import` /
`mscz import` (destination import); `mscz compare` (SCORE mag MusicXML);
format-CLI `mxl …`.

**Geen product (wel straat-actie):** `normalize`, `import`, `validate`,
`transpose`, `kuiser`, `compare` — geen meta-keys in `products`.

**Pagina-PDF (wel voor download en print):** `markdown pdf` schrijft
`index.md.pdf` naast de site-Markdown. Dat is geen notatie-product en
geen checklist P*. In de bibliotheek doet `scripts\pdf.cmd` hetzelfde.
Man-pagina: [`markdown`](../reference/cli/markdown.md). Partituur-PDF
uit `.vsa`: [`vsa pdf`](../reference/cli/pdf.md).

| Actie (niet-product) | Straat / CLI                                                                 |
| -------------------- | ---------------------------------------------------------------------------- |
| normalize            | `mvsa normalize` · `mscz normalize` · `mxl normalize` (geen `vsa normalize`) |
| import               | `mvsa import` · `mscz import`                                                |
| validate             | `mvsa validate` · `vsa validate` · `mxl validate`                            |
| `manual`             | geen auto-`products`                                                         |

## Sidecar-meta (herkomst / versheid)

Canonieke hub: **[products-meta.md](products-meta.md)** (schema **2**).

Sibling `{bronnaam}.products-meta.json`. **Schrijver:** tooling
street-`products` of individuele product-subs (merge).

| CLI                               | Standaardkeys (universeel)                                                                         |
| --------------------------------- | -------------------------------------------------------------------------------------------------- |
| `vsa`/`mvsa`/`mscz products`      | `mxl`, `score-ir`, `from-ir`, `mscz`, `mp3`, `lyrics` + `svg` (tenzij `--skip-svg`). Geen `pdf`.   |
| Individuele `{straat} {product}`  | merge van de bijbehorende key(s) in dezelfde sidecar                                               |

Flags: `--force`, `--dry-run`. Geen tweede inhoudsnorm in meta.

**`vsa products` MXL:** tijdelijke syllabify + playback-export + Coria-finalize.
SVG uit de ongewijzigde bron. Man-pagina:
[`vsa products`](../reference/cli/products.md).

## PDF-namen (afspraak)

| Context                                  | Commando                            | Uitvoernaam                                |
| ---------------------------------------- | ----------------------------------- | ------------------------------------------ |
| Losse partituur-PDF (niet in `products`) | `vsa` / `mvsa` / `mscz pdf`         | `{stam}.{bron}.pdf` (niet verplicht)       |
| Uit site-`index.md` (bibliotheek)        | `markdown pdf` of `scripts\pdf.cmd` | **`index.md.pdf`**                         |

## Bibliotheek-docs (volgt)

Spiegel/links in bibliotheek (`tooling-koppeling`, `schermpartituur`,
publicatiecontrole, handleiding scripts) moeten naar **deze** index wijzen.
Dat is een aparte mijlpaal in het straat-plan; ontbrekende links = open
punt, geen excuus voor een parallelle checklist in de site-repo.
