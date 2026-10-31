# Partituur-SVG uit `.mvsa` of `.mscz` (koormap-brug)

Afgeleide **kale partituur-SVG**, inhoudshoogte na trim. Alleen muziek:
notenbalken, lyrics, uitvoeringsaanwijzingen, maatnummers e.d. — **geen**
titel, copyright, colofon of bewerkersregel. Bron `.mvsa`: layout ``muziek``
via [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg). Bron `.mscz`:
[`mscz svg`](../reference/cli/mscz.md) — blad-chrome op een tijdelijke kopie
gestript (het bron-``.mscz`` blijft ongewijzigd; Style-footer/header ook in
``score_style.mss``).

Productvorm: **één tall-SVG** (hoge MuseScore-`pageHeight`) in **compact**
Style — geen A4-bladreeks (`stem-N.svg`). Die sibling voedt scherm-fallback
én `index.md.pdf` (systeemsnee naar A4). A4-paginering zit in de PDF, niet
in het SVG-product.

| Onderwerp                    | Waar                                                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| CLI (``.mvsa``)              | [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg)                                                                                  |
| CLI (``.mscz``)              | [`mscz svg`](../reference/cli/mscz.md)                                                                                           |
| MSCZ-layout ``muziek``       | [`.mscz` layoutprofielen](mscz.md#layoutprofielen---layout)                                                                      |
| `--engine osmd`              | Score-IR → from-ir MusicXML → headless OSMD + S8 A1-adapter ([`scripts/osmd-svg`](../../scripts/osmd-svg/)); witte `vsa-page-bg` |
| Score-IR / schermpad         | [score-ir](score-ir.md) · [partituur-ir](../plans/partituur-ir.md) §7                                                            |

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

Na MuseScore-export schuift de toolchain te krappe opeenvolgende lyric-paths
uit elkaar (~0,45 spatium), zodat woorden niet als «desheils» aan elkaar
plakken — MuseScore zelf houdt die bboxes vrijwel tegen elkaar.

Bij bron `.mvsa`: compact is de **default** voor SVG (dichtste Style-baseline);
expliciete Style-opties winnen. Zelfde vlaggen als bij
[`mvsa mscz`](../reference/cli/mvsa.md#mvsa-mscz) / [`.mscz`](mscz.md)
(systeemafstand, marges, fonts, ``--measure-spacing``). ``--compact`` blijft
geldig (no-op t.o.v. de default). Bij bron `.mscz` (`mscz svg`) past de
export compact + tall op een tijdelijke kopie; blad-chrome wordt gestript.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa --min-system-distance 9 --max-system-distance 9
```

**Brug:** default `--engine musescore` tekent de tall-SVG (scherm-fallback +
print-bouwsteen voor `index.md.pdf`). Optioneel `--engine osmd` schrijft een
SVG via headless OSMD uit Score-IR (geen MuseScore; vereist Node +
`scripts/osmd-svg`). Headless OSMD graveert met profiel `coribCompact`:
dichtere balkafstand, lyrics tussen de balken, Source Sans 3, S10
(maatnummers alleen aan systeembegin), zonder pixel-pariteit met
MuseScore (S8/S13). Lettergrepen mogen niet overlappen
([mscz-leesbaarheid](mscz-leesbaarheid.md) §2). S8-recite: na render past
de A1-adapter spacer-hide toe (`notehead none`) en tekent ``||O||`` op
breve-midden; zie [osmd-s8-recite](../plans/osmd-s8-recite.md) en
[score-ir](score-ir.md). Scherm-hoofdpad op de site blijft Score-IR/OSMD-embed
([kale-muziek-svg-en-uitgaven](../plans/kale-muziek-svg-en-uitgaven.md) §4).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
cd scripts\osmd-svg && npm install && npx puppeteer browsers install chrome
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\mvsa\1a-vredeslitanie.mvsa -o generated\spike-svg\1a-osmd.svg --engine osmd
```
