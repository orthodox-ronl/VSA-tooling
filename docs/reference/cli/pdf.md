# `vsa pdf` — partituur-PDF uit `.vsa`

Maak een print-PDF van een eenstemmige `.vsa`-bron via MuseScore
(checklist P*). Dit is **los gereedschap**: geen standaardproduct.
`vsa products` schrijft geen `.vsa.pdf`.

Pagina-afdruk van site-Markdown (`index.md.pdf`) gaat via
[`markdown pdf`](markdown.md#markdown-pdf), niet via dit commando.

## Synopsis

```text
vsa pdf [-h] [-o OUTPUT] [--musescore PATH] path
```

| Argument / optie   | Betekenis                                                              |
| ------------------ | ---------------------------------------------------------------------- |
| `path`             | Eén `.vsa` of een map (recursief alle `.vsa`).                         |
| `-o`, `--output`   | Uitvoer-PDF. Alleen bij precies één bron. Default: sibling `.vsa.pdf`. |
| `--musescore PATH` | Pad naar MuseScore (default: auto).                                    |

Andere extensies worden geweigerd met een tip naar de juiste straat:
`.md` → `markdown pdf`, `.mvsa` → `mvsa pdf`, `.mscz` → `mscz pdf`.

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa pdf examples\minimal\valid-demo.vsa
vsa pdf examples\minimal\valid-demo.vsa -o generated\demo.pdf
```

## Wat is dit niet?

- **Pagina-PDF** uit Markdown: [`markdown pdf`](markdown.md#markdown-pdf)
  (`index.md.pdf`).
- **Partituur-PDF** uit `.mvsa` / `.mscz`: [`mvsa pdf`](mvsa.md#mvsa-pdf) /
  [`mscz pdf`](mscz.md).
- **Standaardproducten**: [`vsa products`](products.md) (geen pdf).

## Zie ook

- [contract-index — PDF](../../formats/contract-index.md)
- [`vsa mscz`](index.md) — tussenstap partituur-`.mscz`
