# Spike: Score-IR naar eigen SVG

Dit is een proef. OSMD en MuseScore blijven de gewone paden.
De contract-hubs zijn niet gewijzigd.

Eén stuk: Alleluia toon 8 (`examples/mvsa/alleluia-toon-8.mvsa`).
De tekening laat vier dingen zien:

| Teken                                                                        | Afspraak                          |
| ---------------------------------------------------------------------------- | --------------------------------- |
| Stok sopraan/tenor omhoog, alt/bas omlaag                                    | S4                                |
| Recite: randnoten, stokloze `\|\|O\|\|`, middenlettergrepen alleen als tekst | S8                                |
| Melisma «lu»: extender onder de lettergreep, slur alleen over de toonwissel  | S13                               |
| Eén schuine VSA-hoogtestreep op de eerste «Al»                               | spike-overlay, geen Score-IR-veld |

De overlay staat in `accent.json`. Die hoort niet in Score-IR 0.1.

Het SVG-bestand is het plaatje (download, afdrukken, in Markdown).
`width="100%"` en een viewBox laten het meeschalen met het venster.
Open `index.html` en versmal het venster: het beeld wordt kleiner, de
systeemindeling blijft gelijk. Opnieuw afbreken bij een smal venster doet
deze proef niet.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\spikes\score-ir-svg\alleluia-toon-8.score-ir.json -o examples\spikes\score-ir-svg\alleluia-toon-8.svg --accent examples\spikes\score-ir-svg\accent.json
```

Verse Score-IR uit de bron, daarna hetzelfde SVG:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\mvsa\alleluia-toon-8.mvsa -o examples\spikes\score-ir-svg\alleluia-toon-8.svg --from-mvsa --accent examples\spikes\score-ir-svg\accent.json
```

Test:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python -m pytest tests\test_score_ir_svg_spike.py
```
