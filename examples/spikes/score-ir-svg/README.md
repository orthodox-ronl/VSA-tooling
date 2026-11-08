# Spike: Score-IR naar eigen SVG

Dit is een proef. OSMD en MuseScore blijven de gewone paden.
De contract-hubs zijn niet gewijzigd.

Eén stuk: de Alleluia toon 8 uit
`examples/bug-cases/corib/alleluia-toon-8.mvsa`.
Daar is de sopraan op de laatste «le» `so` (C5), boven de G van de alt.
`examples/mvsa/alleluia-toon-8.mvsa` schrijft die noot als `so-` (C4).

Nootkoppen, sleutels, mollen, kruisen en de stokloze `||O||` zijn
contouren uit Bravura (SMuFL, SIL Open Font License).
De VSA-strepen boven de lettergrepen zijn de echte hoogtebeweging van de
sopraan: een liggende streep zolang de toon gelijk blijft, een schuine
streep waar de toon stijgt of daalt.

| Teken                                                                        | Afspraak                                              |
| ---------------------------------------------------------------------------- | ----------------------------------------------------- |
| Stok sopraan/tenor omhoog, alt/bas omlaag                                    | S4                                                    |
| Recite: randnoten, stokloze `\|\|O\|\|`, middenlettergrepen alleen als tekst | S8                                                    |
| Melisma «lu»: extender onder de lettergreep, slur alleen over de toonwissel  | S13                                                   |
| Hoogtestrepen van de sopraan boven de lettergrepen                           | VSA van dit stuk, afgeleid uit de toonhoogtes         |

Het SVG-bestand is het plaatje (download, afdrukken, in Markdown).
`width="100%"` en een viewBox laten het meeschalen met het venster.
Open `index.html` en versmal het venster: het beeld wordt kleiner, de
systeemindeling blijft gelijk. Opnieuw afbreken bij een smal venster doet
deze proef niet.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\spikes\score-ir-svg\alleluia-toon-8.score-ir.json -o examples\spikes\score-ir-svg\alleluia-toon-8.svg
```

Verse Score-IR uit de bron, daarna hetzelfde SVG:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\bug-cases\corib\alleluia-toon-8.mvsa -o examples\spikes\score-ir-svg\alleluia-toon-8.svg --from-mvsa
```

Test:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python -m pytest tests\test_score_ir_svg_spike.py
```
