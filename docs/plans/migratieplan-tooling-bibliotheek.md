# Migratieplan: één implementatie per functie (tooling ↔ bibliotheek)

Status: **voorstel** (2026-11-16), niet normatief. Gebaseerd op een analyse van
`VSA-tooling` (`development`, commit `e6893bf`) en `bibliotheek` (`main`).

Bij tegenstrijdigheid gelden de [contract-index](../formats/contract-index.md),
[products-meta](../formats/products-meta.md) en de specificaties.
Verwant: [straat-clis.md](straat-clis.md) (producten per straat) en
[partituur-ir.md](partituur-ir.md) (Score-IR).

## Aanleiding

Terugkerende bugs ("weer stale", fix in de ene exporter breekt de andere,
zelfde woord twee keer anders afgebroken) komen voort uit **dubbele
implementaties**, niet uit losse fouten. Vastgestelde situatie:

- **Meerdere wegen naar MusicXML in tooling:** `export_mvsa_to_musicxml`,
  `export_vsa_to_musicxml`, `export_score_ir_path_to_musicxml`,
  `export_mscz_to_playback_mxl` en `export_bron_to_mxl`. Score-IR wordt maar
  door 8 modules gebruikt, `mvsa_musicxml` door 17.
- **Product-orchestratie twee keer:** tooling (`street_products`,
  `street_product_export`) én bibliotheek (`sync_*_products`, met eigen
  `need_mxl`/`need_svg`-logica en 15 subprocess-aanroepen van `vsa.cli_*`).
- **Versheid twee keer:** `*.products-meta.json` (tooling) én in-file
  stempels (`scripts/product_meta.py`, 621 regels, plus `stamp_ok_or_meta`
  op 18 plekken).
- **Syllaben twee keer:** `syllabify` + woordenlijst in tooling, `nl_hyphen.py`
  met eigen `HYPHEN_EXCEPTIONS` in bibliotheek.
- **Afhankelijkheid van `bron` voor code:** tooling importeert het Python-pakket
  `catalogus` uit de repo `bron` (`catalogus_bridge`, `resolve_catalogus`,
  `include_vsa`, `markdown_include`). Het pakket `catalogus` is klein en zelfstandig
  (9 modules, circa 2.200 regels, alleen PyYAML als afhankelijkheid).
- **Naamconflict `catalogus`:** het pakket in `bron`, de eigen module
  `scripts/catalogus.py` in bibliotheek (catalogus-root en id's) en een niet
  verwant PyPI-pakket heten alle drie `catalogus`. Welke een `import catalogus`
  oplevert hangt af van pad en installatie. De losse map
  `C:\Git\orthodox-ronl\catalogus` is oud en ongebruikt en telt niet mee;
  de catalogus van stukken staat in bibliotheek.
- **Godsbestanden:** `cli.py` (4.470 regels), `mvsa_musicxml.py` (3.168),
  `index_md_pdf.py` in bibliotheek (2.989).

## Doelbeeld

- **VSA-tooling** is de enige plek voor "wat betekent dit bestand" en "hoe
  maak ik product X": parse, validate, syllaben/woordenlijst, Score-IR,
  export, products-meta, padcontract.
- **bibliotheek** beslist alleen "wat staat in de catalogus, wanneer, voor
  welke site": bladeren, handmatig/import overslaan, lifecycle, R2/Hugo, dunne
  CLI's die de tooling-API aanroepen.
- **`bron` levert geen code meer aan tooling.** Alle code die tooling uit
  `bron` haalt, komt in tooling zelf (stap 4); `bron` verdwijnt daarna als
  codeafhankelijkheid, en op termijn uit de keten.
- Eén functie = één implementatie. Dunne wrappers (zoals
  `bibliotheek/scripts/input_paths.py` en `street_meta.py`) zijn het patroon.

## Uitgangspunten

1. Niet alles in één run: **één branch en één PR per stap**.
2. **Vangnet vóór refactor:** geen kernexporter ontleden zonder golden- en
   contracttests (stap 5).
3. **Geen geschiedenis herschrijven** van `development`: de wip-commit is al
   gepusht. Herstel gaat via nieuwe commits met duidelijke berichten.
4. Elke stap heeft een meetbaar **klaar-als**; een stap waarvan het klaar-als
   niet gehaald is, is niet af.
5. Of Score-IR de enige hub wordt, is een **besluit** (stap 3), geen aanname.

## Werkafspraken (uit de Cursor-regels van VSA-tooling)

Elke stap wordt uitgevoerd volgens dezelfde regels die Cursor al gebruikt
(`AGENTS.md` en `.cursor/rules`):

- **Model:** `cost-control.mdc` staat standaard alleen Composer of Grok toe.
  Staat bij een stap Sonnet 5.5, Opus 5.5 of Fable 5.2, dan noem je dat model
  uitdrukkelijk in het bericht aan Cursor.
- **Één run, één mijlpaal:** bij een dure of onduidelijke opdracht stopt de
  agent, stelt een goedkoper pad voor en wacht op jouw OK.
- **Branch:** noem in elk bericht de branch (`branch-afstemming.mdc`). De agent
  wisselt niet stil van branch.
- **Commits en pushes:** alleen op uitdrukkelijk verzoek (`AGENTS.md`).
  Pull-request-commando's worden eerst voorgesteld.
- **Contracten eerst:** bij werk aan export, melisma, recite of producten opent
  de agent eerst `docs/formats/contract-index.md` en noemt het contract-id
  (`contracten-eerst.mdc`).
- **Documentatie in dezelfde ronde:** bij elke gedragswijziging werkt de agent
  man-pagina's, handleidingen en format-hubs mee bij
  (`docs-sync-with-code.mdc`).
- **Terminologie:** regels R1-R5 uit `bron/docs/specs/terminologie.md`.
- **Wijzigingen aan de VSA-specificatie** (ook het verhuizen van catalogus-specs
  in stap 4) beginnen met een Wijzigingsanalyse volgens `AI-INSTRUCTIONS.md`.
- **Commando's voor jou:** één plakbaar cmd-blok met `cd /d` en Windows-paden
  (`copy-pasteable-cli-commands.mdc`).

## Stappen

### 1. Baseline (tooling)

- Uitvoerder: Sonnet 5.5 (Cursor of Claude Code), in drie korte runs.
- 1a. Python 3.14-omgeving opzetten, volledige testsuite draaien, rode
  tests inventariseren en oorzaak per test vastleggen.
- 1b. Rode tests herstellen met kleine commits (code of test, per geval
  gemotiveerd); CHANGELOG bijwerken waar gedrag verandert.
- 1c. CI: `bron` pinnen op tag of commit in plaats van `ref: main` (tijdelijk,
  tot stap 4), en een Linux-testjob toevoegen naast Windows.
- Klaar als: `development` groen op CI (Windows en Linux) en een tag
  `baseline-2026-11` is gezet.

### 2. Inventaris (beide repos, alleen document)

- Uitvoerder: Sonnet 5.5 (leeswerk, geen code).
- Maak `docs/plans/migratiematrix.md`: taak → canonieke tooling-module →
  kopie in bibliotheek → besluit (verwijderen, wrapper of bewust
  bibliotheek-eigen), met bestandsnamen en regelaantallen.
- Klaar als: elke genoemde duplicaat uit "Aanleiding" een rij heeft en geen
  rij zonder besluit blijft.

### 3. Besluit en contract

- Uitvoerder: Opus 5.5 of Fable 5.2 (ontwerpafweging), met jou als beslisser.
- Leg in een korte ADR vast: canonieke exportketen
  (bron → normalize → Score-IR → afgeleiden, of een bewust andere keten),
  welke functies de publieke API vormen, en hoe bibliotheek de tooling-versie
  pint (er bestaat al `vsa-tooling.pin` met `bump-vsa-tooling-pin.cmd`; dat
  bestaande mechanisme wordt vastgelegd, er komt geen nieuw ontwerp). Beslis ook de naam en
  plek van de catalogus-code in tooling (stap 4) en waar de data
  (`zangstukken/`, `alias-blokken.yaml`) blijft.
- Voorstel: [adr-001-exportketen-en-catalogus.md](adr-001-exportketen-en-catalogus.md),
  met per vraag opties, een aanbeveling en een kolom voor het besluit.
- Klaar als: ADR gemerged en in de contract-index gelinkt.

### 4. Catalogus-code naar tooling (`bron` eruit)

- Uitvoerder: Sonnet 5.5; naam en API-grens volgen uit het ADR van stap 3.
- Het pakket `catalogus` uit `bron` (`alias_index`, `alias_blokken`,
  `alias_sync`, `zoek`, `include_ref`, `normalize`, `errors`, `cli`) verhuist
  mee met zijn tests (`test_alias_*`, `test_catalogus_zoek`) en fixtures naar
  tooling, als subpakket (voorstel `vsa.catalogus`, niet als top-level
  `catalogus`, vanwege het naamconflict).
- Tooling gaat over op de eigen code: `catalogus_bridge`, `resolve_catalogus`,
  `include_vsa`, `markdown_include` en `tests/test_catalogus_package_guard.py`.
  De dependency `catalogus>=0.1.0`, de bootstrap-stap en de CI-checkout van
  `bron` voor code vervallen.
- Het zoeken naar een `bron`-map met `zangstukken/` (nu hard in `cli.py`,
  `catalogus_bridge.py`, `markdown_include.py`) wordt een instelbare
  data-root (bijvoorbeeld in `vsa.toml`), zodat tooling niet meer aan een
  map met de naam `bron` vastzit.
- De inventaris van stap 2 moet laten zien welke consumenten in bibliotheek
  en `bron` het pakket gebruiken (19 bibliotheek-scripts importeren een module
  `catalogus`; een deel daarvan is de eigen `scripts/catalogus.py`).
  Hernoem `scripts/catalogus.py` in bibliotheek (bijvoorbeeld naar
  `catalogus_root.py`), zodat de naam `catalogus` vrijkomt.
- Klaar als: `pip install vsa-tool` werkt zonder `bron`, tooling heeft geen
  `import catalogus` meer, de meeverhuisde tests zijn groen in tooling, en de
  CI checkt `bron` niet meer uit voor code.

### 5. Vangnet

- Uitvoerder: Sonnet 5.5.
- Lees eerst de [contract-index](../formats/contract-index.md) en de
  [checklists](../formats/canonical-checklists.md). Schrijf daarna golden- en
  contracttests voor MXL, SVG en MSCZ in tooling. Elke test noemt het
  contract-id in zijn naam of docstring.
- Dekken in elk geval: same-pitch melisma (M5a voor MXL; S13 en R7 voor MSCZ),
  melisma-lyrics (K2, K3), recite-playback zonder print-collapse (M10) en de
  partituurlayout (S2, S4).
- Klaar als: elk bekend regressiegeval, bijvoorbeeld same-pitch melisma, in
  precies één pytest in tooling faalt en die test zijn contract-id noemt.

### 6. Versheid

- Uitvoerder: Sonnet 5.5.
- Bibliotheek controleert en synct alleen nog op products-meta
  (`vsa.products_meta.freshness`). Eenmalig migratiescript voor bestaande
  stempels; stamp-fallback weg.
- Klaar als: `stamp_ok_or_meta` nergens meer voorkomt en
  `scripts/product_meta.py` weg is of alleen nog een dunne wrapper.

### 7. Syllaben

- Uitvoerder: Sonnet 5.5.
- Voeg `HYPHEN_EXCEPTIONS` samen in `data/syllable_dictionary.nl.txt`
  (waar `vsa.toml` al naar verwijst). Test dat tooling-syllabify voor elke
  uitzondering dezelfde splitsing geeft; `nl_hyphen.py` wordt wrapper en
  daarna verwijderd.
- Besluiten (2026-11-20, door de eigenaar): `eeuwen` wordt `eeu-wen`, conform
  het woordenboek in bibliotheek; de uitzondering `eeuw-en` in `nl_hyphen.py`
  vervalt. `koninkrijk` blijft `ko-nink-rijk`. Het woordenboek wijzigt verder
  niet, behalve dat de overige uitzonderingen die er nog niet in staan worden
  toegevoegd (12 woorden, zie de migratiematrix).
- Klaar als: `nl_hyphen.py` weg is en geen consument meer eigen
  uitzonderingen bijhoudt.

### 8. Product-sync dun maken

- Uitvoerder: Sonnet 5.5, één script per run.
- Volgorde: `sync_mvsa_products`, `sync_vsa_products`, `sync_mscz_products`,
  `sync_audio_products`, `sync_lyrics_products`, `sync_tekstblad_products`.
  Elk delegeert aan de tooling-API; bibliotheek houdt alleen filter en beleid.
- Klaar als: geen `need_mxl`/`need_svg`-logica meer in bibliotheek en per
  script één smoke-test die bewijst dat de tooling-API wordt aangeroepen.

### 9. Export-kern ontleden (tooling)

- Uitvoerder: Opus 5.5 of Fable 5.2.
- `mvsa_musicxml.py` opsplitsen per slice, in lijn met het ADR uit stap 3;
  melisma, recite en layout in één codepad via de contract-hub. Na elke
  slice moeten de tests uit stap 5 groen zijn. Volgens
  `mvsa-export-contracten.mdc` wordt een nieuwe of gewijzigde regel (M5a, M10,
  S13 en verwante regels) in dezelfde pull request in `canonical-checklists.md`
  bijgewerkt.
- Klaar als: geen exporter meer een eigen kopie van melisma/recite-logica
  heeft en `mvsa_musicxml.py` aanmerkelijk kleiner is.

### 10. Opruimen

- Uitvoerder: Sonnet 5.5 (Haiku 5.5 voor de mechanische klussen).
- `cli.py` opsplitsen (één module per subcommando, patroon `kuiser_cli.py`),
  `index_md_pdf.py` uitdunnen, ruff toevoegen, rommel in de root opruimen
  (`_fix_tests2.py`, `README-step*.md`, `.tmp-bron-specs/`).
- Klaar als: de lijst in "Aanleiding" geen open punten meer heeft.

## Succesmaat

Een regressie (bijvoorbeeld same-pitch melisma) faalt in **één** pytest in
tooling. Bibliotheek heeft voor die regressie geen parallelle assert meer,
alleen een smoke-test die bewijst dat de tooling-API is aangeroepen.

## Open punten

- Score-IR als enige hub (stap 3).
- Subprocess versus in-process: het probleem is dubbel beleid, niet het
  subprocess zelf. In-process vraagt een stabiele API en een gepinde versie.
- Data versus code: `zangstukken/` en `alias-blokken.yaml` zijn inhoud, geen
  code. Moeten `zangstukken/` en `alias-blokken.yaml` in `bron` blijven, naar
  bibliotheek of naar tooling? Het antwoord bepaalt of `bron` echt "eruit" kan
  of alleen als codeafhankelijkheid.
- Normatieve catalogus-specs (`bron/docs/specs/catalogus-*.md`) en de
  `catalogus`-CLI-handleidingen horen bij de code; per document beslissen of
  ze mee verhuizen of vanuit tooling naar `bron` blijven linken.
- Cross-repo wijzigingen raken twee repos: per stap afspreken welke PR eerst
  mergt.
