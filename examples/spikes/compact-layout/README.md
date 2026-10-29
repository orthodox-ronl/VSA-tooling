# Spike: compact layout (MuseScore content-aware gaps)

Bron: `examples/bug-cases/ektinia-vrede-hemelum.mvsa` (3 systemen, SA/TB,
lyrics tussen de balken, SystemText-cues).

Meten: `measure_svg_gaps.py` op MuseScore-SVG (`StaffLines`).

Eenheid: 1 spatium ≈ afstand tussen notenbalklijnen ≈ **82,7** SVG-units.

## Varianten (eerste meting)

| Id  | Style CLI                                      | Gap 1→2 (sp) | Gap 2→3 (sp) | Inner SA→TB (sp) |
| --  | ---------------------------------------------- | ------------ | ------------ | ---------------- |
| A   | default (min/max 8/14)                         | ≈14          | ≈14          | ≈10–11           |
| B   | `--staff-distance 4.5 --min/max-system 3`      | ≈3,7         | ≈6,8         | ≈10–11           |
| C   | staff 4.5, min 3, **max 14**                   | ≈14          | ≈14          | ≈10–11           |
| D   | staff 4.5, min 3, **max 20**                   | ≈20          | ≈20          | ≈10–11           |
| F   | `--staff-distance 1` + min/max 3               | ≈3,7         | ≈6,8         | ≈10–11           |

SVG’s destijds: `generated/spike-compact/` (lokaal).

## Conclusies (spike)

1. **Lage min + ruime max ≠ compact.** MuseScore vult tot
   `maxSystemDistance`. Compact vraagt **lage max** (min≈max laag).
2. **Variabele systeemgaps** bij strakke min=max: inhoud (cues/maatnummers)
   duwt lokaal boven de Style-vloer (≈3,7 vs ≈6,8 sp).
3. **`--staff-distance` alleen** verandert SA↔TB hier nauwelijks; lyrics
   tussen de balken domineren. Wel: **`lyricsMinTop/BottomDistance`**
   (mss-sync) → dichtere balken (zie
   `examples/bug-cases/ektinia-lyric-spike-README.md`).

## Product: `--compact`

Op `mvsa mscz` / `pdf` / `svg` (bron `.mvsa`):

| Sleutel                         | Waarde                                      |
| ------------------------------- | ------------------------------------------- |
| `min`/`maxSystemDistance`       | **7** / **7** (hook vs maatnummer)          |
| `lyricsMinTop/Bottom/Distance`  | **0.1** (SA/TB dichter)                     |
| `measureSpacing`                | **1.6**                                     |
| lyric woordspaties              | trailing spatie op woord-einde-lyrics       |
| pagina-marge boven/onder        | **5** mm                                    |

Style naar `.mscx` **én** `score_style.mss`. **Andere Style-CLI-opties
winnen** van `--compact` (per sleutel).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa pdf lied.mvsa --compact
mvsa pdf lied.mvsa --compact --min-system-distance 9 --max-system-distance 9
```

Normatieve docs: [`docs/formats/mscz.md`](../../../docs/formats/mscz.md),
[`docs/reference/cli/mvsa.md`](../../../docs/reference/cli/mvsa.md).
