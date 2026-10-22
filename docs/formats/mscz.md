# `.mscz` — MuseScore-partituur

Native MuseScore-bestand (zip met o.a. `.mscx`). In deze toolchain vooral
voor de **partituur-workflow**; Coria gebruikt `.mxl`.

## Wat hoort hier

| Onderwerp             | Waar                                                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Export vanuit `.mvsa` | [`mvsa mscz`](../reference/cli/mvsa.md#vsa-mvsa-mscz) (partituur-mxl → MuseScore)                                          |
| Print-PDF (zangers)   | [`mvsa pdf`](../reference/cli/mvsa.md#vsa-mvsa-pdf) (via MuseScore; ook vanaf `.mscz`)                                     |
| Layoutprofiel         | Standaard: [MSCZ-leesbaarheid](mscz-leesbaarheid.md); benoemde keuzes = tooling-taak                                       |
| Import → `.mvsa`      | [`mscz import`](../reference/cli/mscz.md) (**werkbank**-bewerkvorm; SATB-explode; soft-wrap; default `ag-vsa` = ankers)    |
| → `.mxl`              | [`mscz mxl`](../reference/cli/mscz.md)                                                                                     |
| Platte gezongen tekst | [`mscz text`](../reference/cli/mscz.md) / [`vsa text`](../reference/cli/text.md)                                           |
| Template-/corpus-MSCZ | [VSA-templates](../specification-vsa-templates/README.md)                                                                  |

Geen volledige MuseScore-formaat-spec — wel: wat **wij** genereren en
verwachten voor bruikbare SATB + lyrics.

**Normaalvorm (checklist):**
[canonieke checklists — MSCZ](canonical-checklists.md#checklist-mscz-partituur-musescore)
— **twee balken SA + TB**, **geen** stem-indicaties op de balken,
**stokken S/T omhoog en A/B omlaag**, **geen mid-systeem-HBox / spookmaten**,
**`@tekst` als SystemText**, herhalingen zonder lege voorafgaande maat.
Leesbaarheid (recite, lyrics, slurs, cues, stokken, maatnummers):
[MSCZ-leesbaarheid](mscz-leesbaarheid.md).
Semantiek deelt de kern met MXL; layout divergeert (Coria = vier parts).

## Layoutprofielen (`--layout`)

Na de MuseScore-conversie past VSA-tooling een **benoemd profiel** toe.
De consumer **kiest**; de tool **handhaaft**. Zie
[ownership](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

| Profiel     | CLI                            | Wat je krijgt                                                                 |
| ----------- | ------------------------------ | ----------------------------------------------------------------------------- |
| `partituur` | `--layout partituur` (default) | Canonieke koorprint: [MSCZ-leesbaarheid](mscz-leesbaarheid.md) + checklist    |
| `muziek`    | `--layout muziek`              | Leesbaarheid zonder titel/footer/colofon — [koormap-SVG](mvsa-svg.md)         |
| `plain`     | `--layout plain`               | Geen Style-/colofon-/recite-nabewerking; alleen MuseScore-output van de MXL   |

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
min=max **2** spatium (MuseScore mag lokaal meer voor cues), lyric-clearance
**0.1** (SA/TB dichter), boven-/ondermarge **5** mm. Style wordt ook naar
`score_style.mss` gesynchroniseerd (MuseScore 4). **Andere Style-opties
winnen van `--compact`** (per sleutel). Voorbeeld: meer lucht tussen
systemen met behoud van de rest van compact:

```cmd
mvsa pdf lied.mvsa --compact --min-system-distance 4 --max-system-distance 4
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
default `1.2`; hoger = meer ruimte tussen noten in de maat). Dit is geen
volledige “centreer in brede cue-maat”; die breedte komt uit MusicXML
`width` bij cues — dat is een apart onderwerp.

**Bibliotheek-id:** consumer bepaalt de waarde; geef die met
`--bibliotheek-id` (colofon bij `partituur`). Pad-afleiding is alleen een
fallback.

!!! warning "Import = werkbank"
    `mscz import` is een **bewerkvorm** voor de werkbank-fase, geen
    catalogus-klaar product. De output begint met dezelfde
    waarschuwingsbanner als `mvsa import`. Onderstemmen A/T/B worden op duur
    tegen S uitgelijnd; zie
    [`mvsa import`](../reference/cli/mvsa.md#vsa-mvsa-import).

## Typische commando’s

```cmd
mscz import generated\alleluia.mscz -o generated\from-mscz.mvsa
mscz import generated\alleluia.mscz --pitch a-g -o generated\from-mscz.ag.mvsa
mvsa validate generated\from-mscz.mvsa
mscz mxl generated\alleluia.mscz -o generated\from-mscz.mxl
mscz text generated\alleluia.mscz -o generated\alleluia.mscz.lyrics.txt
mvsa mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
```
Via repo-script: `scripts\mscz.cmd …`

Vereist MuseScore 4 (of 3) lokaal, tenzij je alleen `.mxl` gebruikt.

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mvsa`](mvsa.md)
- Platte tekst: [`vsa text`](../reference/cli/text.md) / [`mscz text`](../reference/cli/mscz.md)
- [mvsa-conversies](../plans/mvsa-conversions.md)
