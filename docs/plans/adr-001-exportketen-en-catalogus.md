# ADR-001 (voorstel): exportketen, publieke API en catalogus-code

Status: **voorstel, wacht op besluit** (2026-11-20). Niet normatief. Dit is stap 3
van het [migratieplan](migratieplan-tooling-bibliotheek.md). Het document wijzigt
geen code. Zodra de keuzes hieronder zijn gemaakt, wordt de status "aangenomen"
en volgt een link in de [contract-index](../formats/contract-index.md).

Gebruikte feiten komen uit de broncode van `VSA-tooling` (`development`),
`bibliotheek` (`development`, `12ae194`) en `bron` (`main`, `ee369a9`). Er is niets
uitgevoerd of getest. Wat niet is gecontroleerd, staat er expliciet bij.

## Wat je moet beslissen

| Nr  | Vraag                                              | Aanbeveling                                                                                                               | Jouw keuze |
| --  | -------------------------------------------------- | -----------------------------------------------------------------------                                                   | ---------- |
| 1   | Welke exportketen is de canonieke?                 | **Keuze C**: gefaseerd, één MusicXML-renderer, Score-IR blijft schermlaag                                                 |            |
| 2   | Hoe roept bibliotheek tooling aan?                 | **Keuze 2a**: één API-module `vsa.api`, in-process                                                                        |            |
| 3   | Hoe pint bibliotheek de tooling-versie?            | Bestaand mechanisme vastleggen (geen nieuw ontwerp)                                                                       |            |
| 4   | Wat gebeurt er met de catalogus-code uit `bron`?   | **Keuze 4a** (verhuizen als `vsa.catalogus`) of **4c** (niet meenemen, opnieuw bouwen op de eigen resolver); zie sectie 4 |            |
| 5   | Welke catalogusdata gebruikt tooling nog?          | **Keuze 5a**: alleen de catalogus van bibliotheek; `bron` als gegevensbron vervalt                                        |            |

Je mag per rij "akkoord" zeggen of een andere letter kiezen. Rij 3 hoeft alleen
een "akkoord".

**Open vraag bij keuze 4c (2026-11-20):** blijft de zoekfunctie bestaan? Het gaat om
`zoek=`-includes, `@include-vsa zoek=` en de opdracht `vsa resolve-catalogus`.
Bibliotheek gebruikt die nergens en de catalogus daar heeft geen manifesten.

| Optie | Beschrijving                                                                                                                                           | Gevolg                                                                |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| i     | Verwijderen, met docs en tests (`docs/reference/cli/resolve-catalogus.md`, `tests/test_resolve_catalogus.py` en de `zoek`-delen van de include-tests). | Minder code; wie `zoek=` gebruikt, krijgt een duidelijke foutmelding. |
| ii    | Behouden, maar opnieuw bouwen op de mappenstructuur van bibliotheek (zoeken op mapnamen).                                                              | Meer werk; gedrag wijkt af van nu.                                    |
| iii   | Behouden zoals het is, maar het bron-pakket blijft dan nodig.                                                                                          | Botst met keuze 4c; niet mogelijk.                                    |

De `id:`-includes blijven in elk geval bestaan, als pad-id op de mappenstructuur
(`resolve_catalogus_id`).

**Niet te verwarren met de zoekfunctie op de site.** De zoekbalk in de bibliotheek en de
koormappen is een andere functie en blijft ongemoeid. Die werkt zo: in bibliotheek bouwt
`scripts/build_zoek_index.py` het bestand `static/zoek/index.json` uit de
uitvoeringsvormen van de catalogus. De gezongen tekst komt uit `*.lyrics.txt`, die tooling
maakt uit `.vsa`, `.mvsa` en `.mscz` (`vsa.text_export`, `write_lyrics_product`), en uit
de zoektekst in de frontmatter (`vsa.zoektekst`). Deze keten gebruikt het `bron`-pakket
niet. Daarom verandert er voor die zoekfunctie niets door keuze 4c; `lyrics` en
`zoektekst` horen in `vsa.api` (keuze 2). Het enige dat in stap 4 raakt aan die keten, is
de hernoeming van `scripts/catalogus.py` naar `catalogus_root.py`, omdat
`build_zoek_index.py` daaruit importeert.


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

**Besluit (2026-11-20, eigenaar): keuze 4c.**

Bevindingen bij het uitwerken (alleen gelezen in tooling en bibliotheek):

- De catalogus van bibliotheek heeft **geen manifestbestanden** (0 yaml-bestanden onder
  `content-source/catalogus`). Het `bron`-pakket zoekt juist op manifesten
  (`zangstuk-id`, `variant-id`, `uitvoeringsvorm-id`, `representaties`, zie
  `tests/test_include_vsa.py`). Voor de echte catalogus van bibliotheek kan dat
  zoeken dus niets vinden.
- De ids in de twee genoemde pagina's (`antifoon-1-weekdagen`, `antifoon-2-weekdagen`,
  `antifoon-3-weekdagen`) bestaan niet in de catalogus; daar heten de mappen
  `eerste-antifoon/weekdagen`, `tweede-antifoon/…`, `derde-antifoon/…`. Die includes
  lossen dus nu al niet op tegen de actuele catalogus.
- Daardoor is er in bibliotheek geen levende gebruiker van de `bron`-zoekfunctie. Of
  het gedrag moet blijven bestaan, is een besluit over het product, niet over
  verhuizen (zie de open vraag onder "Wat je moet beslissen").

Alternatief (4b): top-level pakket `catalogus` behouden en alleen verhuizen. Dat laat
het naamconflict staan en is daarom niet aanbevolen.

Alternatief (4c): het `bron`-pakket niet meenemen, maar de twee functies die het nu
aanstuurt opnieuw bouwen op de catalogus-zoekfuncties die tooling al heeft
(`input_paths.discover_catalogus_roots` en `resolve_catalogus_id`, die precies
`content-source/catalogus` van bibliotheek doorzoeken). Het gaat om `id:`-includes in
markdown (in bibliotheek alleen in `content-source/input/liturgikon/antifonen-liturgikon.md`
en `liturgikon-feesteigen.md`, bijvoorbeeld `:::include svg id:antifoon-1-weekdagen/…`)
en de opdracht `vsa resolve-catalogus` (`zoek=`-includes; bibliotheek gebruikt die nergens). Voordeel: minder code (de 2.189 regels hoeven niet mee) en geen
`bron`-concepten meer. Nadeel: de functies moeten herschreven worden en de
meeverhuisbare tests passen dan niet één-op-één. **Niet gecontroleerd:** of alle
`zoek=`-gedragingen (dubbelzinnigheid, aliassen) met die eenvoudiger resolver te
dekken zijn. Daarvoor moet de code van het `bron`-pakket gelezen worden; dat doe ik
alleen na jouw akkoord, omdat je hebt gezegd dat `bron` niet relevant is.

## 5. Welke catalogusdata gebruikt tooling nog

De catalogus van bibliotheek (`content-source/catalogus`, 33 mappen zoals
`alleluia`, `ektinia`, `tropaar`) is de opvolger van `bron`. De map
`zangstukken/` in `bron` telt niet meer mee.

Wat in tooling nog aan `bron` hangt (`catalogus_bridge.discover_bron_root`): een
optionele extra zoekmap met de naam `bron` waarin `zangstukken/` staat. Zonder die
map geeft de functie `None` terug en blijft het zoeken in de catalogus van de
gebruiker werken. Tooling noch bibliotheek verwijst naar `alias-blokken.yaml`
(gecontroleerd in `src/`, `docs/`, `vsa.toml` en alle scripts en docs van bibliotheek).

### Voorstel (keuze 5a)

- Tooling zoekt alleen nog de catalogus van bibliotheek (`discover_catalogus_roots`,
  eventueel met een pad in `vsa.toml` of de omgevingsvariabele `VSA_CATALOGUS`).
- De zoekfunctie naar een map met de naam `bron` en `zangstukken/` vervalt.
- `alias-blokken.yaml` wordt niet meegenomen, omdat niets in tooling of
  bibliotheek het gebruikt. Wil jij die aliassen toch ooit gebruiken, dan hoort dat
  bestand in bibliotheek en niet in `bron`.
- De normatieve catalogus-specificaties blijven waar ze staan; tooling linkt er
  hoogstens naar. Verhuizen ervan is een eigen Wijzigingsanalyse volgens
  `AI-INSTRUCTIONS.md` en valt buiten dit ADR.

Alternatief (5b): `bron` als tweede catalogus blijven ondersteunen. Dat houdt de
afhankelijkheid van `bron` in stand en is daarom niet aanbevolen.

## Gevolgen voor de volgende stappen

- Stap 4 en 5: volgen keuzes 4 en 1.
- Stap 7: zie de besluiten in het [migratieplan](migratieplan-tooling-bibliotheek.md#7-syllaben).
- Stap 8: gebruikt `vsa.api` (keuze 2).
- Stap 9: volgt keuze 1.
