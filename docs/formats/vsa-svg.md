# Muziek-only SVG uit `.vsa` (scherm)

Afgeleide **SVG** met alleen de VSA-notatie (geen titel/colofon). Bedoeld
voor schermweergave op catalogus- en koormap-pagina’s (shortcode `muziek`).
Zelfde productrol als [mvsa-SVG](mvsa-svg.md); andere tekenpipeline
(native VSA-renderer i.p.v. MuseScore).

| Onderwerp | Waar |
| --------- | ---- |
| CLI | [`vsa svg`](../reference/cli/svg.md) |
| Sibling-naam | ``lied.vsa`` → ``lied.vsa.svg`` (default) |
| mvsa-equivalent | [mvsa-SVG](mvsa-svg.md) · [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg) |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa -o generated\vsa\phrase.vsa.svg
```

Print-/download-PDF’s (``.vsa.pdf``) mogen wél titel of andere bladinfo
bevatten; die horen niet in deze SVG.
