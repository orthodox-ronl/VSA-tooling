# Spike: MusicXML → SVG via OSMD (headless)

Proef + productbrug: **OpenSheetMusicDisplay** schrijft een partituur-SVG
uit Score-IR-MusicXML — **zonder MuseScore**.

Product-CLI (D3): `mvsa svg --engine osmd` (renderer:
[`scripts/osmd-svg/`](../../../scripts/osmd-svg/)).

## Vereisten

- Node.js 18+ (`npm`)
- Eenmalig: `cd scripts\osmd-svg && npm install && npx puppeteer browsers install chrome`

## MusicXML

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o examples\spikes\partituur-browser\score.score-ir.json --musicxml examples\spikes\partituur-browser\score.musicxml
```

## Renderen (spike)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\partituur-osmd-svg
npm run render
```

(Delegeert naar `scripts\osmd-svg\render.mjs`.) Uitvoer: `out\score.svg`.

Of via product-CLI:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-osmd.svg --engine osmd
```

## D2 — vergelijking OSMD vs MuseScore (1a-vredeslitanie)

Cloud-run (2026-10-31): MuseScore niet in de VM; OSMD-SVG wél gerenderd
(`out\score.svg`, ~238 KB, viewBox `0 0 900 585.5`, 1 Endless-pagina).

| Check                          | OSMD (headless)                          | MuseScore (`mvsa svg`, default)        |
| ------------------------------ | ---------------------------------------- | -------------------------------------- |
| Twee balken SA/TB              | Ja (Score-IR MusicXML)                   | Ja (partituur-MXL → MSCZ)              |
| Lyrics                         | Ja (o.a. Amen, Heer ontferm U)           | Ja                                     |
| `@tekst`-cues                  | Ja (o.a. «P: Gezegend…», «P: Laat ons…») | Ja (SystemText)                        |
| Titel/colofon                  | Uit (`drawTitle` false)                  | Uit (layout ``muziek``)                |
| Bronketen                      | Score-IR → from-ir MusicXML              | partituur-MXL → MSCZ                   |
| Style-CLI (afstand/fonts/…)    | Nee (OSMD/Score-IR)                      | Ja (MuseScore Style)                   |
| Print/`index.md.pdf`-bouwsteen | Nee — scherm/optioneel bestand           | Ja (tall compact sibling)              |

**Conclusie:** OSMD-SVG dekt lyrics + cues voor dit voorbeeld; geschikt als
optionele scherm-/inspectie-export. Print-fallback en pagina-PDF blijven
MuseScore ([kale-muziek §4](../../../docs/plans/kale-muziek-svg-en-uitgaven.md)).

Lokaal MuseScore-SVG naast leggen:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-musescore.svg
```

## Relatie

| Pad                                                               | Rol                                      |
| ----------------------------------------------------------------- | ---------------------------------------- |
| [`partituur-browser`](../partituur-browser/)                      | OSMD in de browser                       |
| **deze spike** / [`scripts/osmd-svg`](../../../scripts/osmd-svg/) | Headless SVG-bestand                     |
| `mvsa svg --engine osmd`                                          | Product-CLI (D3)                         |
| `mvsa svg` (default musescore)                                    | Print/fallback tall-SVG                  |

Contract: [partituur-ir §7](../../../docs/plans/partituur-ir.md).
