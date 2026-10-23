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

## Gap-audit SVG layout `muziek` (2026-10-23)

Tegen `schermpartituur.md` §4. Alleen **code/contract-lezing** (geen
nieuwe MuseScore-rendersteekproef in deze run). Keten:
`.mvsa` → partituur-MusicXML → MSCZ (`music_only`) → MuseScore SVG.

| Id / eis                                      | Stand SVG `muziek`                                                                                                                      | Oordeel                       |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| O1 Titel/credits uit                          | `music_only` → `_strip_header_footer_colophon_for_muziek`                                                                               | OK                            |
| O2 Partijnamen uit                            | `_clear_instrument_names` + style visibility 0                                                                                          | OK                            |
| O3 Metronoom uit                              | Tempo `visible=0`; MusicXML metronoom `print-object=no`                                                                                 | OK*                           |
| O4 Geen maatsoort                             | MusicXML `<senza-misura/>`; checklist M3                                                                                                | OK†                           |
| O5 Maatnummers begin systeem                  | `measureNumberSystem=1`, `interval=0`                                                                                                   | OK                            |
| O6 Source Sans 3                              | Style lyrics/staff/system/… = Source Sans 3                                                                                             | OK‡                           |
| O7 Systeemovergangen / cues niet afkappen     | MuseScore-layout; `@mscz-newline`                                                                                                       | Deels                         |
| O8 Cue juiste maat + SystemText               | Promote StaffText→SystemText; geen mid-HBox                                                                                             | OK                            |
| O8–O9 Wrap / niet over maatstreep / inklappen | Wrap op `...` (`wrap_tekst_at_ellipsis`); **geen** OSMD-inklappen-naar-1-regel-als-past; **geen** “cue blijft staan na centreren noten” | Gap                           |
| O10 Noten+lyrics centreren in maat            | MuseScore `measureSpacing`; geen OSMD-`centerMeasureContents`                                                                           | Gap                           |
| O11–O13 Korte/lange stukken, wit              | Style afstanden; lange stukken: SVG-pagina kan falen (één schermpagina)                                                                 | Deels                         |
| §4.4 Speelplan-nav                            | Zelfde partituur-MusicXML + MSCZ als blad-SVG                                                                                           | OK (mvsa)                     |
| S4 Eén schermpagina                           | Bekend productgedrag                                                                                                                    | Bewust anders dan OSMD-scroll |

\* Tempo-**woord** (`@tempo 72 "Andante"`) blijft zichtbaar — dat is geen
metronoom-glyph; geen gap tenzij product dat ook wil verbergen.  
† Residual risico was open; **steekproef 2026-10-23** (catalogus
`alleluia/9a-toon-1/groningen/….mvsa.svg` én bug-case-kopie): geen class
`TimeSig` / `Title` / `Composer` / `Metronome`; bron heeft wel
`@title "Alleluia - Toon 1"` — die tekst staat **niet** in de SVG. Enige
`<title>mvsa-…</title>` = SVG-documentmeta (tijdelijke exportnaam), geen
partituurtitel. → O1/O4 voor dit stuk: **geen gap in de SVG**.  
‡ Font moet op de MuseScore-machine geïnstalleerd zijn; anders fallback.

### VSA-SVG (apart pad)

Primair scherm voor `.vsa` (`svg_export` / eigen renderer): **niet** de
MuseScore-`muziek`-keten. Waarschijnlijk **niet** §4-pariteit (lettertype,
cues-regels, speelplan). Buiten scope van “fix `muziek`”; apart ticket als
VSA-scherm ook §4 moet volgen.

### Voorgestelde fix-volgorde (nog niet doen)

1. Steekproef: één `.mvsa.svg` op 4/4-glyph + metronoom + titel (visueel).  
2. Cue-pariteit waar MuseScore het toelaat (breedte/wrap); documenteer wat
   OSMD-only blijft (inklappen, cue-anker na centreren, noten-centreren).  
3. VSA-SVG §4 alleen na expliciete productkeuze.
