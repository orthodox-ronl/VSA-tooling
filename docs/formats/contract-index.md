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

Agent-regels: `.cursor/rules/contracten-eerst.mdc`,
`.cursor/rules/canonieke-bestanden.mdc` (en voor mvsa-export:
`mvsa-export-contracten.mdc`). VSA↔template / `vsa mvsa`: T-reeks in
[vsa-mvsa-contract.md](../specification-vsa-templates/vsa-mvsa-contract.md).

## Contract-skelet (vaste H2-volgorde)

Elk **formatcontract** (pagina onder `docs/formats/…` voor een
bestandstype) gebruikt **dezelfde** H2-volgorde. Per hoofdstuk = één
topic. Ontbreekt het onderwerp voor dat type → korte regel **«n.v.t.»**
plus één zin waarom.

Nieuwe **generieke** topics eerst hier toevoegen, daarna op alle
formatpagina’s. Type-specifieke H2’s komen **na** §11.

| #   | H2-titel (vast)      | Wat erin hoort (minimaal)                                                                                                                                      |
| --  | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Identiteit           | Extensie; rol (bron/afgeleid/sidecar); wanneer dit type bestaat; sibling-naam `{stam}.{bron}.{doel}` of bronnaam                                               |
| 2   | Canoniciteit         | Definitie «canoniek» voor dit type; C*-gates; bekende uitzonderingen                                                                                           |
| 3   | Inhoud en metadata   | Wel/geen frontmatter; verplichte/verboden velden; encoding (UTF-8); toegestane tekens; eigendom (bibliotheek frontmatter waar van toepassing)                  |
| 4   | Syllabificatie       | Soft `-` / hard `=`: vereist, strip, syllabic-brug, of n.v.t.; motivatie + kort voorbeeld                                                                      |
| 5   | Melisma en binding   | Meerdere noten op één lettergreep (K2/K3/S13); hyphen ≠ melisma; frase-slurs; of n.v.t.                                                                        |
| 6   | Transliteratie       | Wel/geen tweede lyric-/SVG-laag; welke modus; n.v.t. waar geen lyrics                                                                                          |
| 7   | Stemmen en partijen  | SATB / melodiestem-default; welke stemmen in dit type; of n.v.t.                                                                                               |
| 8   | Leesbaarheid         | Fonts, groottes, stacking/overlap, marges; layoutprofiel (`partituur`/`muziek`/`plain`); scherm vs blad — of n.v.t.                                            |
| 9   | Herkomst             | products-meta / versheid; of dit type sidecar schrijft/leest; schema; of n.v.t.                                                                                |
| 10  | Conversies           | Wat dit type als bron/doel mag; welke CLI; moet bron/doel canoniek zijn                                                                                        |
| 11  | Validatie            | Hoe je canoniciteit controleert (`validate`, checklists); severity                                                                                             |

**Type-specifiek** (na §11): checklists M*/S*/R*/T*/E*/P*, recite/print-collapse,
Score-IR-velden, kuiser, OSMD-emit, audio-parameters, enz.

Afspraken die **geen** vaste H2 zijn (recite-collapse, normalisatie-details,
bibliotheek-publicatiekeuze, CLI-invoerpad) moeten wél op **alle toepasselijke**
formatpagina’s staan (samenvatting + contract-id + link naar diepte-hub). Zie
agentregel `.cursor/rules/canonieke-bestanden.mdc` en §Nieuwe regel hieronder.

Diepte-hubs in de tabel «Hubs» blijven de **enige** plek voor volledige
normtekst; formatpagina’s vatten samen en linken.

## Canoniciteit en conversiegates (C*)

| Id  | Regel                                                                                                                                 |
| --  | ------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | Elk invoer-/uitvoertype dat tooling leest of schrijft heeft een formatcontract (pagina of hub hieronder).                             |
| C2  | Een bestand is **canoniek** als het voldoet aan het formatcontract van dat type (incl. checklist-id’s waar die gelden).               |
| C3  | Een **conversie** verifieert dat de **bron** canoniek is, tenzij het CLI-contract een expliciete uitzondering noemt.                  |
| C4  | Een conversie levert een **canonieke doel**, tenzij het CLI-contract een expliciete uitzondering noemt.                               |

**Bekende uitzonderingen** (geen stille omzeiling; noem ze in man-pages):

| Situatie                         | Waarom toegestaan                                         |
| -------------------------------- | --------------------------------------------------------- |
| `validate`                       | Mag juist niet-canonieke bron tonen/melden                |
| `syllabify` / `--unsyllabify`    | Bewust (on)canoniek maken van zing-deling                 |
| `--syllabify` op o.a. MXL-export | Expliciete opt-in; default eist zing-deling in de bron    |
| `import` / werkbank              | Tussenstadium vóór catalogus-canoniciteit                 |
| `--allow-noncanonical`           | C3-uitzondering op products/product-subs (niet catalogus) |

**C3 afgedwongen (fase 3):** `.vsa` / `.mvsa` bronnen bij
`{straat} products` en hoog-prio product-subs (`text`, `mxl`, `svg`,
`mp3`/`audio`, `mscz`, …) via `vsa.canonicity_gate` (non-interactieve
`validate`). Bron `.mscz`: **structurele** C3 (geldige zip + leesbare
``.mscx``); nog geen volle S*/leesbaarheid-gate. Zie
[cli-canoniciteit-audit](cli-canoniciteit-audit.md).

## Nieuwe regel → contracten → naleving

Wanneer een normatieve afspraak **nieuw** is of **wijzigt** (geldt voor
alle chats; gebruiker hoeft dit niet opnieuw te noemen):

1. **Hub eerst** — wijzig alleen de canonieke hub (of voeg daar een
   contract-id toe).
2. **Alle toepasselijke formatcontracten** — samenvatting + id + link in
   het juiste H2; bij een nieuw *generiek* topic eerst dit skelet
   bijwerken, daarna alle formatpagina’s.
3. **Deze contract-index** — hub-rij / onderwerp bijwerken als nodig.
4. **Naleving starten** — in dezelfde ronde of als volgende mijlpaal na
   expliciete OK bij bulk: validate/gates/tests waar mogelijk; plan om
   **bestaande bestanden** van die types compliant te maken (regen,
   bronfix, steekproef → bulk). Geen stille «alleen docs».
5. **Man-pages / handleidingen** synchroon (repo-regel
   `.cursor/rules/docs-sync-with-code.mdc`).

**Verboden:** alleen code of één formatpagina wijzigen terwijl andere
toepasselijke types dezelfde regel missen; nieuwe regel alleen in een
chat laten hangen.

## Dekkingsmatrix (afspraak → formatcontracten)

Elke rij moet op de genoemde formatpagina’s terugkomen (samenvatting +
id + link). Gat = migratieschuld. Diepte-hubs blijven normtekst.

| Afsprakencluster                       | Diepte-hub                                                                                  | Toepasselijke formatcontracten                                                                                                                                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Syllabificatie (soft `-` / `=` / dict) | [syllabificatie.md](syllabificatie.md)                                                      | [vsa](vsa.md), [mvsa](mvsa.md), [mxl](mxl.md), [mscz](mscz.md), [lyrics.txt](lyrics.txt.md), [vsa-svg](vsa-svg.md), [mvsa-svg](mvsa-svg.md), [translit-svg](translit-svg.md), [audio](audio.md) (n.v.t. inhoud) |
| Melisma M5a/S13/K2                     | [canonical-checklists](canonical-checklists.md) · [mscz-leesbaarheid](mscz-leesbaarheid.md) | [vsa](vsa.md), [mvsa](mvsa.md), [mxl](mxl.md), [mscz](mscz.md), [score-ir](score-ir.md), [from-ir](from-ir.md)                                                                                                  |
| Recite print-collapse S8 / R5          | checklists · leesbaarheid                                                                   | [mscz](mscz.md), [score-ir](score-ir.md), [from-ir](from-ir.md), [mvsa-svg](mvsa-svg.md)                                                                                                                        |
| Recite playback M10 (geen collapse)    | checklists §MXL                                                                             | [mxl](mxl.md) (expliciet), [mscz](mscz.md) (contrast)                                                                                                                                                           |
| R8 underlay (geen interne hyphens)     | [mscz-leesbaarheid](mscz-leesbaarheid.md)                                                   | [mscz](mscz.md), [syllabificatie](syllabificatie.md), [score-ir](score-ir.md)/[from-ir](from-ir.md) waar underlay                                                                                               |
| Naamgeving `{stam}.{bron}.{doel}`      | [canonical-checklists](canonical-checklists.md)#bestandsnaamgeving-conventie                | alle productpagina’s §Identiteit                                                                                                                                                                                |
| Products-meta schema 2                 | [products-meta](products-meta.md)                                                           | [products-meta](products-meta.md) + §Herkomst op producten                                                                                                                                                      |
| Frontmatter `.vsa`                     | bibliotheek vsa-frontmatter                                                                 | [vsa](vsa.md) §Inhoud                                                                                                                                                                                           |
| VSA→MVSA T1–T7                         | [vsa-mvsa-contract](../specification-vsa-templates/vsa-mvsa-contract.md)                    | [vsa](vsa.md) §Conversies · [mvsa](mvsa.md) §Stemmen                                                                                                                                                            |
| MVSA→VSA E1–E6                         | [mvsa-vsa-contract](mvsa-vsa-contract.md)                                                   | [mvsa](mvsa.md) · product `vsa`                                                                                                                                                                                 |
| Zoektekst YAML / lyrics-product        | [zoektekst](zoektekst.md) · [lyrics.txt](lyrics.txt.md)                                     | [vsa](vsa.md), [mvsa](mvsa.md), [lyrics.txt](lyrics.txt.md)                                                                                                                                                     |
| Transliteratie                         | [kerkslavisch-transliteratie](../plans/kerkslavisch-transliteratie.md)                      | [translit-svg](translit-svg.md); §Transliteratie op bron/SVG                                                                                                                                                    |
| Layoutprofielen                        | [mscz.md](mscz.md)#layoutprofielen---layout                                                 | [mscz](mscz.md), [mvsa-svg](mvsa-svg.md)                                                                                                                                                                        |
| Audio A1–A5                            | [audio](audio.md)                                                                           | [audio](audio.md)                                                                                                                                                                                               |
| Score-IR / from-ir / OSMD              | [score-ir](score-ir.md) · [from-ir](from-ir.md) · osmd-s8-recite                            | die pagina’s + [mvsa-svg](mvsa-svg.md)                                                                                                                                                                          |

## Hubs (onderwerp → canonieke plek)

| Id / onderwerp                                                                                             | Canonieke hub                                                                                                                                                                                                                 | Typische CLI / keten                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Kern + M-reeks (Coria / playback-`.mxl`)                                                                   | [canonical-checklists.md](canonical-checklists.md) §MXL                                                                                                                                                                       | `vsa mxl` / `mvsa mxl` / `mscz mxl` / `mxl normalize`                                                  |
| S-reeks (partituur-`.mscz`)                                                                                | [canonical-checklists.md](canonical-checklists.md) §MSCZ                                                                                                                                                                      | `mvsa mscz` / layout `partituur`                                                                       |
| P-reeks (PDF A4 e.d.)                                                                                      | [canonical-checklists.md](canonical-checklists.md) §PDF                                                                                                                                                                       | los: `vsa`/`mvsa`/`mscz pdf`; site: `markdown pdf` → `index.md.pdf`                                    |
| Bestandsnaamgeving `{stam}.{bron}.{doel}`                                                                  | [canonical-checklists.md](canonical-checklists.md)#bestandsnaamgeving-conventie                                                                                                                                               | alle exports zonder `-o`                                                                               |
| MSCZ-leesbaarheid (R*/L*/S* print: melisma, breve, spacers, slurs, cues; R8 recite zonder interne hyphens) | [mscz-leesbaarheid.md](mscz-leesbaarheid.md) · [syllabificatie.md](syllabificatie.md)                                                                                                                                         | layoutprofiel `partituur` / `muziek`                                                                   |
| Layoutprofielen `partituur` / `muziek` / `plain`                                                           | [mscz.md](mscz.md)#layoutprofielen---layout                                                                                                                                                                                   | `mvsa mscz` / `{straat} svg` / `{straat} pdf`                                                          |
| `.mvsa`-syntax                                                                                             | [specification-mvsa](../specification-mvsa/README.md)                                                                                                                                                                         | `mvsa validate`                                                                                        |
| `.mvsa` normaliseren (spelling / pitch-opties)                                                             | man-page [`mvsa normalize`](../reference/cli/mvsa.md#mvsa-normalize) + conversieplan                                                                                                                                          | `mvsa normalize`                                                                                       |
| Conversiematrix bron↔doel                                                                                  | [mvsa-conversions](../plans/mvsa-conversions.md) · [formats-overzicht](index.md)                                                                                                                                              | `mxl mvsa`, `mscz mvsa`, …                                                                             |
| Score-IR / from-ir (bedoelde printvorm)                                                                    | [score-ir.md](score-ir.md) · [partituur-ir](../plans/partituur-ir.md)                                                                                                                                                         | `{straat} score-ir` (uit `.vsa`/`.mvsa`/`.mscz`)                                                       |
| OSMD-scherm (S8 e.d.; emit, zelfde bedoeling)                                                              | [osmd-s8-recite](../plans/osmd-s8-recite.md) → checklists S8/R3                                                                                                                                                               | from-ir → OSMD                                                                                         |
| Kale muziek-SVG / scherm vs blad                                                                           | [mvsa-svg.md](mvsa-svg.md) · [kale-muziek-svg-en-uitgaven](../plans/kale-muziek-svg-en-uitgaven.md)                                                                                                                           | `{straat} svg`                                                                                         |
| Eenstemmig `.vsa`                                                                                          | [vsa.md](vsa.md) · [specification](../specification/README.md) · frontmatter (`soort`/`toon`): [bibliotheek](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md)                            | `vsa …`                                                                                                |
| **VSA + template → MVSA** (T1–T7: template-id, melodiestem, emit, corpus)                                  | [vsa-mvsa-contract.md](../specification-vsa-templates/vsa-mvsa-contract.md) · [conversion-lessons.md](../specification-vsa-templates/conversion-lessons.md) · [mapping-vsa.md](../specification-vsa-templates/mapping-vsa.md) | `vsa mvsa` / `vsa.vsa_mvsa` / template-instance                                                        |
| **MVSA → VSA** (E1–E6: stem-extractie, maat=strofe, herkomst-FM)                                           | [mvsa-vsa-contract.md](mvsa-vsa-contract.md)                                                                                                                                                                                  | `mvsa vsa` / `mvsa products` key `vsa`                                                                 |
| MusicXML-exportprofielen (playback e.d.)                                                                   | [rendering — MusicXML](../specification/rendering.md#musicxml-exportprofielen)                                                                                                                                                | `vsa mxl` / `mvsa mxl` / `mscz mxl`                                                                    |
| Zoektekst (YAML in bron) / lyrics-product (sibling)                                                        | [zoektekst.md](zoektekst.md) · [lyrics.txt.md](lyrics.txt.md) · [`vsa text`](../reference/cli/text.md)                                                                                                                        | `{straat} text` → `*.lyrics.txt`                                                                       |
| **Syllabificatie** (zing-deling; soft `-` / hard `=`; dictionary; uitzonderingslijst)                      | [syllabificatie.md](syllabificatie.md) · [`vsa syllabify`](../reference/cli/syllabify.md) · [`mvsa syllabify`](../reference/cli/mvsa.md#mvsa-syllabify)                                                                       | `.vsa`: `vsa validate`/`syllabify`; `.mvsa`: `mvsa validate`/`syllabify` (L-lyrics); strip in text/SVG |
| Translit-SVG                                                                                               | [translit-svg.md](translit-svg.md) · [kerkslavisch-transliteratie](../plans/kerkslavisch-transliteratie.md)                                                                                                                   | `--translit` / consumer siblings                                                                       |
| from-ir MusicXML (OSMD)                                                                                    | [from-ir.md](from-ir.md) · [score-ir.md](score-ir.md)                                                                                                                                                                         | `{straat} score-ir --musicxml`                                                                         |
| Audio-preview                                                                                              | [audio.md](audio.md)                                                                                                                                                                                                          | `{straat} mp3` / `ogg` / `wav`                                                                         |
| CLI-canoniciteit-audit (C3/C4 gaps)                                                                        | [cli-canoniciteit-audit.md](cli-canoniciteit-audit.md)                                                                                                                                                                        | fase 2 inventaris; fase 3 gates                                                                        |
| Scherm/Download in de **bibliotheek**-site                                                                 | bibliotheek [`schermpartituur.md`](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/schermpartituur.md) — **linkt** hierheen, geen tweede checklist                                                          | Hugo / shortcode `muziek`                                                                              |
| Products-meta (herkomst-sidecar, schema 2)                                                                 | [products-meta.md](products-meta.md)                                                                                                                                                                                          | `vsa`/`mvsa`/`mscz products`                                                                           |

## Universele productcatalogus

Een standaardproduct is een afgeleid bestand met **één** contract.
`{straat} products` schrijft de **volledige** standaardset uit elke
notatiebron. De bibliotheek mag per bron kiezen wat zij publiceert.
Straat-CLI’s: [straat-CLIs (plan)](../plans/straat-clis.md).

| Meta-key   | Sibling (voorbeeld)          | Contract (hub)                                                                   |
| ---------- | ---------------------------- | -------------------------------------------------------------------------------- |
| `mxl`      | `lied.mvsa.mxl`              | checklists M* (Coria / playback)                                                 |
| `svg`      | `lied.mscz.svg`              | kale tall compacte SVG — [mvsa-svg](mvsa-svg.md)                                 |
| `mp3`      | `lied.mscz.mp3`              | [audio.md](audio.md) (ogg/wav alleen los)                                        |
| `lyrics`   | `lied.mscz.lyrics.txt`       | platte tekst — [zoektekst](zoektekst.md) / text                                  |
| `score-ir` | `lied.mvsa.score-ir.json`    | [score-ir.md](score-ir.md) / partituur-ir                                        |
| `from-ir`  | `lied.mvsa.from-ir.musicxml` | MusicXML uit IR → OSMD                                                           |
| `mscz`     | `lied.vsa.mscz`              | checklists S* / leesbaarheid (partituur-`.mscz`)                                 |
| `vsa`      | `lied.mvsa.vsa`              | [mvsa-vsa-contract](mvsa-vsa-contract.md) (E*) — **mvsa-straat**; default stem S |

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
[input-pad](../reference/cli/input-pad.md) (bestand / map / **catalogus-id**).

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

**`vsa products` MXL / `vsa audio` uit `.vsa`:** playback-export **zonder**
stille syllabify (+ Coria-finalize); zing-deling in de bron — zie
[syllabificatie.md](syllabificatie.md). Man-pagina’s:
[`vsa products`](../reference/cli/products.md),
[`vsa audio`](../reference/cli/audio.md).

## PDF-namen (afspraak)

| Context                                  | Commando                            | Uitvoernaam                                |
| ---------------------------------------- | ----------------------------------- | ------------------------------------------ |
| Losse partituur-PDF (niet in `products`) | `vsa` / `mvsa` / `mscz pdf`         | `{stam}.{bron}.pdf` (niet verplicht)       |
| Uit site-`index.md` (bibliotheek)        | `markdown pdf` of `scripts\pdf.cmd` | **`index.md.pdf`**                         |

## Bibliotheek-docs

Consumer-repo **bibliotheek** linkt hierheen (geen parallelle checklist):

| Bibliotheek-doc                                                                                               | Wat het linkt                                  |
| ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| [tooling-koppeling](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/tooling-koppeling.md)         | §Canoniek in de catalogus + formatpagina-tabel |
| [schermpartituur](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/schermpartituur.md)       | Schermketens → score-ir / from-ir / SVG        |
| [publicatiecontrole](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/publicatiecontrole.md)       | Publicatieregels + deze index                  |
| [catalogus-notatiebron](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/catalogus-notatiebron.md) | Eén bron per leaf + formatcontracten           |
| [vsa-frontmatter](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md)       | Frontmatter-eigendom (bibliotheek)             |

Agentregels in bibliotheek: `contracten-eerst.mdc`, `canonieke-bestanden.mdc`.
