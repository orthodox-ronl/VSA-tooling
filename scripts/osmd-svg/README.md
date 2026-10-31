# OSMD → SVG (headless) voor `mvsa svg --engine osmd`

Node-hulp voor partituur-SVG **zonder MuseScore**: MusicXML (uit Score-IR)
→ OpenSheetMusicDisplay → S8 A1-adapter → `.svg`.

**S8 (contract A1):** from-ir markeert spacers met `<notehead>none</notehead>`
en het recite-midden met `<notehead>breve</notehead>`. Na OSMD-render:
`s8-a1-adapter.js` verbergt spacer-koppen (lyrics blijven) en zet de breve
om naar de MuseScore-``||O||``-path (uit de referentie-SVG). Lyrics:
**Source Sans 3** (lokale WOFF2 in `fonts/`, `@font-face` in de uitvoer-SVG).
Uitvoer-SVG krijgt een witte pagina-achtergrond (`rect.vsa-page-bg`, zelfde
idee als MuseScore-trim). Zelfde marker-contract als bibliotheek
`score-osmd.js` ([osmd-s8-recite](../../docs/plans/osmd-s8-recite.md)).

Graveerprofiel **`coribCompact`** (in `render.mjs`, na OSMD-`compacttight`)
zet de schermafstanden: balk- en systeemafstand, lyrics naar het midden
van het balkgat (na-render verschuiving), iets kortere stokken.
Lettergreep-afstanden volgen OSMD-defaults (geen lagere elongatie:
die liet S8-recite overlappen, o.a. maat 2 van derde-antifoon).
`VoiceSpacing` terug naar 0.85/3.0 (compacttight knelde op 0.65/2.0).
Bladbreedte 1000 px; `MeasureWidthFactor` 1. **S10:** maatnummers alleen
aan systeembegin (`RenderMeasureNumbersOnlyAtSystemStart`); maatnummer
**1** wordt nagetekend. Een stuk dat korter is dan de bladbreedte wordt
bijgesneden op de inkt. Contract-check: `node verify-corib-contract.mjs`.

S8 A1-adapter (`s8-a1-adapter.js`) koppelt spacer/breve per **measure-id**
(geen y-systeemdrempel — die brak bij compacte CoriB-layout). Lettergreep-
streepjes (`vf-text dash`) blijven zichtbaar. Pixel-pariteit met MuseScore
is geen eis ([corib-mvp](../../docs/plans/corib-mvp.md)); S8/S13 blijven
het contract voor recite en melisma.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\scripts\osmd-svg
npm install
npx puppeteer browsers install chrome
```

Handmatig:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\scripts\osmd-svg
node render.mjs ..\..\examples\spikes\partituur-browser\score.musicxml out\score.svg
```

S8-check op from-ir MusicXML:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\scripts\osmd-svg
npm run check-s8-a1 -- ..\..\generated\corib-s8-toets\from-ir\alleluia-toon-8.from-ir.musicxml
```

Via CLI (na `npm install` hierboven):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-osmd.svg --engine osmd
```

Override scriptpad: omgevingsvariabele `VSA_OSMD_RENDER` = pad naar `render.mjs`.

Scherm-hoofdpad blijft Score-IR → OSMD in de site; deze CLI is optioneel
bestandsexport. Print/fallback blijft MuseScore (`--engine musescore`, default).
Zie [partituur-ir §7](../../docs/plans/partituur-ir.md) en
[kale-muziek §4](../../docs/plans/kale-muziek-svg-en-uitgaven.md).
Corpus: `examples/bug-cases/corib/`.
