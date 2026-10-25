# Spike: S8-spacer peiling (OSMD)

Empirische peiling voor plan
[`docs/plans/osmd-s8-recite.md`](../../../docs/plans/osmd-s8-recite.md).
Geen product-from-ir; alleen welke MusicXML-vorm OSMD tekent als
lyric-zichtbaar zonder nootkop.

## Varianten

| Id                         | Spacer-encoding                                       |
| -------------------------- | ----------------------------------------------------- |
| `01-notehead-none`         | Huidige from-ir: `stem none` + `notehead none`        |
| `02-print-object-note`     | `print-object="no"` op hele `<note>`                  |
| `03-print-object-notehead` | `notehead print-object="no"`                          |
| `04-stemless-normal-head`  | Controle: alleen `stem none` (kop mag zichtbaar zijn) |
| `05-rest-with-lyric`       | `<rest/>` + lyric                                     |

**Uitslag (OSMD 1.9.3):** geen van 01–04 verbergt spacer-koppen; 05 toont
rustglyphs. Lyrics blijven in alle varianten. Zie plan §2.2 Besluit.

Patroon: Al (kwart) → le (breve) → lu/i/a (spacers) → al (kwart).

## Draaien

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\osmd-s8-peiling
npm install
npm run probe
```

Output: `out\*.svg` + `out\peiling-summary.json`.
OSMD CDN: 1.9.3 (zelfde major als bibliotheek-scherm).
