# Partituur-SVG uit `.mvsa` of `.mscz` (koormap-brug)

Afgeleide **kale partituur-SVG**, inhoudshoogte na trim. Alleen muziek:
notenbalken, lyrics, uitvoeringsaanwijzingen, maatnummers e.d. — **geen**
titel, copyright, colofon of bewerkersregel. Bron `.mvsa`: layout ``muziek``
via [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg). Bron `.mscz`:
[`mscz svg`](../reference/cli/mscz.md) — blad-chrome op een tijdelijke kopie
gestript (het bron-``.mscz`` blijft ongewijzigd); Style/fonts uit het bestand
blijven. Bedoeld voor koormap-pagina’s (bibliotheek-shortcode `muziek` later).
Past het stuk op één MuseScore-pagina, dan één `.svg`; anders een **bladreeks**
(`stem-1.svg`, `stem-2.svg`, …).

| Onderwerp                    | Waar                                                               |
| ---------------------------- | ------------------------------------------------------------------ |
| CLI (``.mvsa``)              | [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg)                    |
| CLI (``.mscz``)              | [`mscz svg`](../reference/cli/mscz.md)                             |
| MSCZ-layout ``muziek``       | [`.mscz` layoutprofielen](mscz.md#layoutprofielen---layout)        |
| Score-IR (later schermpad)   | [score-ir](score-ir.md) · [partituur-ir](../plans/partituur-ir.md) |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek.svg
scripts\mvsa.cmd svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek-tr.svg --transparent
scripts\mscz.cmd svg generated\spike-mscz\1a.mscz -o generated\spike-svg\1a-from-mscz.svg
```

Default na trim: **witte** achtergrond. ``--transparent`` laat de achtergrond
leeg (handig op gekleurde pagina’s). De trim zet ``viewBox`` op de getekende
inhoud inclusief MuseScore-``transform`` (glyphs staan lokaal rond ``(0,0)``);
anders zouden linker- en bovenmarge veel te breed blijven.

Bij bron `.mvsa`: optioneel ``--compact`` (dichtste Style-baseline; andere
Style-opties winnen), systeemafstand, stafafstand (``--staff-distance``),
pagina-marges (``--page-margin-top`` / ``--page-margin-bottom``), fonts en
``--measure-spacing`` — zelfde Style-opties als bij
[`mvsa mscz`](../reference/cli/mvsa.md#mvsa-mscz) / [`.mscz`](mscz.md).
Bij bron `.mscz` (`mscz svg`) gelden Style-CLI-opties niet (waarden staan al
in het bestand); blad-chrome wordt altijd gestript vóór de SVG-export.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --compact
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --compact --min-system-distance 4 --max-system-distance 4
```

**Brug:** MuseScore tekent de SVG. Afspraak over kale scherm- vs blad-SVG,
catalogus-PDF vs koormap-pagina-PDF, en latere tall scherm-SVG / Score-IR:
[kale-muziek-svg-en-uitgaven](../plans/kale-muziek-svg-en-uitgaven.md).
Een gedeelde browser-renderer (OSMD / Score-IR) voor koormap én CoriB blijft
het beoogde schermpad (plan §4); dit MuseScore-product dekt nu de
koormap-brug.
