# Migratiematrix: tooling en bibliotheek

Status: **inventaris** (2026-11-20), niet normatief. Dit is stap 2 van het
[migratieplan](migratieplan-tooling-bibliotheek.md). Het document wijzigt geen
code; het legt vast wat waar staat en wat het voorlopige besluit per rij is.

## Peildatum en werkwijze

- **VSA-tooling:** branch `ci-woordenboek`, commit `e55d2cd`.
- **bibliotheek:** branch `development`, commit `12ae194`.
- **bron:** branch `main`, commit `ee369a9` (2026-10-03).
- Regelaantallen zijn met `wc -l` geteld. Aantallen van aanroepen en imports
  komen uit zoekpatronen in de broncode (`grep`). Ze zijn bruikbaar als
  ordegrootte, maar niet als sluitende telling.
- Tests zijn niet gedraaid. Er is geen code uitgevoerd.
- Rijen met "eerst vergelijken" hebben nog geen definitief besluit: daarvoor
  moeten de twee implementaties naast elkaar worden gelegd. Dat gebeurt in de
  genoemde stap. Het stapcriterium "geen rij zonder besluit" is daarmee nog
  niet gehaald voor die rijen.

## 1. Meerdere wegen naar MusicXML (tooling)

| Taak                     | Canoniek in tooling                                                   | Kopie of eigen variant elders                                            | Besluit                                     |
| ------------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------- |
| MusicXML maken uit .mvsa | `mvsa_musicxml.py` 3.168 r., `export_mvsa_to_musicxml` (r. 441)       | Geen eigen kopie in bibliotheek; aanroep via `vsa.cli_mvsa` (subprocess) | Bewust tooling-eigen; opsplitsen in stap 9  |
| MusicXML maken uit .vsa  | `vsa_musicxml_export.py` 68 r., `export_vsa_to_musicxml`              | Geen                                                                     | Eerst vergelijken met de .mvsa-weg (stap 9) |
| MusicXML uit Score-IR    | `score_ir_musicxml.py` 299 r., `export_score_ir_path_to_musicxml`     | Geen                                                                     | Eerst vergelijken (stap 9)                  |
| Playback-MXL uit .mscz   | `musicxml_playback_normalize.py` 99 r., `export_mscz_to_playback_mxl` | Geen                                                                     | Eerst vergelijken (stap 9)                  |
| MXL uit bron (straat)    | `street_product_export.py` 225 r., `export_bron_to_mxl` (r. 195)      | Geen                                                                     | Eerst vergelijken (stap 9)                  |

Score-IR wordt door 8 modules gebruikt, `mvsa_musicxml` door 18. De vijf
functies zijn niet in bibliotheek gekopieerd; het probleem zit binnen tooling.

## 2. Product-orkestratie

| Taak                                                      | Canoniek in tooling                                                    | Kopie of eigen variant elders                                                                                                                                                                                                                                                                                      | Besluit                                                                                                         |
| --------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Producten genereren (orkestratie)                         | `street_products.py` 694 r. en `street_product_export.py` 225 r.       | `sync_mvsa_products.py` 690, `sync_vsa_products.py` 666, `sync_mscz_products.py` 390, `sync_tekstblad_products.py` 269, `sync_lyrics_products.py` 233, `sync_audio_products.py` 230, `sync_import_mvsa.py` 234, `translit_svg_products.py` 411, `product_regen.py` 221 en `products.py` 286 (samen circa 3.630 r.) | Dunne wrapper (stap 8): bibliotheek bepaalt welke UV's, welke kinds en welk beleid; tooling doet het exporteren |
| Wanneer is een product verouderd (`need_mxl`, `need_svg`) | `products_meta.freshness` in `products_meta.py`                        | `need_*`-logica in `sync_mvsa_products.py` (r. 201-215) en `sync_mscz_products.py`                                                                                                                                                                                                                                 | Verwijderen; vervangen door `freshness` (stap 6)                                                                |
| Aanroepen van de vsa-CLI                                  | `vsa.cli`, `vsa.cli_mvsa`, `vsa.cli_mscz`, `vsa.cli_md`, `vsa.cli_mxl` | Circa 19 aanroepen in 10 bestanden (sync_*, translit_svg_products, product_regen, bieb_accepteer, index_md_pdf)                                                                                                                                                                                                    | Houden als subprocess of in-process omzetten: open punt voor het ADR in stap 3                                  |

## 3. Versheid

| Taak                                 | Canoniek in tooling                  | Kopie of eigen variant elders                                                                                                                                    | Besluit                                                            |
| ------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Sidecar `*.products-meta.json`       | `products_meta.py` 303 r. (schema 2) | `street_meta.py` 129 r. in bibliotheek: eigen kopie van schema 2, geen import                                                                                    | Dun maken: importeren uit `vsa.products_meta` (stap 6)             |
| Herkomststempels in het bestand zelf | Geen (bewust niet: versheid = meta)  | `product_meta.py` 622 r.; fallback via `stamp_ok_or_meta` (16 aanroepen: sync_vsa 5, sync_mvsa 4, translit_svg_products 4, sync_mscz 3, street_meta 1 definitie) | Verwijderen zodra geen enkel product meer `no_meta` heeft (stap 6) |

## 4. Lettergrepen

| Taak                                      | Canoniek in tooling                                                                                                                                              | Kopie of eigen variant elders                                                                                                              | Besluit                                                                                                                 |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Woorden in lettergrepen verdelen          | `syllabify.py` 730, `dutch_syllables.py` 147, `syllable_dictionary.py` 519, `syllable_dict_check.py` 1.976, `mvsa_syllabify.py` 812, `syllabify_validate.py` 136 | `nl_hyphen.py` 195 r. met eigen `HYPHEN_EXCEPTIONS`; gebruikt door `cleanup_capella_mxl.py` (706 r.) en `mscz_content_cleanup.py` (523 r.) | Vervangen door de tooling-API (stap 7), maar eerst alle uitzonderingen vergelijken met het woordenboek; zie open punten |
| Nakijklijst van meerlettergrepige woorden | Geen                                                                                                                                                             | `syllabe_woordlijst.py` 153 r.                                                                                                             | Bewust bibliotheek-eigen; gebruik van de tooling-API controleren (stap 7)                                               |
| Syllabify aanroepen vóór export           | `vsa.syllabify.syllabify_vsa_source`                                                                                                                             | `sync_vsa_products.py` (r. 138-143) gebruikt die al                                                                                        | Geen actie nodig                                                                                                        |

## 5. Catalogus-code en `bron`

| Taak                                                                      | Canoniek in tooling                                                                                                                                                                               | Kopie of eigen variant elders                                                                                                                                                                                                       | Besluit                                                                                             |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Catalogus-pakket (zoeken, alias-blokken, alias-sync, include-referenties) | Geen; tooling importeert het uit de repo `bron` via `catalogus_bridge.py` 50 r., `resolve_catalogus.py` 250 r., `include_vsa.py` 289 r., `markdown_include.py` 543 r. (4 modules, 7 importregels) | `bron`, `src/catalogus/`: 9 modules, 2.189 r. (`alias_index` 655, `zoek` 426, `cli` 392, `alias_sync` 389, `alias_blokken` 149, `errors` 85, `__init__` 41, `include_ref` 35, `normalize` 17). Laatste commit op `main`: 2026-10-03 | Verhuizen naar `vsa.catalogus` met tests en fixtures; `bron` verdwijnt als codebron (stap 4)        |
| Pakket `catalogus` gebruikt door bibliotheek                              | Niet van toepassing                                                                                                                                                                               | Geen enkel bibliotheek-script gebruikt de API van het `bron`-pakket (`AliasIndex`, `zoek_met_roots`, `ZoekContext`, `alias_*`): 0 treffers in `scripts/`. Buiten `scripts/` niet doorzocht                                          | Controle buiten `scripts/` (hugo-lagen, docs) hoort bij stap 4                                      |
| Catalogus-root, id's, titels, verwijzingen oplossen                       | Geen                                                                                                                                                                                              | `scripts/catalogus.py` 787 r. (`parse_id`, `folder`, `resolve_existing_ref`, `derived_leaf_title`, ...)                                                                                                                             | Bewust bibliotheek-eigen (beleid en bestandsstructuur); hernoemen naar `catalogus_root.py` (stap 4) |

## 6. Mogelijk dubbel werk dat nog niet is vergeleken

| Taak                                        | Canoniek in tooling                     | Kopie of eigen variant elders                                                                   | Besluit                                          |
| ------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Gedeeld CLI-invoercontract (bestand of map) | `input_paths.py` in tooling             | `input_paths.py` 172 r. in bibliotheek; de laatste commit (`12ae194`) noemt "tooling-resolvers" | Eerst vergelijken of het nu een dunne wrapper is |
| CLI-stijl en -berichten                     | `cli_messages.py`                       | `cli_style.py` 725 r. en `cli_help.py`                                                          | Eerst vergelijken                                |
| MSCZ opschonen en layout                    | `mscz_layout.py`, `mvsa_mscz.py` 562 r. | `mscz_content_cleanup.py` 523, `apply_mscz_layout.py` 262, `staff_clefs.py` 290                 | Eerst vergelijken (stap 9)                       |
| Coria-MXL en Capella-opschoning             | `musicxml_coria_timing.py`, `coria.py`  | `coria_mxl.py` 336, `fingerprint_coria_mxl.py` 257, `cleanup_capella_mxl.py` 706                | Eerst vergelijken (stap 9)                       |

## 7. Bewust bibliotheek-eigen

| Taak                             | Canoniek in tooling | Kopie of eigen variant elders                                                                                      | Besluit                                                                |
| -------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Beheer van de catalogus (`bieb`) | Geen                | `bieb_accepteer.py` 1.295, `bieb_hernoem.py` 586, `bieb_verwijder.py` 600, `bieb_kopieer.py` 408, `bieb_fs.py` 242 | Bewust bibliotheek-eigen                                               |
| Opkuisen en lifecycle            | Geen                | `opkuisen.py` 595, `opkuis_detect.py` 366, `opkuis_io.py`, `lifecycle_grenzen.py`                                  | Bewust bibliotheek-eigen                                               |
| PDF-blad en publicatie           | Geen                | `index_md_pdf.py` 3.005 r., `r2_pdf_upload.py` 573                                                                 | Bewust bibliotheek-eigen; `index_md_pdf.py` later opsplitsen (stap 10) |
| Repo-beheer                      | Geen                | `seed_repo.py` 858, `fix.py` 571, `commit_sources.py` 449                                                          | Bewust bibliotheek-eigen                                               |

## 8. Naamconflict

| Taak                     | Canoniek in tooling                         | Kopie of eigen variant elders                                                                                                                                                                    | Besluit                                              |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Naamconflict `catalogus` | In tooling bestaat alleen het `bron`-pakket | Drie verschillende dingen heten `catalogus`: het pakket in `bron`, `scripts/catalogus.py` in bibliotheek (geïmporteerd door 16 bestanden: 11 scripts en 5 tests) en een niet-verwant PyPI-pakket | Oplossen in stap 4: bibliotheek hernoemt zijn module |

## 9. Grote bestanden

| Bestand                            | Regels | Besluit                                          |
| ---------------------------------- | ------ | ------------------------------------------------ |
| `cli.py` (tooling)                 | 4.768  | Opsplitsen in stap 9; geen verandering in gedrag |
| `mvsa_musicxml.py` (tooling)       | 3.168  | Opsplitsen in stap 9                             |
| `syllable_dict_check.py` (tooling) | 1.976  | Niet in het plan genoemd; kandidaat voor stap 9  |
| `index_md_pdf.py` (bibliotheek)    | 3.005  | Opsplitsen in stap 10                            |

## Afwijkingen ten opzichte van het migratieplan

Bij het natellen zijn de volgende getallen anders dan in het plan.

| Onderwerp                                                    | Plan  | Nu geteld                                                          |
| ------------------------------------------------------------ | ----- | ------------------------------------------------------------------ |
| Scripts in bibliotheek die een module `catalogus` importeren | 19    | 16 (11 scripts en 5 tests)                                         |
| Plekken met `stamp_ok_or_meta`                               | 18    | 16 aanroepen in 5 bestanden, plus de definitie in `street_meta.py` |
| Subprocess-aanroepen van `vsa.cli*` in bibliotheek           | 15    | Circa 19 in 10 bestanden (grove telling)                           |
| Modules die `mvsa_musicxml` noemen                           | 17    | 18                                                                 |
| `cli.py` (tooling)                                           | 4.470 | 4.768                                                              |
| `index_md_pdf.py` (bibliotheek)                              | 2.989 | 3.005                                                              |
| `product_meta.py` (bibliotheek)                              | 621   | 622                                                                |

De getallen in het plan zijn een momentopname die ouder is; geen van de
afwijkingen verandert de volgorde van de stappen.

## Open punten

1. **Uitzonderingen in `nl_hyphen.py` tegenover het woordenboek.** De lijst
   `HYPHEN_EXCEPTIONS` bevat afbrekingen die kunnen afwijken van de
   woordenlijst en van de regels in de [syllabificatie-specificatie](../formats/syllabificatie.md).
   Voorbeeld: `eeuwen` staat er als `eeuw-en`, terwijl de conventie in tooling
   `eeu-wen` lijkt te zijn (niet gecontroleerd). Vóór stap 7: alle
   uitzonderingen naast het woordenboek leggen en per verschil beslissen.
2. **Zoeken buiten `scripts/`.** Alleen `scripts/` van bibliotheek is
   doorzocht op gebruik van het `bron`-pakket. Hugo-lagen, documentatie en
   workflows zijn niet nagelopen.
3. **Subprocess of in-process.** Ongeveer 19 aanroepen gaan via een subprocess
   naar de CLI van tooling. Of dat zo blijft, is een ontwerpkeuze voor het ADR.
4. **Rijen onder "eerst vergelijken".** De vier exportfuncties zonder besluit
   (sectie 1), de vier vergelijkingen in sectie 6 en de uitzonderingen uit
   punt 1 vragen een inhoudelijke vergelijking voordat er een besluit valt.
