# Partituur-SVG uit `.mvsa` of `.mscz` (koormap-brug)

Afgeleide **partituur-SVG**, inhoudshoogte na trim. Bron `.mvsa`: muziek-only
(geen titel/colofon). Bron `.mscz`: MuseScore tekent wat er al in het bestand
staat (inclusief Style/fonts). Bedoeld voor koormap-pagina’s
(bibliotheek-shortcode `muziek` later). Past het stuk op één MuseScore-pagina,
dan één `.svg`; anders een **bladreeks** (`stem-1.svg`, `stem-2.svg`, …).

| Onderwerp                    | Waar                                                               |
| ---------------------------- | ------------------------------------------------------------------ |
| CLI                          | [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg)            |
| MSCZ-layout ``muziek``       | [`.mscz` layoutprofielen](mscz.md#layoutprofielen---layout)        |
| Score-IR (later schermpad)   | [score-ir](score-ir.md) · [partituur-ir](../plans/partituur-ir.md) |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek.svg
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek-tr.svg --transparent
mvsa svg generated\spike-mscz\1a.mscz -o generated\spike-svg\1a-from-mscz.svg
```

Default na trim: **witte** achtergrond. ``--transparent`` laat de achtergrond
leeg (handig op gekleurde pagina’s).

Bij bron `.mvsa`: optioneel ``--compact`` (dichtste Style-baseline; andere
Style-opties winnen), systeemafstand, stafafstand (``--staff-distance``),
pagina-marges (``--page-margin-top`` / ``--page-margin-bottom``), fonts en
``--measure-spacing`` — zelfde Style-opties als bij
[`mvsa mscz`](../reference/cli/mvsa.md#mvsa-mscz) / [`.mscz`](mscz.md).
Bij bron `.mscz` staan die waarden al in het bestand; Style-CLI-opties
gelden dan niet.

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
