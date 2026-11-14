# `.mscz` — MuseScore-partituur

Native MuseScore-bestand (zip met o.a. `.mscx`). In deze toolchain vooral
voor de **partituur-workflow**; Coria gebruikt [`.mxl`](mxl.md).

Start: [contract-index](contract-index.md) (§Contract-skelet, C*, hubs).

## Identiteit

| Veld        | Waarde                                                                    |
| ----------- | ------------------------------------------------------------------------- |
| Extensie    | `.mscz`                                                                   |
| Rol         | Notatiebron **of** standaardproduct (meta-key `mscz`)                     |
| Sibling     | Product: `{stam}.{bron}.mscz` (bijv. `lied.vsa.mscz`, `lied.mvsa.mscz`)   |
| Wanneer     | Partituur-print / MuseScore-bewerking; catalogus-leaf als bron of product |

Geen volledige MuseScore-formaat-spec — wel: wat **wij** genereren en
verwachten voor bruikbare SATB + lyrics.

## Canoniciteit

Canoniek = voldoet aan checklist **S\*** ([canonical-checklists](canonical-checklists.md#checklist-mscz-partituur-musescore))
en [MSCZ-leesbaarheid](mscz-leesbaarheid.md) (R\*/L\*), bij layout
`partituur` of `muziek`. C1–C4: [contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

**C3 vóór conversie (fase 3, structureel):** de bron moet een geldige
MuseScore-zip zijn met een leesbare ``.mscx`` (codes `MSCZ-ZIP` /
`MSCZ-MSCX` / …). Geen volle S*-gate op de bron; `--allow-noncanonical`
slaat deze check over. Aangesloten op `mscz products` en product-subs
(`mxl`, `svg`, `pdf`, audio, `score-ir`, `mscz`, `text`).

**Kern (S\*):** twee balken SA + TB; geen stem-indicaties op de balken;
stokken S/T omhoog en A/B omlaag; geen mid-systeem-HBox / spookmaten;
`@tekst` als SystemText; herhalingen zonder lege voorafgaande maat.

## Inhoud en metadata

| Onderwerp        | Regel                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| Frontmatter      | n.v.t. (binair MuseScore; geen VSA-YAML)                              |
| Encoding         | MuseScore intern; lyrics UTF-8 in MusicXML-brug                       |
| Colofon / titel  | Via layout `partituur` + consumer `--bibliotheek-id`                  |
| Verboden         | Mid-systeem-HBox als “oplossing” voor gaps (zie leesbaarheid C3/C4)   |

## Syllabificatie

Soft `-` hoort in de **bron** (`.vsa` / `.mvsa`), niet als zichtbare glyphs
binnen elke recite op het blad.

| Regel | Inhoud                                                                                                                                   |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| R8    | Recite-underlay: geen zichtbare soft `-` *binnen* recite; MusicXML `syllabic` begin/middle/end + brugstreepjes over woordgrenzen blijven |
| Bron  | Zing-deling = noot-aantal; zie [syllabificatie](syllabificatie.md)                                                                       |

Voorbeeld: bron `ver-heer-lijkt` → op blad syllabic begin/middle/end (en
eventueel brug bij cadens); geen hyphen-glyph op elke lettergreep in de
recite.

## Melisma en binding

| Id           | Regel                                                                              |
| ------------ | ---------------------------------------------------------------------------------- |
| S13 / M5a    | Same-pitch melisma: compacte eindvorm op blad (MSCZ-postprocess); hyphen ≠ melisma |
| S1 / S4 / R7 | Geen Capella-fraseslur die als melisma oogt                                        |

Diepte: [canonical-checklists](canonical-checklists.md) · [mscz-leesbaarheid](mscz-leesbaarheid.md).

## Transliteratie

n.v.t. op het `.mscz` zelf als tweede lyric-laag. Translit-weergave is een
apart product ([translit-svg](translit-svg.md)); partituur-`.mscz` volgt
de bronlyrics.

## Stemmen en partijen

Canoniek: **SA + TB** op twee balken (geen vier labeled parts zoals Coria).
Stemextractie naar `.vsa`: zie [mvsa-vsa-contract](mvsa-vsa-contract.md) (E\*).

## Leesbaarheid

Fonts, groottes, stacking, cues, slurs, maatnummers, spacers: volledig in
[MSCZ-leesbaarheid](mscz-leesbaarheid.md). Layoutprofielen hieronder
(`partituur` / `muziek` / `plain`).

## Herkomst

Als **product** uit `{straat} products` / `{straat} mscz`: merge in
`{bronnaam}.products-meta.json` (key `mscz`) — [products-meta](products-meta.md).
Als **catalogusbron** `.mscz`: de bron zelf heeft geen meta-key voor het
brontype; products naast de bron wel.

## Conversies

| Richting                                      | CLI                                              | Canoniciteit                                                |
| --------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| `.mvsa` / `.vsa` → `.mscz`                    | `mvsa mscz` / `vsa products` (key `mscz`)        | C3/C4: canonieke bron → canonieke partituur                 |
| `.mscz` → product `mscz`                      | `mscz mscz` / `mscz normalize`                   | Zelfde-type = partituur-conform maken                       |
| `.mscz` → `.mxl`                              | `mscz mxl`                                       | Doel: M\* / playback                                        |
| `.mscz` → `.mvsa`                             | `mscz mvsa`                                      | **Uitzondering:** werkbank-bewerkvorm, niet catalogus-klaar |
| `.mscz` → SVG / PDF / text / audio / score-ir | `mscz svg` / `pdf` / `text` / `mp3` / `score-ir` | Doel per productcontract                                    |

**CLI-lock:** MuseScore-aanroepen via `vsa.musescore_cli` wachten op elkaar
(Windows-vergrendelingen).

## Validatie

| Hoe                                 | Wat                                    |
| ----------------------------------- | -------------------------------------- |
| Checklist S\* / R\*                 | Hand/CI + exportpad                    |
| `mscz normalize --layout partituur` | Layout naar normaalvorm                |
| `mscz compare`                      | Score ↔ `.mvsa` (lyrics, pitch, gaten) |

---

## Recite en print-collapse (type-specifiek)

| Id  | Regel                                                | Hub                                             |
| --  | -----                                                | ---                                             |
| S8  | Recite-print spacers / breve bij `n ≥ 6` (partituur) | [canonical-checklists](canonical-checklists.md) |
| M10 | **Geen** print-collapse in Coria-playback-`.mxl`     | zelfde hub §MXL                                 |
| R5  | Maatlengte = som noten + spacers; spacers `play=0`   | [mscz-leesbaarheid](mscz-leesbaarheid.md)       |
| R8  | Geen interne hyphen-glyphs in recite-underlay        | zelfde                                          |

Semantiek deelt de kern met MXL; layout divergeert (Coria = vier parts).

## Layoutprofielen (`--layout`)

Na de MuseScore-conversie past VSA-tooling een **benoemd profiel** toe.
De consumer **kiest**; de tool **handhaaft**. Zie
[ownership](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

| Profiel     | CLI                            | Wat je krijgt                                                               |
| ----------- | ------------------------------ | --------------------------------------------------------------------------- |
| `partituur` | `--layout partituur` (default) | Canonieke koorprint: [MSCZ-leesbaarheid](mscz-leesbaarheid.md) + checklist  |
| `muziek`    | `--layout muziek`              | Leesbaarheid zonder titel/footer/colofon — [koormap-SVG](mvsa-svg.md)       |
| `plain`     | `--layout plain`               | Geen Style-/colofon-/recite-nabewerking; alleen MuseScore-output van de MXL |

```cmd
mvsa mscz lied.mvsa -o generated\lied.mscz --layout partituur --bibliotheek-id zangstuk/var/uv
mvsa mscz lied.mvsa -o generated\lied.plain.mscz --layout plain
mvsa mscz lied.mvsa -o generated\lied.mscz --min-system-distance 10 --max-system-distance 18
mvsa mscz lied.mvsa -o generated\lied.mscz --compact
mvsa mscz lied.mvsa -o generated\lied.mscz --staff-distance 4.5
mvsa mscz lied.mvsa -o generated\lied.mscz --page-margin-top 5 --page-margin-bottom 5
mvsa mscz lied.mvsa -o generated\lied.mscz --lyrics-font-size 14 --cue-font-size 11
```

**Systeemafstand:** bij `partituur` / `muziek` kun je de vaste Style-waarden
(default 8 / 14) overschrijven met `--min-system-distance` en
`--max-system-distance` (spatium). Niet bij `--layout plain`.

**`--compact`:** dichtste Style-baseline (pdf/svg/mscz): systeemafstand
min=max **7** spatium (genoeg dat de accolade-*hook* niet door het
maatnummer van het volgende systeem snijdt; MuseScore mag lokaal meer
voor cues), lyric-clearance **0.1** (SA/TB dichter), boven-/ondermarge
**5** mm, maat-spreiding **1.6**. Daarnaast zetten partituur-nabewerking
en SVG-export een **trailing spatie** op woord-einde-lyrics zodat MuseScore
woorden niet als «desheils» aan elkaar plakt. Style wordt ook naar
`score_style.mss` gesynchroniseerd (MuseScore 4). **Andere Style-opties
winnen van `--compact`** (per sleutel). Voorbeeld: nog meer lucht tussen
systemen met behoud van de rest van compact:

```cmd
mvsa pdf lied.mvsa --compact --min-system-distance 9 --max-system-distance 9
```

Niet bij `--layout plain`.

**Stafafstand:** `--staff-distance` (spatium) zet de afstand tussen de
notenbalken *binnen* één systeem (`staffDistance` én accolade-afstand voor
SA/TB). Geen vaste Style-default in de export (MuseScore + lyrics bepalen
anders de ruimte). Lyrics tussen de balken blijven een harde ondergrens.
Niet bij `--layout plain`.

**Pagina-marges:** default 15 mm rondom. Alleen boven/onder overschrijven met
`--page-margin-top` / `--page-margin-bottom` (millimeters; `0` toegestaan).
Linker- en rechtermarge blijven 15 mm. Niet bij `--layout plain`.

Alle Style-CLI-opties (incl. `--compact`) worden in het `.mscz` naar zowel
de score-`.mscx` als `score_style.mss` geschreven — MuseScore 4 leest layout
vooral uit die `.mss`.

**Fonts:** `--lyrics-font` / `--lyrics-font-size` (zangtekst; default Source
Sans 3 / 13 pt) en `--cue-font` / `--cue-font-size` (cues/`@tekst`; default
zelfde font / 12 pt). Fontnaam moet op de machine in MuseScore beschikbaar
zijn. Niet bij `--layout plain`.

**Maat-spreiding:** `--measure-spacing` (MuseScore Style `measureSpacing`,
default `1.2`; hoger = meer ruimte tussen noten in de maat). Cue-maten
krijgen een milde MusicXML-`width` ([leesbaarheid C6](mscz-leesbaarheid.md#c--cues-gaps-hbox-accolade));
dat vermindert “noten links in een holle maat” bij lange `@tekst`.

**Bibliotheek-id:** consumer bepaalt de waarde; geef die met
`--bibliotheek-id` (colofon bij `partituur`). Pad-afleiding is alleen een
fallback.

!!! warning "Import = werkbank"
    `mscz mvsa` is een **bewerkvorm** voor de werkbank-fase, geen
    catalogus-klaar product. De output begint met dezelfde
    waarschuwingsbanner. Onderstemmen A/T/B worden op duur
    tegen S uitgelijnd; zie
    [score naar mvsa](mvsa.md#score-naar-mvsa).

## Typische commando’s

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mscz.cmd mvsa generated\alleluia.mscz
scripts\mscz.cmd mvsa generated\alleluia.mscz --pitch a-g -o generated\from-mscz.ag.mvsa
scripts\mvsa.cmd validate generated\from-mscz.mvsa
scripts\mscz.cmd mxl generated\alleluia.mscz -o generated\from-mscz.mxl
scripts\mscz.cmd svg generated\alleluia.mscz -o generated\alleluia.svg
scripts\mscz.cmd pdf generated\alleluia.mscz -o generated\alleluia.pdf
scripts\mscz.cmd normalize generated\alleluia.mscz --layout partituur
scripts\mscz.cmd text generated\alleluia.mscz -o generated\alleluia.mscz.lyrics.txt
scripts\mvsa.cmd mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
```

Vereist MuseScore 4 (of 3) lokaal, tenzij je alleen `.mxl` gebruikt.

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mvsa`](mvsa.md)
- Platte tekst: [lyrics.txt](lyrics.txt.md) · [`mscz text`](../reference/cli/mscz.md)
- Score ↔ `.mvsa`: [`mscz compare`](../reference/cli/mscz.md#mscz-compare)
- [mvsa-conversies](../plans/mvsa-conversions.md)
