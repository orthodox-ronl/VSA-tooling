# `.mscz` — MuseScore-partituur

Native MuseScore-bestand (zip met o.a. `.mscx`). In deze toolchain vooral
voor de **partituur-workflow**; Coria gebruikt `.mxl`.

## Wat hoort hier

| Onderwerp             | Waar                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------- |
| Export vanuit `.mvsa` | [`mvsa mscz`](../reference/cli/mvsa.md#vsa-mvsa-mscz) (partituur-mxl → MuseScore)      |
| Print-PDF (zangers)   | [`mvsa pdf`](../reference/cli/mvsa.md#vsa-mvsa-pdf) (via MuseScore; ook vanaf `.mscz`) |
| Layoutprofiel         | Standaard: [MSCZ-leesbaarheid](mscz-leesbaarheid.md); benoemde keuzes = tooling-taak   |
| Import → `.mvsa`      | [`mscz import`](../reference/cli/mscz.md)                                              |
| → `.mxl`              | [`mscz mxl`](../reference/cli/mscz.md)                                                 |
| Template-/corpus-MSCZ | [VSA-templates](../specification-vsa-templates/README.md)                              |

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
| `plain`     | `--layout plain`               | Geen Style-/colofon-/recite-nabewerking; alleen MuseScore-output van de MXL   |

```cmd
mvsa mscz lied.mvsa -o generated\lied.mscz --layout partituur --bibliotheek-id zangstuk/var/uv
mvsa mscz lied.mvsa -o generated\lied.plain.mscz --layout plain
```

**Bibliotheek-id:** consumer bepaalt de waarde; geef die met
`--bibliotheek-id` (colofon bij `partituur`). Pad-afleiding is alleen een
fallback.

## Typische commando’s

```cmd
mscz import generated\alleluia.mscz --pitch abc -o generated\from-mscz.mvsa
mscz mxl generated\alleluia.mscz -o generated\from-mscz.mxl
mvsa mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
```

Via repo-script: `scripts\mscz.cmd …`

Vereist MuseScore 4 (of 3) lokaal, tenzij je alleen `.mxl` gebruikt.

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mvsa`](mvsa.md)
- [mvsa-conversies](../plans/mvsa-conversions.md)
