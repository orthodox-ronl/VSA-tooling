# OSMD → SVG (headless) voor `mvsa svg --engine osmd`

Node-hulp voor partituur-SVG **zonder MuseScore**: MusicXML (uit Score-IR)
→ OpenSheetMusicDisplay → S8 A1-adapter → `.svg`.

**S8 (contract A1):** from-ir markeert spacers met `<notehead>none</notehead>`.
OSMD tekent die koppen wél; `s8-a1-adapter.js` verbergt ze na render
(lyrics blijven). Zelfde contract als bibliotheek `score-osmd.js`
([osmd-s8-recite](../../docs/plans/osmd-s8-recite.md)).

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
