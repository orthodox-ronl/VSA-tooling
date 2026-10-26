# Spike B: één hoge SVG + index.md → pagina-PDF

**Script:** `spike_tall_svg.py`  
**Bronnen:** `vriendelijk-licht-default-groningen.mscz`, `vriendelijk-licht-index.md`

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python examples\bug-cases\spike_tall_svg.py
```

## Zichtbare artefacten (deze map)

| Bestand | Wat |
| ------- | --- |
| `vriendelijk-licht-a4-1.svg`, `-a4-2.svg` | Huidige A4-bladreeks (`mscz svg`) |
| `vriendelijk-licht-tall.svg` | Één hoge strip (`pageHeight` + chrome-strip) |
| `vriendelijk-licht-index.md.pdf` | **Proef-PDF:** shortcodes uit de index (`kop`, tekst, `bieb`) + tall-SVG in A4-stroken |
| `vriendelijk-licht-index-preview.html` | Zelfde inhoud in de browser |

(Geen verborgen `spike-tall-svg-out/` meer.)

## Wat de proef-PDF doet

1. Leest `vriendelijk-licht-index.md` (frontmatter weg).
2. Shortcodes: `kop` → gecentreerde titel; overige tekst → regel; `bieb` → muziekblok.
3. Muziek = `vriendelijk-licht-tall.svg`, geschaald op breedte; A4-einde alleen
   **tussen systemen** (midden in de gap op `StaffLines`-clusters), niet door
   een notenbalk. Rest van blad 1 eerst vullen — geen wees-titelpagina.

## Verwacht resultaat

- Tall: **1** SVG (niet 2 A4-pagina’s).
- PDF: titel + «bron: …» + begin muziek op **blad 1**, rest op volgende A4.

## Productie (nog open)

`mscz svg --continuous` (of equivalent) + bibliotheek-`pdf.cmd` op tall-SVG.  
Scherm blijft Score-IR/OSMD — zie `docs/plans/kale-muziek-svg-en-uitgaven.md` §4.
