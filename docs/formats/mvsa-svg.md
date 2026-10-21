# Partituur-SVG uit `.mvsa` of `.mscz` (koormap-brug)

Afgeleide **partituur-SVG**, inhoudshoogte na trim. Bron `.mvsa`: muziek-only
(geen titel/colofon). Bron `.mscz`: MuseScore tekent wat er al in het bestand
staat (inclusief Style/fonts). Bedoeld voor koormap-pagina’s
(bibliotheek-shortcode `muziek` later).

| Onderwerp                    | Waar                                                               |
| ---------------------------- | ------------------------------------------------------------------ |
| CLI                          | [`vsa mvsa svg`](../reference/cli/mvsa.md#vsa-mvsa-svg)            |
| MSCZ-layout ``muziek``       | [`.mscz` layoutprofielen](mscz.md#layoutprofielen---layout)        |
| Score-IR (later schermpad)   | [score-ir](score-ir.md) · [partituur-ir](../plans/partituur-ir.md) |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek.svg
vsa mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-muziek-tr.svg --transparent
vsa mvsa svg generated\spike-mscz\1a.mscz -o generated\spike-svg\1a-from-mscz.svg
```

Default na trim: **witte** achtergrond. ``--transparent`` laat de achtergrond
leeg (handig op gekleurde pagina’s).

Bij bron `.mvsa`: optioneel systeemafstand, fonts en
``--measure-spacing`` — zelfde Style-opties als bij
[`mvsa mscz`](../reference/cli/mvsa.md#vsa-mvsa-mscz). Bij bron `.mscz`
staan die waarden al in het bestand; Style-CLI-opties gelden dan niet.

**Brug:** MuseScore tekent de SVG. Een gedeelde browser-renderer (OSMD /
Score-IR) voor koormap én CoriB komt later; dit product dekt nu de koormap-behoefte.
