# Changelog

## Unreleased

- **Fix (mvsa svg/mxl-partituur):** in recite (`(Uw Naam wor-de ge-hei-ligd)`) kwamen de lettergreep-streepjes niet in de partituur-SVG: R8 verborg ze doelbewust. Contract herzien: een partituur-SVG toont **alle** streepjes (ook binnen recite); alleen de `.vsa.svg` laat ze weg. Producten moeten opnieuw gegenereerd worden (`products --force`).
- **Nieuw (vsa svg):** de SVG wordt na het tekenen bijgesneden tot de getekende inhoud (rand 6 links/rechts, 4 boven/onder). Lege rijen of commentaar boven de notatie geven geen witruimte meer. Uit te zetten met `rendering.svg.trim = false`; zie `docs/formats/vsa-svg.md`. Bestaande svg's worden korter; daarmee verandert de `scale` in gegenereerde markdown mee.
- **Fix (syllabify):** een regel die met `#` begint (broncommentaar) kreeg streepjes (`over` werd `o-ver`) als er in dezelfde passage geen `<!--` stond. `#`-regels blijven nu altijd onaangeroerd, bij `syllabify` en `--unsyllabify`.
- **Nieuw (vsa mvsa):** valideert de zojuist geschreven MVSA; bij errors worden die met bestand/regel/kolom gemeld en eindigt het commando met exitcode 1 (bestand blijft staan).
- **Fix (vsa mvsa):** een `_` achter een recite-lettergreep in de VSA-tekst (`{/ver}hoor_`, `tot_`) kwam binnen de haakjes terecht (`(ver-hoor_)`, fout `duur-/melisma-ELM binnen recite-haakjes`). De ELM staat nu ná `)`: `(ver-hoor)_`.
- **Fix (vsa mvsa):** `template:` in de frontmatter van de `.vsa` wordt gebruikt (CLI `--template` wint nog steeds). Voorheen gaf `soort`+`toon` met meerdere formules (bijv. tropaar toon 4: groningen/hemelum) `TEMPLATE-SELECT-AMBIGUOUS`, ook als de .vsa de template al noemde.
- **Fix (mvsa validate):** een maatstreep gevolgd door een Unicode-spatie (bijv. U+2006, gebruikt om Cyrillische lyrics uit te lijnen) werd als eindanker gelezen (`MVSA-BAR-ANKER`); nu geldt elke witruimte als spatie.
- **Fix (mvsa):** `heer -(lijkt …)` (streepje vóór het haakje) werd stil genegeerd; het telt nu als `heer (-lijkt …)`: de recite zet het woord voort (`ver-heer-lijkt`). Gevolg: ook in MusicXML/MuseScore loopt het woord door.
- **Fix:** de interactieve vraag bij een onbekend woord noemde de láátst gecontroleerde lijst (bijv. `syllable_dictionary.ksl.txt` bij het Latijnse `Ky-ri-e`). De vraag noemt nu de lijst die bij het schrift van het woord hoort; het toevoegen zelf schreef al naar de juiste lijst.
- **Nieuw:** `@taal xx` voor passages in een taal zonder woordenlijst (`@taal ro`, `@taal el`, …; 2–3 kleine letters). In `.mvsa` accepteert de bestaande sticky `@taal` nu ook zulke codes (voorheen `MVSA-TAAL`); in `.vsa` kun je `@taal xx` als regel in de tekst zetten. Woorden in zo'n taal worden niet tegen de woordenlijst gecontroleerd en niet door `syllabify` aangepast. `@taal auto` zet de herkenning op schrift (nl/ksl) weer aan. Zie `docs/formats/syllabificatie.md`.
- **Fix:** ook een regelbegin direct na een scope is een woordgrens in de woordenlijst-controle (`be{\vrijd_}⏎en` werd het "woord" `be-vrijd-en`).
- **Fix:** de woordenlijst-controle plakte woorden over een regeleinde heen aan elkaar (`{/mij_},` + volgende regel `{/ver}{hoor_}` werd het "woord" `mij-,-ver-hoor`). Een regeleinde na lyric-tekst is nu altijd een woordgrens.
- **Nieuw (migratie stap 7):** `vsa.syllabify.hyphenate_token_parts` (lettergrepen van één lyric-token uit de canonieke lijst; onbekende woorden blijven heel) en `vsa.syllabify.split_syllabic`. Vervangen `nl_hyphen.py` in bibliotheek. `eeuwen` is `eeu-wen`.
- **Fix:** in een terminal (TTY) voegden `validate`/`svg` bij `.vsa` en `.mvsa` stil Pyphen-gokken toe aan onbekende woorden (`onbekendwoord` werd `on-be-kend-woord`). De stille reparatie past nu alleen woorden uit de lettergreeplijst aan. Het commando `syllabify` (met TTY-vragen) is ongewijzigd.
- **Fix:** `vsa validate`/`vsa svg` herschreven stil een onbekend woord in scopes (`{/e_}ren` werd `{/eren_}`). Woorden die niet in de lettergreeplijst staan blijven nu ongewijzigd; validate meldt ze als onbekend met een voorstel.
- **Verwijderd (breaking):** `zoek=` in `:::include` en `@include-vsa`, en de opdracht
  `vsa resolve-catalogus`. Een include met `zoek=` geeft nu een foutmelding; gebruik
  `id=` / `id:` of een bestandspad. De site-zoekfunctie
  (`*.lyrics.txt`, zoektekst) is een andere keten en blijft ongewijzigd.
- **Gewijzigd (breaking, migratie stap 4 deel 2):** `id=` / `id:` wijst nu naar een map onder
  `content-source/catalogus/` (zangstuk/variant/uitvoeringsvorm) en moet precies één `.vsa`
  opleveren. `lokaal=` / `lokaal:` en `bron:` vervallen en geven een foutmelding.
  Het pakket `catalogus` uit `bron` is geen afhankelijkheid meer; de optie `--bron-root`
  van `markdown svg` en `markdown pdf` en de bron-checkout in CI zijn verwijderd.
- Docs/CLI-voorbeelden: overal `mvsa …` i.p.v. `vsa mvsa …` (bron = command);
  nested `vsa mvsa` verwijderd — alleen top-level `mvsa`
- CLI: score → `.mvsa` is `mxl mvsa` / `mscz mvsa` (conventie bron→doel); `import` verwijderd uit `mvsa`/`mxl`/`mscz`
- Canonieke maatnummers: MusicXML/MuseScore-`@number` blijft leidend;
  Coria-`[PAUZE]` krijgt `Np` zonder hernummering; import-`#maat N` gebruikt
  dat nummer (MSCZ-import zonder pauzematen in de schets)
- CLI: `mvsa musicxml` → `mvsa mxl`, `mvsa audio` → `mvsa mp3` (aliases
  `musicxml` / `audio` blijven werken); documentatie bijgewerkt
- `mvsa mxl` accepteert `.mscz` / `.mxl` (geen UTF-8-crash op binaire bronnen);
  validate/normalize/kuiser/mscz geven een duidelijke fout bij verkeerd type
- MVSA-import: A/T/B spiegelen op **duur** t.o.v. S (niet noot-index/lyrics),
  zodat lange noten + lyric-loze spacers (typisch MSCZ) Bb/T niet verschuiven
- MVSA-import: gerichte lyric-hacks — spaties in `end`-lyrics, `we-der-ke`,
  geen valse `dag-gaan`/`steun-van`/`Heer-richt`, `Ja_-cob` / `zon_-daars`
- MVSA L-normaalvorm: lone standaard-`~` weglaten; `~` blijft bij `&`-melisma
  en na recite-`)` (kuiser + import)
- MVSA-import: ASCII-waarschuwingsbanner na `# Imported:` (schets/checklist;
  entrypoints `mxl mvsa` / `mscz mvsa`)
- Testfixtures hersteld: `test-alleluia-toon-8.mvsa` en
  `test-kleine-intocht-zondag-hemelum.mvsa` (multi-`@sectie` voor roundtrips;
  ≠ catalogus-voorbeelden). `test-trisagion-…` blijft weg (geen testgebruik)
- MVSA→MusicXML: soft-wrap-`-` over systeemovergangen houdt de lopende toon
  (beginanker/`@start` reset); zelfde carry in eindanker-check en normalize

## 0.2.0 - MVSA-authoring, export en preview-audio

- MVSA: parser, validatie, normalize/align, **`mvsa kuiser`** (canonieke authoring-vorm)
- Export: MusicXML, MSCZ, PDF, preview-**audio** (`vsa audio` / `mvsa mp3` via MuseScore)
- Speelplan / layout voor partituur-navigatie
- Align bewaart leidende `|:` (repeat-start) op alle stokken
- Consumer-pin: tag `0.2.0` i.p.v. alleen `@main`

## 0.1.0 - eerste werkende ontwikkelversie

Bevat:

- parser;
- syntaxvalidatie;
- semantische validatie;
- SVG-rendering;
- Markdown/Hugo preprocessing;
- GitHub Actions CI;
- preview/productie build artifacts.

Nog niet stabiel:

- finale SVG-layout;
- MusicXML-export;
- meerstemmige VSA-uitbreiding.
