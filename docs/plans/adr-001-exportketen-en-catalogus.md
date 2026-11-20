# ADR-001 (voorstel): exportketen, publieke API en catalogus-code

Status: **voorstel, wacht op besluit** (2026-11-20). Niet normatief. Dit is stap 3
van het [migratieplan](migratieplan-tooling-bibliotheek.md). Het document wijzigt
geen code. Zodra de keuzes hieronder zijn gemaakt, wordt de status "aangenomen"
en volgt een link in de [contract-index](../formats/contract-index.md).

Gebruikte feiten komen uit de broncode van `VSA-tooling` (`development`),
`bibliotheek` (`development`, `12ae194`) en `bron` (`main`, `ee369a9`). Er is niets
uitgevoerd of getest. Wat niet is gecontroleerd, staat er expliciet bij.

## Wat je moet beslissen

| Nr  | Vraag                                                | Aanbeveling                                                               | Jouw keuze |
| --  | --------------------------------------------------   | -----------------------------------------------------------------------   | ---------- |
| 1   | Welke exportketen is de canonieke?                   | **Keuze C**: gefaseerd, één MusicXML-renderer, Score-IR blijft schermlaag |            |
| 2   | Hoe roept bibliotheek tooling aan?                   | **Keuze 2a**: één API-module `vsa.api`, in-process                        |            |
| 3   | Hoe pint bibliotheek de tooling-versie?              | Bestaand mechanisme vastleggen (geen nieuw ontwerp)                       |            |
| 4   | Hoe heet de catalogus-code in tooling?               | **Keuze 4a**: subpakket `vsa.catalogus`, opdracht `vsa catalogus`         |            |
| 5   | Waar blijft de data (`zangstukken/`, alias-blokken)? | **Keuze 5a**: voorlopig in `bron`, met instelbare data-root               |            |

Je mag per rij "akkoord" zeggen of een andere letter kiezen. Rij 3 hoeft alleen
een "akkoord".

## 1. Exportketen

### Wat er nu is

Er zijn twee volledige MusicXML-renderers:

- `mvsa_musicxml.py` (3.168 regels) voor `.mvsa`;
- `musicxml_renderer.py` (937 regels) voor `.vsa`, aangeroepen via
  `vsa_musicxml_export.py`.

Beide bevatten melisma-logica, net als `score_ir.py` en `score_ir_musicxml.py`.
Daar komen de terugkerende bugs vandaan: een fix in de ene renderer raakt de andere
niet. `export_bron_to_mxl` is geen derde renderer, maar kiest op bestandsextensie
tussen deze wegen (zie `docs/plans/migratiematrix.md`, sectie 1; dat bestand staat nog op de branch `migratiematrix`).

Score-IR (`score_ir.py`) is bedoeld voor schermweergave en de partituurlaag, niet
als vervanging van MusicXML (zie [partituur-ir.md](partituur-ir.md), "Non-goals").

### Opties

| Keuze | Beschrijving                                                                                                                                                                                                           | Voordeel                                                           | Nadeel                                                                                                             |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| A     | Score-IR wordt de enige hub: bron → Score-IR → MXL, MSCZ, SVG, PDF.                                                                                                                                                    | Eén plek voor melisma en recite.                                   | Zeer grote ombouw van `mvsa_musicxml.py`. Score-IR bevat bewust geen MusicXML-details. Hoog risico zonder vangnet. |
| B     | Alles laten zoals het is; alleen afspraken over wie wat mag wijzigen.                                                                                                                                                  | Geen werk.                                                         | Lost de dubbele melisma-logica niet op. Het probleem uit "Aanleiding" blijft.                                      |
| C     | Gefaseerd: eerst vangnet (stap 5), dan één MusicXML-renderer voor notatiebronnen en één gedeelde melisma/recite-module. Score-IR blijft de laag voor scherm en partituur. Later heroverwegen of Score-IR de hub wordt. | Kleine, controleerbare stappen. Past bij de volgorde van het plan. | Duurt langer; tijdelijk blijven twee lagen bestaan.                                                                |

### Aanbeveling: keuze C

Redenen:

1. Het plan eist vangnet vóór refactor (uitgangspunt 2). Keuze A zou dat omkeren.
2. De `.vsa`-weg kan naar de `.mvsa`-renderer: `convert_vsa_to_mvsa` bestaat al in
   `vsa_mvsa.py` en accepteert een optioneel template. **Niet gecontroleerd:** of de
   uitvoer daarmee voor alle `.vsa`-bestanden gelijk blijft aan de huidige uitvoer.
   Dat toetst stap 5 met golden-tests vóórdat iets wordt omgezet.
3. De hub-vraag (Score-IR voor alles) kan na stap 9 opnieuw worden gesteld, met
   het vangnet op zijn plek.

Gevolgen van keuze C voor de stappen: stap 5 schrijft ook golden-tests voor het
huidige `.vsa`-resultaat; stap 9 splitst `mvsa_musicxml.py` en brengt de
`.vsa`-weg erbij; `musicxml_renderer.py` verdwijnt pas als de golden-tests groen
blijven.

## 2. Publieke API en aanroepwijze

### Wat er nu is

Bibliotheek roept tooling op twee manieren aan: ongeveer 19 keer als subprocess
(`vsa.cli_*`) en op tientallen plekken in-process (bijvoorbeeld `vsa.parser`,
`vsa.mscz_layout`, `vsa.input_paths`). Er is geen lijst met functies die stabiel
mogen zijn, dus elke interne hernoeming kan bibliotheek breken.

### Voorstel (keuze 2a)

- Eén module `vsa.api` is de enige plek waar bibliotheek uit mag importeren. Alles
  achter die module is intern en mag wijzigen.
- Eerste inhoud, uit bestaande functies:

| Taak                              | Bestaande functie (wordt doorverwezen)                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Product maken uit een bron        | `export_bron_to_mxl`, `export_bron_to_mscz_product`, `export_bron_to_score_ir`, `export_bron_to_partituur_pdf` (`street_product_export.py`) |
| Is een product verouderd          | `products_meta.freshness`                                                                                                                   |
| Meta lezen en schrijven           | `products_meta.load_meta`, `write_meta`                                                                                                     |
| Lettergrepen                      | `syllabify.syllabify_plain_text`, `syllabify_vsa_body`                                                                                      |
| Pad van de gebruiker oplossen     | `input_paths.resolve_cli_path`, `collect_cli_sources`                                                                                       |
| Catalogus zoeken                  | `vsa.catalogus` (zie keuze 4)                                                                                                               |

- **In-process is de standaard.** Een subprocess blijft alleen waar proces-isolatie
  nodig is, bijvoorbeeld voor het starten van MuseScore. Reden: het probleem is
  dubbel beleid, niet het subprocess zelf (zie "Open punten" in het plan); een
  gepinde API maakt in-process veilig.
- Elke wijziging in `vsa.api` krijgt een regel in `CHANGELOG.md`; een brekende
  wijziging verhoogt het versienummer in `pyproject.toml`.

Alternatief (2b): alles via de CLI als subprocess laten lopen. Dat is langzamer,
maakt foutafhandeling moeilijker en lost dubbel beleid niet op.

## 3. Pinnen van de tooling-versie

Dit legt het bestaande mechanisme vast; er komt geen nieuw ontwerp.

- Bibliotheek heeft het bestand `vsa-tooling.pin` met één verwijzing (tag of
  commit). De workflow `pages.yml` leest die verwijzing voor de productie-site
  en voor de `development`-preview (`tooling_mode=pin`). Previews van andere
  branches "floaten" op `main` van tooling (`tooling_mode=float`); alleen de
  branch `feat/products-meta-consumer` is tijdelijk gepind.
- `scripts/bump-vsa-tooling-pin.cmd` zet de pin op een nieuwe verwijzing
  (standaard `main`); de gebruiker commit zelf. **Niet gecontroleerd:** of dat
  script `main` omzet naar een vaste commit of de naam `main` laat staan. Een pin
  op de naam `main` is niet reproduceerbaar; dat wordt in stap 8 nagelopen.
- Regel die wordt toegevoegd: bibliotheek verhoogt de pin pas na een groene CI van
  tooling, en de PR die de pin verhoogt noemt de `CHANGELOG`-regels die erbij
  horen.

## 4. Naam en plek van de catalogus-code

### Wat er nu is

Het pakket `catalogus` in `bron` (`src/catalogus/`, 9 modules, 2.189 regels,
alleen PyYAML nodig) levert zoeken, alias-blokken en id-gebaseerde includes. Tooling
importeert het via `catalogus_bridge.py`, `resolve_catalogus.py`, `include_vsa.py` en
`markdown_include.py`. Drie dingen heten `catalogus` (`bron`-pakket,
`bibliotheek/scripts/catalogus.py`, een niet-verwant PyPI-pakket).
Bibliotheek gebruikt de API van het `bron`-pakket nergens (`docs/plans/migratiematrix.md`, open punt 2).

### Voorstel (keuze 4a)

- De code verhuist naar het subpakket `vsa.catalogus`, samen met de tests
  (`test_alias_*`, `test_catalogus_zoek`) en fixtures.
- De opdracht wordt `vsa catalogus …` (subopdracht) en **niet** een aparte
  console-opdracht `catalogus`. Zo botst er niets meer met het PyPI-pakket.
  Gevolg: de opdracht `catalogus` in het `README` van `bron` en in
  `docs/reference/catalogus-cli.md` van `bron` moet verwijzen naar `vsa catalogus`.
- `bibliotheek/scripts/catalogus.py` wordt `catalogus_root.py` (zoals in het plan).

Alternatief (4b): top-level pakket `catalogus` behouden en alleen verhuizen. Dat laat
het naamconflict staan en is daarom niet aanbevolen.

## 5. Waar blijft de data

### Wat er nu is

| Plek                                     | Inhoud                                                                                                                                      |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `bron/zangstukken/`                      | 29 `yaml`-bestanden, 18 `vsa`-bestanden en afbeeldingen. Mappen als `troparion-zondag-toon-1`, `kondak-zondag-toon-1`, `antifoon-1-zondag`. |
| `bron/catalogus/data/alias-blokken.yaml` | 234 regels: org-brede alias-blokken voor liturgische rollen.                                                                                |
| `bibliotheek/content-source/catalogus/`  | 33 mappen als `alleluia`, `ektinia`, `tropaar`, `kondak`.                                                                                   |

De mapnamen van `bron/zangstukken` en de catalogus in bibliotheek **overlappen niet**
(0 gelijke namen). Het zijn dus twee aparte verzamelingen, geen kopieën.

Tooling zoekt nu hard-gecodeerd naar een map met de naam `bron` (`vendor/bron` of
`../bron`) met daarin `zangstukken/` (`catalogus_bridge.discover_bron_root`).

### Opties

| Keuze | Beschrijving                                                                                                 | Voordeel                                                                             | Nadeel                                                           |
| ----- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| 5a    | Data blijft in `bron` (dan alleen inhoud, geen code). Tooling krijgt een instelbare data-root in `vsa.toml`. | Geen inhoud verplaatsen; `bron` blijft vindbaar voor parochies die er al uit putten. | `bron` verdwijnt alleen als codebron, niet uit de keten.         |
| 5b    | `zangstukken/` en alias-blokken verhuizen naar bibliotheek.                                                  | Eén repo voor inhoud.                                                                | Verhuist inhoud waar anderen mogelijk van afhangen; meer risico. |
| 5c    | Eigen nieuwe inhoudsrepo.                                                                                    | Schone scheiding.                                                                    | Extra repo en extra beheer.                                      |

### Aanbeveling: keuze 5a

De instelbare data-root is bij alle keuzes nodig (plan, stap 4). Het verhuizen van
inhoud is een aparte, moeilijk terug te draaien beslissing en hoeft niet in dit
migratietraject te vallen. **Ik weet niet welke andere sites of parochies uit
`bron` putten**; dat moet jij weten voordat 5b een optie wordt.

De normatieve catalogus-specificaties (`bron/docs/specs/catalogus-*.md`) blijven
voorlopig in `bron`; tooling linkt ernaar. Verhuizen ervan is een eigen
Wijzigingsanalyse volgens `AI-INSTRUCTIONS.md` en valt buiten dit ADR.

## Gevolgen voor de volgende stappen

- Stap 4 en 5: volgen keuzes 4 en 1.
- Stap 7: zie de besluiten in het [migratieplan](migratieplan-tooling-bibliotheek.md#7-syllaben).
- Stap 8: gebruikt `vsa.api` (keuze 2).
- Stap 9: volgt keuze 1.
