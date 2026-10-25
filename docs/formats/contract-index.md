# Contract-index (canonieke afspraken)

**Start hier** als je export, normalize, layout, Score-IR/from-ir of OSMD
aanraakt. Normatieve regels staan **alleen** in de hubs hieronder. Elders
(man-pages, plans, bibliotheek-specs) **linken** — niet herformuleren.

## Regels

1. Wijzig een afspraak alleen in de canonieke hub; elders alleen een link.
2. Elke CLI, test of consumer-doc die gedrag raakt noemt het **contract-id**
   (checklistregel of layoutprofiel), niet alleen een vrije samenvatting.
3. Kanalen (Coria-`.mxl`, MuseScore-`.mscz`, Score-IR, from-ir, OSMD) delen
   dezelfde **bedoelde** print-/recite-/melisma-vorm; alleen de *emit* mag
   per kanaal verschillen als de hub dat zo scheidt (bijv. M10 vs R5).
4. `normalize` / toekomstig `products` / `import` **implementeren** deze
   hubs; ze definiëren geen parallelle norm.

Agent-regel in de repo: `.cursor/rules/contracten-eerst.mdc` (en voor
mvsa-export: `mvsa-export-contracten.mdc`).

## Hubs (onderwerp → canonieke plek)

| Id / onderwerp                                                           | Canonieke hub                                                                                                                                                        | Typische CLI / keten                      |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Kern + M-reeks (Coria / playback-`.mxl`)                                 | [canonical-checklists.md](canonical-checklists.md) §MXL                                                                                                              | `mvsa mxl` / `mxl normalize` / `mscz mxl` |
| S-reeks (partituur-`.mscz`)                                              | [canonical-checklists.md](canonical-checklists.md) §MSCZ                                                                                                             | `mvsa mscz` / layout `partituur`          |
| P-reeks (PDF A4 e.d.)                                                    | [canonical-checklists.md](canonical-checklists.md) §PDF                                                                                                              | `mvsa pdf` / `mscz pdf` / `vsa pdf`       |
| Bestandsnaamgeving `{stam}.{bron}.{doel}`                                | [canonical-checklists.md](canonical-checklists.md)#bestandsnaamgeving-conventie                                                                                      | alle exports zonder `-o`                  |
| MSCZ-leesbaarheid (R*/L*/S* print: melisma, breve, spacers, slurs, cues) | [mscz-leesbaarheid.md](mscz-leesbaarheid.md)                                                                                                                         | layoutprofiel `partituur` / `muziek`      |
| Layoutprofielen `partituur` / `muziek` / `plain`                         | [mscz.md](mscz.md)#layoutprofielen---layout                                                                                                                          | `mvsa mscz` / `mvsa svg` / `mvsa pdf`     |
| `.mvsa`-syntax                                                           | [specification-mvsa](../specification-mvsa/README.md)                                                                                                                | `mvsa validate`                           |
| `.mvsa` normaliseren (spelling / pitch-opties)                           | man-page [`mvsa normalize`](../reference/cli/mvsa.md#mvsa-normalize) + conversieplan                                                                                 | `mvsa normalize`                          |
| Conversiematrix bron↔doel                                                | [mvsa-conversions](../plans/mvsa-conversions.md) · [formats-overzicht](index.md)                                                                                     | `mxl mvsa`, `mscz mvsa`, …                |
| Score-IR / from-ir (bedoelde printvorm)                                  | [score-ir.md](score-ir.md) · [partituur-ir](../plans/partituur-ir.md)                                                                                                | `mvsa score-ir`                           |
| OSMD-scherm (S8 e.d.; emit, zelfde bedoeling)                            | [osmd-s8-recite](../plans/osmd-s8-recite.md) → checklists S8/R3                                                                                                      | from-ir → OSMD                            |
| Kale muziek-SVG / scherm vs blad                                         | [mvsa-svg.md](mvsa-svg.md) · [kale-muziek-svg-en-uitgaven](../plans/kale-muziek-svg-en-uitgaven.md)                                                                  | `mvsa svg` layout `muziek`                |
| Eenstemmig `.vsa`                                                        | [vsa.md](vsa.md) · [specification](../specification/README.md)                                                                                                       | `vsa …`                                   |
| MusicXML-exportprofielen (playback e.d.)                                 | [rendering — MusicXML](../specification/rendering.md#musicxml-exportprofielen)                                                                                       | `vsa musicxml`                            |
| Zoektekst / lyrics-export                                                | [zoektekst.md](zoektekst.md) · [`vsa text`](../reference/cli/text.md)                                                                                                | `vsa text` / `mscz text`                  |
| Audio-preview                                                            | [audio.md](audio.md)                                                                                                                                                 | `vsa audio` / `mvsa mp3`                  |
| Scherm/Download in de **bibliotheek**-site                               | bibliotheek [`schermpartituur.md`](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/schermpartituur.md) — **linkt** hierheen, geen tweede checklist | Hugo / shortcode `muziek`                 |

## Straat × product × contract (doelbeeld)

Product = afgeleid bestand dat de consumer (o.a. bibliotheek) nodig heeft.
Straat-CLI’s (`vsa` / `mvsa` / `mscz` / `manual`) en `products` zijn het
uitrolpad; zie [straat-CLIs (plan)](../plans/straat-clis.md).

| Straat           | Product / actie          | Contract (hub + id)                                 | CLI nu / doel                                                                                          |
| ---------------- | ------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **mvsa**         | Coria-`.mxl`             | checklists M* + K*                                  | `mvsa mxl` / `mvsa musicxml`                                                                           |
| **mvsa**         | Score-IR + from-ir       | partituur-ir / score-ir; S8 → osmd-s8-recite        | `mvsa score-ir [--musicxml]`                                                                           |
| **mvsa**         | scherm/blad-SVG          | leesbaarheid + layout `muziek`                      | `mvsa svg`                                                                                             |
| **mvsa**         | bron-PDF                 | checklists P* + layout `partituur`                  | `mvsa pdf`                                                                                             |
| **mvsa**         | audio / lyrics           | audio.md / zoektekst + `vsa text`                   | `mvsa mp3` · text-export                                                                               |
| **mvsa**         | normalize                | mvsa-normalize man-page (canonieke spelling)        | `mvsa normalize`                                                                                       |
| **mvsa**         | import (→ `.mvsa`)       | mvsa-conversions; werkbank-bewerkvorm               | **`mvsa import`** (= `mscz mvsa` / `mxl mvsa`)                                                         |
| **mscz**         | Coria-`.mxl`             | checklists M*                                       | `mscz mxl`                                                                                             |
| **mscz**         | scherm-SVG               | leesbaarheid + `muziek` (via `mvsa svg` op `.mscz`) | `mvsa svg` → doel: `mscz svg`                                                                          |
| **mscz**         | bron-PDF                 | P* + `partituur`                                    | `mvsa pdf` op `.mscz` → doel: `mscz pdf`                                                               |
| **mscz**         | normalize                | leesbaarheid + layout `partituur` + S*              | nu: bibliotheek `layout` / tooling layout → doel: `mscz normalize`                                     |
| **mscz**         | import (→ `.mscz`)       | leesbaarheid / S*                                   | **`mscz import`** (= `mvsa mscz` / `mxl mscz`)                                                         |
| **vsa**          | Coria-`.mxl`             | M* (mono waar van toepassing) + rendering playback  | `vsa products` (syllabify + finalize) · `vsa musicxml` ([`--syllabify`](../reference/cli/musicxml.md)) |
| **vsa**          | scherm-SVG               | vsa-svg / native renderer                           | `vsa svg`                                                                                              |
| **vsa**          | bron-PDF                 | P* waar van toepassing                              | `vsa pdf`                                                                                              |
| **vsa**          | audio / lyrics           | audio.md / text                                     | `vsa audio` / `vsa text`                                                                               |
| **vsa**          | normalize                | specification VSA (canonieke notatie)               | expliciet maken als `vsa normalize` waar nodig                                                         |
| **manual**       | geen auto-`products`     | consumer: `manueel`/`manual`-flag                   | geen stille regen                                                                                      |
| **manual**       | format-normalize SVG/PDF | **nog geen** hub — pas CLI ná contract              | uitgesteld                                                                                             |
| **mxl** (format) | normalize playback       | M*                                                  | `mxl normalize`                                                                                        |
| **mxl**          | → mvsa / mscz            | mvsa-conversions + S*/M*                            | `mxl mvsa` / `mxl mscz`                                                                                |

## Sidecar-meta (versheid, schema v1)

Sibling `{stam}.{bron}.products-meta.json` (bijv. `lied.mvsa.products-meta.json`)
met `bron_sha256` + productpaden. Geschreven door:

| CLI             | Kernproducten (meta-keys)                                  |
| --------------- | ---------------------------------------------------------- |
| `mvsa products` | `mxl`, `score-ir`, `from-ir` (+ `svg` tenzij `--skip-svg`) |
| `mscz products` | `mxl` (+ `svg` tenzij `--skip-svg`)                        |
| `vsa products`  | `mxl`, `svg`                                               |

Flags: `--force`, `--dry-run`. Geen bibliotheek-stamps (consumer). Geen
tweede inhoudsnorm — alleen versheid t.o.v. bron. Zie
[straat-CLIs](../plans/straat-clis.md).

**`vsa products` MXL:** tijdelijke syllabify + playback-export + Coria-finalize
(sanitize/voortekens). SVG uit de ongewijzigde bron. Man-pagina:
[`vsa products`](../reference/cli/products.md).

## PDF-namen (afspraak)

| Context                           | Commando          | Uitvoernaam                                |
| --------------------------------- | ----------------- | ------------------------------------------ |
| Uit notatiebron                   | `xxx pdf`         | `{stam}.{bron}.pdf` (naamgevingsconventie) |
| Uit site-`index.md` (bibliotheek) | `scripts\pdf.cmd` | **`index.md.pdf`**                         |

## Bibliotheek-docs (volgt)

Spiegel/links in bibliotheek (`tooling-koppeling`, `schermpartituur`,
publicatiecontrole, handleiding scripts) moeten naar **deze** index wijzen.
Dat is een aparte mijlpaal in het straat-plan; ontbrekende links = open
punt, geen excuus voor een parallelle checklist in de site-repo.
