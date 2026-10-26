# `vsa pdf` — verouderd (gebruik `md pdf`)

`vsa pdf` blijft werken als **alias** voor
[`md pdf`](md.md#md-pdf): Markdown met VSA → A4-PDF via Edge/Chrome.

Bij elke aanroep schrijft de CLI een waarschuwing naar stderr:

```text
Let op: `vsa pdf` is verouderd; gebruik `md pdf` (zelfde opties; default sibling *.md.pdf).
```

## Synopsis (alias)

```text
vsa pdf [-h] [--config CONFIG] [--content-root CONTENT_ROOT]
         [--bron-root BRON_ROOT] [--max-line-width MAX_LINE_WIDTH]
         [--chrome CHROME] [-o OUTPUT]
         input
```

Argumenten en gedrag zijn gelijk aan [`md pdf`](md.md#md-pdf), inclusief
default sibling-naam (`index.md` → `index.md.pdf`).

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
md pdf content-source\praktijk\samenstellingen\20260811-di-liturgie.md
```

## Wat is dit niet?

- **Partituur-PDF** uit `.mvsa` / `.mscz`: [`mvsa pdf`](mvsa.md#mvsa-pdf) /
  [`mscz pdf`](mscz.md) (MuseScore; checklist P*).
- **Notatie-SVG** uit `.vsa`: [`vsa svg`](svg.md).

## Zie ook

- [`md`](md.md) — canonieke Markdown-straat (`pdf` / `svg` / `text`)
- [`vsa build-markdown`](build-markdown.md)
- [contract-index — site-Markdown-PDF](../../formats/contract-index.md)
