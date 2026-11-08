# Spike: Score-IR naar eigen SVG

Dit is een proef. OSMD en MuseScore blijven de gewone paden.
De contract-hubs zijn niet gewijzigd.

Drie stukken, één systeem per stuk:

- Alleluia toon 8, `examples/bug-cases/corib/alleluia-toon-8.mvsa`.
  De sopraan op de laatste «le» is `so` (C5), boven de G van de alt.
- Alleluia toon 2, `examples/bug-cases/corib/alleluia-toon-2.mvsa`.
  Hier zit een liggende streep ín het melisma (`-&/`).
- Vredeslitanie (1a), `examples/mvsa/1a-vredeslitanie.mvsa`.
  Enkele streep, herhaling en een dubbele streep.

Nootkoppen, sleutels, mollen, kruisen, de stokloze `||O||`, de
systeemaccolade en de herhaalpuntjes zijn contouren uit Bravura
(SMuFL, SIL Open Font License). Een maatstreep is geen teken: dat is
een lijn over de balk, dun, of dun-plus-dik bij een slotstreep.

De VSA boven de lettergrepen is de hoogtebeweging van de sopraan.
Een kale liggende streep (`-`) blijft weg. Die streep komt alleen
in beeld binnen een melisma dat ook stijgt of daalt (`-&/` of `-&\\`).
Een onderstreping staat op de nootpositie waar de bron een lengteteken
heeft (`_`, `__`). Bij «lu_&~&~&_» zijn dat de eerste en de laatste noot.

| Teken                                                                        | Afspraak                                              |
| ---------------------------------------------------------------------------- | ----------------------------------------------------- |
| Stok sopraan/tenor omhoog, alt/bas omlaag                                    | S4                                                    |
| Recite: randnoten, stokloze `\|\|O\|\|`, middenlettergrepen alleen als tekst | S8                                                    |
| Melisma: slur alleen over de toonwissel                                      | S13                                                   |
| Hoogtestrepen en onderstreping van de sopraan                                | VSA van dit stuk, afgeleid uit toonhoogte en lengte   |

Het SVG-bestand is het plaatje (download, afdrukken, in Markdown).
`width="100%"` en een viewBox laten het meeschalen met het venster.
Open `index.html` en versmal het venster: het beeld wordt kleiner, de
systeemindeling blijft gelijk. Opnieuw afbreken bij een smal venster doet
deze proef niet.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\bug-cases\corib\alleluia-toon-8.mvsa -o examples\spikes\score-ir-svg\alleluia-toon-8.svg --from-mvsa
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\bug-cases\corib\alleluia-toon-2.mvsa -o examples\spikes\score-ir-svg\alleluia-toon-2.svg --from-mvsa
python examples\spikes\score-ir-svg\render_score_ir_svg.py examples\mvsa\1a-vredeslitanie.mvsa -o examples\spikes\score-ir-svg\1a-vredeslitanie.svg --from-mvsa
```

Test:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
set PYTHONPATH=src
python -m pytest tests\test_score_ir_svg_spike.py
```
