# Template-instance rendering — valkuilen

**Doel:** checklist voor agents die verder werken aan vsa-templates →
MSCZ/MXL/PDF. Geen projectgeschiedenis; alleen **probleem → oorzaak → regel**.

Lees dit **vóór** je `scripts/render_vsa_template_musicxml.py`,
`src/vsa/template_instance.py` of corpus-PDF’s wijzigt.

Gerelateerd: [mapping-vsa.md](mapping-vsa.md), [open-points.md](open-points.md),
`collapse_recite_for_print()` in `scripts/render_vsa_template_musicxml.py`.

---

## Twee exportkanalen

| Kanaal                         | Doel                         | Recite-printmodel                                      |
| ------------------------------ | ---------------------------- | ------------------------------------------------------ |
| **MSCZ** (MuseScore / PDF)     | leespartituur                | collapse: `\|\|O\|\|` + slotlettergreep als kwart      |
| **MXL** (Coria e.d.)           | playback / solo per stem     | **geen** collapse — elke syllabe een noot              |

Regel: wijzigingen aan `collapse_recite_for_print` raken **alleen** MSCZ/print.
Coria-export via `render_instance_musicxml` houdt per-syllabe-noten.

---

## Recite-collapse (print)

| Probleem                                                  | Oorzaak                                                               | Regel                                                                                                                                                                                                                  |
| --------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{moe__}`, `{Ni__}`, `{/en}` verdwijnen in de breve       | Heuristieken: “zelfde toonhoogte”, “woord loopt door”, leading absorb | Collapse **alleen** aaneengesloten `role=recite` (ongemarkeerde VSA-syllaben). Elke **VSA-scope** blijft een eigen noot met VSA-duur — nooit breve, nooit opslokken.                                                   |
| Te korte recite (`Als de`) op `\|\|O\|\|`                 | Collapse bij 1–2 syllaben                                             | Alleen bij **≥ 3** recite-syllaben (`RECITE_COLLAPSE_MIN_SYLLABLES`). Anders aparte kwarten.                                                                                                                           |
| Onduidelijk wat onder de breve hoort                      | Te veel speciale gevallen                                             | Simpel: **eerste** body-lettergreep gecentreerd op de `\|\|O\|\|`; overige body-lettergrepen elk op een onzichtbare spacer-noot (naar rechts); **laatste** recite-syllabe = kwart; daarna template/cadens ongewijzigd. |
| Punt achter de `\|\|O\|\|` (gestippelde whole/breve)      | Duur opgeblazen met `dots=1` voor tekstbreedte                        | Recite-printnoot: altijd **half + `headType` breve + `noStem`**, **`dots=0`**. Nooit dotted whole/longa als “ `\|\|O\|\|` ”.                                                                                           |
| Lege systemen / “rij rusten”                              | Maatduur opgeblazen (`longa`, 22/4) zodat MuseScore rare layout maakt | Tekstruimte via **onzichtbare spacer-noten** (één per body-lettergreep) ná de `\|\|O\|\|`, niet via langere notehead-duur of één joined lyric + ticks.                                                                 |
| Grote gap tussen einde recitaltekst en cadens-lettergreep | Eén joined lyric + te veel spacer-rusten                              | Rest-ruimte verdeelt MuseScore over de spacer-noten **tussen** de lettergrepen.                                                                                                                                        |
| Melisma-extender onder recite-tekst                       | `lyric_ticks` op de `\|\|O\|\|`                                       | Geen extender op de recite-printnoot; ticks/slur alleen op echte VSA-melisma’s.                                                                                                                                        |

Canonieke voorbeelden (T4-11):

- `{/en} het voor-beeld der zacht{moe__}dig{\heid_}` → `en` \| `het` (gecentreerd op `\|\|O\|\|`) \| `voor-` `beeld` `der` (spacers) \| `zacht` \| `moe` (heel) \| `dig` \| `heid`
- `{/Va}der … pries-ter {Ni__}ko{\laas_}` → `Va` \| `der … pries-` (eerste op `\|\|O\|\|`, rest spacers) \| `ter` \| `Ni` (heel) \| `ko` \| `laas`

---

## MuseScore 4 (MSCZ)

| Probleem                                                | Oorzaak                                                               | Regel                                                                                                                                                                                   |
| ------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Binnen-strofe-maatstrepen blijven zichtbaar             | `Measure/endBarLineVisible` wordt **genegeerd**                       | Maatstreep-zichtbaarheid alleen via `<BarLine><subtype>…</subtype><visible>0</visible></BarLine>` **in de voice**. Roundtrip verifiëren.                                                |
| Layout-splits midden in strofe vs “één maat”            | `split_events_for_layout` voor instance                               | Instance: **één maat per strofe**, geen binnen-strofe-knip. Coria idem.                                                                                                                 |
| Recite-lyrics blijven gecentreerd ondanks `<align>left` | MS 4.7: horizontale plaatsing = **`position`**, niet (alleen) `align` | Eerste recite-lettergreep: **geen** `position=left` (default = gecentreerd op de nootkop). Overige body-lettergrepen op spacer-noten. `align` alleen = tekstinterne uitlijning.         |
| Maatsoort-getallen zichtbaar                            | TimeSig in maat nodig voor `len`, maar stijl toont ze                 | TimeSig mag in de maat; staff: `showTimeSig=0`, style: `genCourtesyTimesig=0`.                                                                                                          |
| Stokken systematisch S/T omhoog, A/B omlaag             | Twee stemmen per balk                                                 | **Canoniek** voor MSCZ: voice 1 + `<stem>up</stem>` (S/T), voice 2 + `<stem>down</stem>` (A/B), met `<backup/>`.                                                                        |
| “Invisible” rusten of style verdwijnen na opslaan       | MuseScore herschrijft bij save                                        | Niet steunen op roundtrip-behoud van Style; opnieuw genereren vanuit script is bron van waarheid.                                                                                       |
| “Corrupt score” / ongelijke stemmen na melisma-collapse | MusicXML `type=breve` of gestipte som (`half`+`dot`, `duration≠type`) | Partituur: zelfde-hoogte melisma alleen mergen naar ongestipte ≤ whole; maat-`len` gelijk over staves. Zie checklist S13 / leesbaarheid R7 (mvsa) en `headType` breve ≠ `durationType`. |

---

## Mapping / hoogten (instance)

| Probleem                           | Oorzaak                                         | Regel                                                                                                        |
| ---------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Stil hold op verkeerde laddergraad | Soft mismatch                                   | **H9:** hoogte-mismatch → harde `TemplateInstanceError`, geen stil hold.                                     |
| Slotcadens `laatste` vs frase `1`  | Template: `laatste` is mi–re–mi; frase 1 anders | VSA voor `laatste` moet template pitches volgen; parallelle cadenspaden via YAML `of` (eerste passende pad). |
| `T.4` / `T.N` als zingbare syllabe | Toon-aanduiding in VSA-regel                    | Geen `T.N` in de zingbare VSA-regel; inline-fragment in proza is geen lyric-pipeline.                        |

---

## Corpus / tooling

| Probleem                            | Oorzaak                                                                              | Regel                                                                                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Verwarring legacy `*.pad-b.*`-namen | Legacy `*.pad-b.*`                                                                   | Corpus: `T4-XX-….vsa/.mscz/.mxl`; formule: `template.mscz` + `template.mxl`.                                                     |
| PDF in git vs lokaal                | PDF is afgeleide MuseScore-export                                                    | PDF lokaal regenereren (`--pdf` / `--pdf-only`); niet als bron behandelen.                                                       |
| Tests groen, PDF “fout”             | Tests toetsen MSCX-strings, niet visuele MuseScore-layout                            | Na layout-wijzigingen: PDF/MSCZ **openen in MuseScore** of screenshot; niet alleen pytest.                                       |
| Grote verticale witruimte           | MuseScore vult tot `maxSystemDistance`; MS4 leest Style vooral uit `score_style.mss` | Doel 1,5× stafafruimte op scherm: titel = VBox+`frameSystemDistance`; systemDistance ×9/7 t.o.v. naïeve 1,5× (gemeten 7/6).      |
| Eerste systeem springt in           | MuseScore default `enableIndentationOnFirstSystem`                                   | Zet die op `0` (gelijke linker marge).                                                                                           |

---

## Wat niet opnieuw proberen

1. Leading/trailing “zelfde pitch” of “woord-hold” in `collapse_recite_for_print` om scopes onder de breve te trekken.
2. `endBarLineVisible` op `Measure` voor verborgen maatstrepen in MS4.
3. `longa` / gestippelde whole als recite-duur om lyric-breedte te forceren.
4. Alle body-lettergrepen tot één left-aligned lyric + `lyric_ticks` (extender onder de tekst; gap ná de recitaltekst).
5. Alleen `<align>left,…>` verwachten voor left-attach aan de nootkop in MS 4.7+.
6. Recite-collapse in de Coria-MXL-pipeline.

---

## Formuleblad vs instance (wat in git)

| Bestand                 | In git?                    | Regenereren                                         |
| ----------------------- | -------------------------- | --------------------------------------------------- |
| `template.yaml`         | ja (bron)                  | handmatig                                           |
| `template.mscz`         | ja (afgeleid, formuleblad) | `scripts\render_tropaar_toon4_corpus.py --template` |
| `template.mxl`          | ja (afgeleid)              | idem                                                |
| `template.pdf`          | **nee**                    | `--template --pdf`                                  |
| corpus `.vsa`           | ja (bron)                  | curated                                             |
| corpus `.mscz` / `.mxl` | ja (afgeleid instance)     | `scripts\render_tropaar_toon4_corpus.py`            |
| `*.pdf`                 | **nee** (`.gitignore`)     | `--pdf` / `--pdf-only` (MuseScore CLI)              |

CI draait pytest (o.a. MSCX-strings); visuele PDF-check is lokaal. Formuleblad
heeft ankers/frase-ids/cycle-frames; instance niet. Instance-titel =
frontmatter-`title` (anders bestandsstem). Coria-MXL is instance zonder
recite-collapse.

Andere genres/tonen gebruiken dezelfde mapper (`map_vsa_to_template`) en
renderers; de corpus-CLI is tropaar-toon-4 totdat hun `pitches_status` geen
`provisional` meer is.

## MVSA → MSCZ-partituur (niet template)

Voor litanie/LSATB-export (`mvsa mscz`) gelden aparte normaalvorm-regels:
geen mid-systeem-HBox, geen spacermaat met balklijnen, leidende `|:` zonder
lege maat, `@tekst` als SystemText. Zie
[canonieke checklists — MSCZ S14–S19](../formats/canonical-checklists.md#checklist-mscz-partituur-musescore)
en [MSCZ-leesbaarheid — cues](../formats/mscz-leesbaarheid.md#c--cues-gaps-hbox-accolade).
Template-HBox aan **systeemeinde** (cycle-tekst e.d.) blijft een apart patroon
en hoort niet mid-systeem.

## Regenereren

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
.\.venv\Scripts\python.exe -m pytest tests\test_vsa_template_instance.py tests\test_vsa_template_corpus_mscx.py -q
.\.venv\Scripts\python.exe scripts\render_tropaar_toon4_corpus.py
.\.venv\Scripts\python.exe scripts\render_tropaar_toon4_corpus.py --template
.\.venv\Scripts\python.exe scripts\render_tropaar_toon4_corpus.py --pdf-only
```
