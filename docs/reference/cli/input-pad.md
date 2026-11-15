# Gedeeld CLI-contract — generieke eigenschappen

**Status:** mijlpalen 1–5 gedaan (norm → resolvers → tooling →
bibliotheek → handhaving). Normatieve tekst woont **alleen hier**
(plus C*-definities in de
[contract-index](../../formats/contract-index.md)); man-pages en
bibliotheek-docs **linken**.

Dit is het **CLI-contract** waar C3/C4 naar verwijzen («expliciete
uitzondering»). Het geldt voor `vsa …`, `mvsa …`, `mxl …`, `mscz …`,
`markdown …` en bibliotheek-`scripts\….cmd` — zodat de gebruiker het
verschil tussen lagen niet merkt.

## Wat «generiek» betekent

Elk (sub)commando heeft dezelfde **vaste eigenschappen**, tenzij de
man-pagina een **genoemde** uitzondering heeft (geen stille omzeiling).
Nieuwe commando’s starten vanaf dit contract; geen one-shot pad-/gate-logica
per handler.

| #  | Eigenschap                         | Kort                                                                          |
| -- | ---------------------------------- | ----------------------------------------------------------------------------- |
| G1 | Straat-puur                        | Alleen de bronextensie(s) van die CLI-straat                                  |
| G2 | Padresolutie                       | Bestand / map / korte lookup / catalogus-id — overal hetzelfde                |
| G3 | Canonieke bron (C3)                | Conversie/export **toetst** dat de invoer canoniek is                         |
| G4 | Canonieke doel (C4)                | Conversie/export **levert én toetst** een canonieke uitvoer                   |
| G5 | Uitvoerpaden                       | Sibling/`derived_output_path`; `-o` alleen bij één bron                       |
| G6 | Gedeelde vlaggen                   | Zelfde namen/betekenis (`--dry-run`, `-h` met defaults, …)                    |
| G7 | Exitcodes / foutvorm               | `0` ok, `1` fout; herkenbare NL-fouten                                        |
| G8 | Docs-sync                          | Man-page + `-h` in dezelfde ronde als gedrag                                  |

Diepte per formaat (checklists M*/S*/…): formatpagina’s. Per-commando
C3/C4-status: [cli-canoniciteit-audit](../../formats/cli-canoniciteit-audit.md).
Straatmodel: [straat-CLIs](../../plans/straat-clis.md).

## Aannames (mijlpaal 1)

1. Hub = deze pagina; bibliotheek linkt (geen parallelle norm).
2. Padresolutie-doel = bibliotheek-korte-paden ∪ tooling catalogus-id,
   inclusief **soort-/tussenmappen** (`alleluia`, `communievers`).
3. C3/C4 blijven normatief gedefinieerd in contract-index §C*; **deze
   pagina** is de operationele CLI-spec (wie toetst, uitzonderingen,
   vlaggen).
4. Mijlpaal 2: API in ``vsa.input_paths`` (``resolve_cli_path``,
   soort-map in ``resolve_catalogus_id``, ``collect_cli_sources``);
   bibliotheek ``resolve_user_path`` delegeert.

---

## G1 — Straat-puur (invoer-extensie)

`{straat} {actie}` accepteert **alleen** de bronextensie(s) van die straat
(`.vsa` / `.mvsa` / `.mscz` / MusicXML / …). Vreemde extensie → weigeren
met hint naar de juiste straat (bijv. `.mscz` bij `mvsa mxl` → `mscz mxl`).

**Uitzonderingen** (man-page noemt ze):

| Situatie                    | Toelichting                                      |
| --------------------------- | ------------------------------------------------ |
| `mvsa import` / `mscz import` | Destination-import (bron ≠ straat-extensie)    |
| `mscz compare`              | SCORE mag MusicXML; MVSA = `.mvsa`               |
| Format-CLI `mxl …`          | Eigen MusicXML-straat                            |
| Bibliotheek id-commando’s   | Werken op catalogus-ids, geen bestandsscan       |

---

## G2 — Padresolutie (invoer)

Eén pad-argument betekent overal hetzelfde.

### Resolutievolgorde

1. **Bestaand pad** — absoluut, of relatief t.o.v. de cwd (en in
   bibliotheek-context ook t.o.v. de repository-root):
   - **bestand** met toegestane extensie → precies dat bestand;
   - **map** → recursief (default) alle passende bestanden;
     geneste afgeleiden (`stem.brontype.doeltype`, bijv. `lied.mvsa.mscz`
     bij zoeken op `.mscz`) in een **map**-batch overslaan;
     een **expliciet** bestandspad mag wél genest zijn.
2. Anders **korte lookup** (eerste bestaande kandidaat wint):
   1. zoals getypt (cwd / repo-root);
   2. `content-source/<pad>`;
   3. `content-source/catalogus/<pad>`;
   4. `content-source/koormappen/<pad>`.
3. Anders **catalogus-id** onder catalogus-root(s)
   (`VSA_CATALOGUS` → `./content-source/catalogus` → sibling
   `../bibliotheek/content-source/catalogus`):

| Vorm                              | Voorbeeld                               | Resolutie                                                          |
| --------------------------------- | --------------------------------------- | ------------------------------------------------------------------ |
| Slash-pad (leaf of dieper)        | `tropaar/…/hemelum`                     | Map `catalogus/<id>/` → passende bronnen                           |
| **Soort- of tussenmap**           | `alleluia`, `communievers`              | Map `catalogus/<pad>/` → **alle** passende bronnen eronder         |
| Canonieke stam (`/` → `-`)        | `tropaar-…-hemelum`                     | Uniek bestand met die stem                                         |
| Stam + extensie (gemak)           | `tropaar-…-hemelum.vsa`                 | Alleen als pad niet als bestand bestaat: strip `.vsa`/`.mvsa` …    |

Plakfout uit logs: optionele `:regel` / `:regel:kolom` mag weg vóór
resolutie.

**Lege map** → fout. Ontbrekend pad/id → «Pad niet gevonden» /
«Catalogus-id … niet gevonden».

```cmd
cd /d C:\Git\orthodox-ronl\bibliotheek
scripts\validate.cmd alleluia
vsa validate alleluia
vsa validate communievers
vsa format communievers-kruisverheffing-hemelum.vsa --dry-run
```

---

## G3 / G4 — Canonieke invoer en uitvoer (toetsen)

«Genormaliseerd» / **canoniek** = voldoet aan het formatcontract van dat
type (C2). Conversies en product-exports **mogen niet stil** een
niet-canonieke bron of doel doorlaten.

| Gate | Wanneer                                              | Wat het (sub)commando doet                                      |
| ---- | ---------------------------------------------------- | --------------------------------------------------------------- |
| **C3** | Vóór schrijven van een conversie/product/export    | Toets dat de **bron** canoniek is (non-interactieve validate / structurele check) |
| **C4** | Ná schrijven van het doel                          | Toets dat het **doel** canoniek is (checklist / structurele steekproef) |

Definities C1–C4: [contract-index §Canoniciteit](../../formats/contract-index.md#canoniciteit-en-conversiegates-c).
Implementatie: `vsa.canonicity_gate`. Status per subcommando:
[cli-canoniciteit-audit](../../formats/cli-canoniciteit-audit.md).

### Default voor nieuwe (sub)commando’s

| Soort commando                         | C3     | C4     |
| -------------------------------------- | ------ | ------ |
| Product / export / conversie           | **ja** | **ja** |
| `normalize` (diagonaal → canonieke vorm) | ext/deel; doel moet canoniek worden | **ja** (na write) |
| Authoring-schrijfhulp (`format`, `kuiser`, `zoektekst`, …) | zie man-page; geen stille omzeiling van validate | n.v.t. of deel |
| `validate` / inspect / compare         | **n.v.t.** (mag juist fouten tonen) | **n.v.t.** |

### Expliciete uitzonderingen (geen stille omzeiling)

Elke uitzondering **moet** in de man-pagina staan. Dit is de canonieke
lijst waar C3/C4 naar verwijzen:

| Situatie                            | Gate(s) | Waarom toegestaan                                              |
| ----------------------------------- | ------- | -------------------------------------------------------------- |
| `validate`                          | C3/C4 n.v.t. | Mag niet-canonieke bron tonen/melden                      |
| `parse` / `blocks` / `compare`      | n.v.t.  | Inspectie / rapport, geen conversie                            |
| `syllabify` / `--unsyllabify`       | uitz.   | Bewust (on)canoniek maken van zing-deling                      |
| `--syllabify` op o.a. MXL-export    | C3-opt-in | Expliciete opt-in; **default** eist zing-deling in de bron   |
| `import` / werkbank (`mxl mvsa`, `mscz mvsa`, …) | uitz. | Tussenstadium vóór catalogus-canoniciteit                 |
| `--allow-noncanonical`              | C3 én C4 | Opt-in op products/product-subs; **niet** voor catalogus-publicatie |
| Translit-as-parts / engraving-paden | C4 deels | Documenteer per man-page welke C4-steekproef wegvalt           |
| `markdown pdf` (pagina-PDF)         | geen notatie-P* | Pagina-contract bibliotheek; geen partituur-checklist P* |

**Verboden:** conversie zonder C3 «omdat het handig is»; C4 overslaan
zonder uitzonderingsregel hier of in de man-pagina.

### Normalisatie vs conversie

| Actie | Voorbeeld | Verwachting |
| ----- | --------- | ----------- |
| **Normalize** (diagonaal) | `mvsa normalize`, `mxl normalize`, `mscz normalize` | Zelfde formaat → canonieke vorm; C4 na schrijven |
| **Geen** `vsa normalize` | — | Canonieke `.vsa` via authoring + `vsa validate` |
| **Conversie** | `mvsa mxl`, `vsa products` | C3 bron + C4 doel |

---

## G5 — Uitvoer

| Situatie | Afspraak |
| -------- | -------- |
| Afgeleid product | Sibling via `derived_output_path` (`bronnaam` + doelsuffix); naamgeving `{stam}.{bron}.{doel}` — [canonical-checklists](../../formats/canonical-checklists.md#bestandsnaamgeving-conventie) |
| Map / meerdere bronnen | Per bron een sibling (of uitvoer**map** alleen als de man-pagina dat zegt) |
| In-place authoring | Default: schrijf terug naar het bronbestand |
| `--dry-run` | Preview / rapport; **schrijf niets** |
| `--check` | Geen schrijven; exit ≠ 0 als er iets zou wijzigen; niet met `--dry-run` |
| `-o` + `--dry-run` | Weigeren |
| `-o` / `--keep-*` | Alleen bij precies **één** bronbestand |

---

## G6 — Gedeelde opties

Zelfde **naam** en **betekenis** in tooling en bibliotheek-cmd’s, voor zover
van toepassing:

| Optie | Betekenis (contract) |
| ----- | -------------------- |
| `-h` / `--help` | Hulp; **defaults** zichtbaar |
| `--dry-run` | Geen schrijven; toon resultaat / zou-doen |
| `-o` / `--output` | Enkelvoudig uitvoerpad; alleen bij één bron |
| `--check` | Alleen controleren; niet met `--dry-run` |
| `--allow-noncanonical` | C3/C4-uitzondering (products/product-subs); niet catalogus |
| `--config` | Alternatieve `vsa.toml` (waar de CLI config kent) |

Schrijvende (sub)commando’s **moeten** `--dry-run` hebben (of in de
man-pagina uitleggen waarom niet). Pure `validate` heeft geen `--dry-run`
nodig.

---

## G7 — Exitcodes

| Exitcode | Betekenis |
| -------- | --------- |
| `0` | Succes |
| `1` | Fout of commando mislukt (incl. C3/C4-weigering, `--check` zou wijzigen) |

```cmd
echo %ERRORLEVEL%
```

---

## G8 — Docs-sync

Bij elke CLI-gedragswijziging of nieuw subcommando: man-page,
`-h`-tekst, en dit contract (inventaris / uitzonderingstabel) in
**dezelfde ronde** — zie `.cursor/rules/docs-sync-with-code.mdc`.

---

## Canonieke API (mijlpaal 2 — gedaan)

Module: `src/vsa/input_paths.py`. Bibliotheek
`scripts/input_paths.py` → `resolve_user_path` = `resolve_cli_path`.

| Functie | Rol |
| ------- | --- |
| `resolve_cli_path(raw, *, repo_root=…)` | G2 stappen 1–2 (+ strip locatie-suffix) |
| `collect_cli_sources(raw, *, suffixes=…)` | G1+G2 → niet-lege bestandslijst |
| `resolve_catalogus_id(…)` | Incl. soort-/tussenmap (`alleluia`, …) |
| `reject_multi_with_output(…)` | G5: weiger `-o` bij meerdere bronnen |
| `derived_output_path(…)` | G5 sibling (`vsa.derived_path`) |
| `check_canonical_source` / C4-helpers | G3/G4 (`vsa.canonicity_gate`) |
| `add_allow_noncanonical_arg` | G6 vlag |

**Verboden in handlers:** ad-hoc `Path(…).rglob`, eigen pad-lookup, of
eigen C3/C4 zonder gate. Tooling-handlers gebruiken
`_cli_collect_sources` / `_cli_resolve_existing` / `validate_path` (G2).
*(Scan-test / cursor-handhaving: mijlpaal 5.)*

Tests: `tests/test_input_paths.py` (soort-map, stam, leaf-slash, missing,
locatie-suffix). C3/C4: `tests/test_canonicity_gate.py`.

---

## Gap-analyse: tooling vs bibliotheek (nu)

| Onderwerp | VSA-tooling | Bibliotheek | Contract (doel) |
| --------- | ----------- | ----------- | --------------- |
| Bestaand bestand/map | Ja | Ja | Gelijk |
| Korte pad `content-source` / `catalogus` / `koormappen` | Nee / deels | Ja | Beide (G2) |
| Soort-map `alleluia` | **Ja** (mijlpaal 2) | Ja (map) | Map → alle bronnen |
| Leaf slash-id / stam / `stam.vsa` | Ja | Via tooling-API (resolve) | Beide |
| Locatie-suffix `:regel:kolom` | **Ja** (mijlpaal 2) | Ja (re-export) | Beide |
| Geneste afgeleiden in map-batch | Ja | Deels | Overslaan |
| Straat-puur (G1) | Ja (product-subs) | Via doorgeven | Gelijk |
| C3/C4 toetsen (G3/G4) | Deels (`canonicity_gate`) | Via tooling | Zelfde gates |
| `-o` alleen bij 1 bron | Ja | Ja | Gelijk |
| `--dry-run` / `-h` defaults | Deels | Deels | Pariteit (G6) |
| `validate.cmd alleluia` vs raw `vsa` | Raw faalt | Wrapper werkt | Beide gelijk |

**Pad + handhaving (mijlpaal 2–5):** soort-map + korte lookup in
`vsa.input_paths`; tooling-CLI’s via `_cli_collect_sources` /
`validate_path`; bibliotheek via `resolve_user_path`; scan-test +
AGENTS/cursor-regel afdwingen G2.

**Kern-gap canoniciteit:** audit toont nog open C3/C4 op o.a. strengere
mscz-S*, svg/lyrics-C4 — geen stille «klaar»; zie audit §Samenvatting.

---

## Inventaris (commando’s)

### `vsa`

| Commando | Map? | Extensies / opmerking |
| -------- | ---- | --------------------- |
| `validate` | Ja | `.vsa` / `.md` / `.markdown`; C3/C4 n.v.t. |
| `parse` | Nee | één `.vsa`; inspect |
| `blocks` | Nee | één `.md`; inspect |
| `svg` | Ja | `.vsa`; bij map = uitvoermap |
| `process` | Ja | Markdown-map |
| `build-markdown` | Ja | invoermap |
| `pdf` | Nee* | partituur-PDF (zie man-page; batch via products-straat elders) |
| `resolve-catalogus` | Nee | één `.md` |
| `syllabify` | Ja | `.vsa`; C3/C4-uitz. |
| `format` | Ja | `.vsa`; `--dry-run` |
| `kuiser` | Ja | `.vsa` |
| `text` | Ja | straat-puur / multi — zie man-page |
| `zoektekst` | Ja | `.vsa` / `.mvsa` |
| `mxl` / `musicxml` | Ja | alleen `.vsa`; C3/C4 |
| `products` | Ja | `.vsa`; C3/C4 + `--allow-noncanonical` |
| `audio` | Ja | alleen `.vsa` |
| `template validate` | Ja | `template.yaml` |

### `mvsa`

| Commando | Map? | Extensies |
| -------- | ---- | --------- |
| `validate` | Ja | `.mvsa` |
| `mxl` / `mscz` / `pdf` / `svg` / audio / `score-ir` / `text` / `products` | Ja | alleen `.mvsa`; C3/C4 waar audit «ja» |
| `normalize` / `transpose` / `kuiser` | Ja | `.mvsa` |
| `syllabify` | Ja | uitz. |
| `vsa` | Ja | → sibling `.mvsa.vsa` (E1–E6) |
| `import` | Ja | werkbank-uitz. |

### `mxl` / `mscz`

| Commando | Map? | Opmerking |
| -------- | ---- | --------- |
| `mxl mvsa` / `mscz mvsa` | Ja | werkbank-uitz. |
| `mxl`/`mscz` product-subs + `products` | Ja | straat-puur; C3/C4 zie audit |
| `mxl normalize` / `mscz normalize` | Ja | diagonaal → canoniek |
| `mscz compare` | Nee | SCORE mag MusicXML |
| `mscz import` | Ja | destination-import |

### Bibliotheek (mijlpaal 4)

| Script | Padresolutie | `-h` / `--dry-run` |
| ------ | ------------ | ------------------ |
| `scripts\validate.cmd` | `resolve_cli_path` → tooling G2 | usage; geen schrijven |
| `scripts\products.cmd` | `resolve_user_path` | `CliHelpFormatter`; `--dry-run` |
| `scripts\pdf.cmd` / `index_md_pdf.py` | `resolve_user_path` | `CliHelpFormatter`; `--dry-run` |
| `scripts\layout.cmd` / `apply_mscz_layout.py` | `resolve_user_path` | `make_parser`; `--dry-run` |
| `scripts\opkuisen.cmd` | `resolve_user_path` | `make_parser`; `--dry-run`/`--analyze` |
| `ensure-bibliotheek-id` | `resolve_user_path` | `make_parser`; `--dry-run`=`--check-only` |
| `cleanup-chained-products` | `resolve_user_path` | `make_parser`; default dry-run / `--apply` |
| `bieb accepteer` e.d. | `collect_cli_sources` / ids | `make_parser`; `--dry-run` |
| `bieb hernoem` / `verwijder` / `kopieer` | catalogus-id | buiten G2-bestandsscan |

---

## Handhaving (mijlpaal 5 — gedaan)

1. **Scan-test** — `tests/test_cli_input_contract_scan.py`: elk
   `src/vsa/cli*.py`-entrypoint moet een G2-helper gebruiken; `.rglob(`
   alleen met `# G2-allow: <reden>` (zelfde of vorige regel).
2. **Cursor-regel** — `.cursor/rules/cli-input-bestand-of-map.mdc`.
3. **AGENTS.md** — §6 Gedeeld CLI-contract (G1–G8).
4. **Inventaris** — bij nieuw/gewijzigd subcommando deze pagina + man-page
   in dezelfde ronde bijwerken (C3/C4 + uitzonderingen noemen).

---

## Migratiepad

| Mijlpaal | Inhoud | Status |
| -------- | ------ | ------ |
| **1** | Deze hub (G1–G8 incl. C3/C4 + pad + opties) + gap | gedaan |
| **2** | Canonieke resolvers + unit tests (pad) | gedaan |
| **3** | Migratie VSA-tooling (sub)commando’s | gedaan |
| **4** | Migratie bibliotheek; `-h` / `--dry-run`-parity | gedaan |
| **5** | Scan-test + regels + inventaris + man-pages | **gedaan** |

## Zie ook

- [contract-index §C*](../../formats/contract-index.md#canoniciteit-en-conversiegates-c)
- [cli-canoniciteit-audit](../../formats/cli-canoniciteit-audit.md)
- [straat-CLIs](../../plans/straat-clis.md)
- [CLI-overzicht](index.md) · [specification/cli.md](../../specification/cli.md) (per-commando referentie; generieke regels → **deze** pagina)
