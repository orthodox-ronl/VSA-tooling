# Schermeisen — overdracht (archief)

**Canonieke norm:**  
[`bibliotheek/docs/specs/schermpartituur.md`](https://github.com/orthodox-ronl/bibliotheek/blob/development/docs/specs/schermpartituur.md)
(besluit 8 = A).

**Speelplan-bladvorm (patronen):**  
[`docs/specification-mvsa/speelplan.md`](../specification-mvsa/speelplan.md)

Dit bestand was de verenigings-/besluitnotitie (2026-10-23). Inhoud is
opgenomen in `schermpartituur.md`. OSMD-zichtbaarheidscheck (besluit 9):
`bibliotheek/scripts/osmd-nav-check/`.

## Score-IR / from-ir (deze repo)

Speelplan-navigatie in Score-IR → `.from-ir.musicxml` volgt dezelfde
helpers als partituur-MusicXML. Regressie:
`tests/test_score_ir_musicxml.py`.

## SVG layout `muziek` (open vervolg)

Export-gaps t.o.v. het gedeelde pakket (titel/chrome uit, Source Sans 3,
maatnummers, cue wrap/centreer) blijven een **aparte** VSA-tooling-stap;
zie schermpartituur §5 / §9.
