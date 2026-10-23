# Spike: MusicXML → SVG via OSMD (headless)

Proef: kan **OpenSheetMusicDisplay** in headless Chromium een
**partituur-SVG** schrijven uit dezelfde MusicXML als de browser-spike —
**zonder MuseScore** en **zonder** `vsa`-CLI?

Geen product-commando. Bewijs voor een latere optie
`mvsa svg --engine osmd` (handover D, stap 2–3).

## Vereisten

- Node.js 18+ (met `npm`)
- Netwerk bij eerste run (Puppeteer downloadt Chromium; OSMD via CDN)

## Eenmalig

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\partituur-osmd-svg
npm install
npx puppeteer browsers install chrome
```

(Als `npm install` de Chromium-download blokkeert: het tweede commando
is verplicht vóór `npm run render`.)

## MusicXML (zelfde als browser-spike)

Als `..\partituur-browser\score.musicxml` ontbreekt:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o examples\spikes\partituur-browser\score.score-ir.json --musicxml examples\spikes\partituur-browser\score.musicxml
```

## Renderen

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\partituur-osmd-svg
npm run render
```

Uitvoer: `out\score.svg`. Optioneel eigen paden:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\partituur-osmd-svg
node render.mjs ..\partituur-browser\score.musicxml out\score.svg
```

Open `out\score.svg` in een browser of viewer. Vergelijk met MuseScore-SVG:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-musescore.svg
```

## Wat we willen zien

1. Twee balken (SA / TB).
2. Lyrics zichtbaar.
3. `@tekst`-cues (o.a. “P: Gezegend…”).
4. Eén SVG-bestand (Endless-page; geen A4-stapel tenzij OSMD splitst).

## Relatie tot andere spikes / product

Productieschermrichting: Score-IR → MusicXML → OSMD. Deze spike bewijst
headless SVG uit dezelfde MusicXML; MuseScore blijft print/blad.

| Pad                                                                | Rol                                      |
| ------------------------------------------------------------------ | ---------------------------------------- |
| [`partituur-browser`](../partituur-browser/)                       | OSMD in de browser (zelfde MusicXML)     |
| **deze spike**                                                     | Zelfde keten → **bestand** `.svg`        |
| [`mvsa svg`](../../../docs/reference/cli/mvsa.md#mvsa-svg) | Blad-/print-SVG via MuseScore            |
| Later: CLI `--engine osmd`                                         | Optioneel; ná site-embed                 |

Contract Score-IR / CoriB-brug: [partituur-ir.md](../../../docs/plans/partituur-ir.md) §7.
