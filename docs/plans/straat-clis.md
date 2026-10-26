# Straat-CLIs en producten (plan)

Status: fases **1–7e gedaan**; daarna **universele productcatalogus**
(elk product uit elke bronstraat; volle `{straat} products`) — zie
[contract-index — universele productcatalogus](../formats/contract-index.md#universele-productcatalogus).

Normatieve meta-spec: [products-meta.md](../formats/products-meta.md).

Dit plan is **niet** de plek voor print-/melisma-/layout-regels. Die staan
in de [contract-index](../formats/contract-index.md) en de hubs die daar
genoemd worden.

## Doelbeeld

Eén CLI per **straat** (bronfamilie):

| Straat (docs) | CLI        | Alias                  |
| ------------- | ---------- | ---------------------- |
| vsa           | `vsa`      | —                      |
| mvsa          | `mvsa`     | —                      |
| mscz          | `mscz`     | —                      |
| md            | `md`       | `markdown` → `md`      |
| manueel       | `manual`   | `manueel` → `manual`   |

Per straat:

1. **Individuele product-subs** — elk product dat bij die bronfamilie
   hoort, via `{straat} {product}` (bijv. `mscz svg`, `mscz pdf`,
   `mvsa svg`). Geen cross-street omweg (`mvsa svg` op `.mscz` is fout).
2. **`products`** — alle standaardproducten van die straat + sidecar-meta.
3. **`normalize`** / **`import`** waar het contract dat vraagt
   (`{doel} import bron.{ext}` ≡ `{bron} {doel}`).

Bibliotheek: orchestratie (`all-products` / check op meta), `bieb`,
`scripts\pdf.cmd` → `index.md.pdf`. Geen blijvende shims voor afgeschafte
namen. Frontmatter: `manueel` / `manual` i.p.v. `artefacten_handmatig`.

Gebruikerscommando’s: de `scripts\*.cmd` wrappers (`mscz`, `mvsa`,
`vsa`, …) — geen `python -m vsa.cli …` in handleidingen of handover.

## Versheid (sidecar-meta)

**Canonieke spec:** [products-meta.md](../formats/products-meta.md).

Schema **2**: bron-hash, product-hashes, én per product een
`generated_at` (wanneer dát productbestand geschreven werd). Top-level
`generated_at` = tijdstip van de meta-schrijfactie.

Individuele product-subs **én** `products` schrijven/bijwerken dezelfde
sidecar (merge per product-key; zie products-meta).

```json
{
  "schema": 2,
  "bron": "lied.mscz",
  "bron_sha256": "…",
  "generated_at": "…",
  "products": {
    "mxl": {
      "file": "lied.mscz.mxl",
      "sha256": "…",
      "generated_at": "…"
    },
    "svg": {
      "file": "lied.mscz.svg",
      "sha256": "…",
      "generated_at": "…"
    }
  }
}
```

## Normalize per straat (check 7e)

| Straat | CLI                     | Status                                                                    |
| ------ | ----------------------- | ------------------------------------------------------------------------- |
| mvsa   | `mvsa normalize`        | aanwezig (spelling / uitlijning)                                          |
| mxl    | `mxl normalize`         | aanwezig (Coria/playback-profiel)                                         |
| mscz   | `mscz normalize`        | aanwezig (layout `partituur`/`muziek`/`plain`)                            |
| vsa    | —                       | **geen** `vsa normalize`; canonieke `.vsa` via authoring + `vsa validate` |
| manual | —                       | uitgesteld (geen contract-hub)                                            |

Regressie: `tests/test_street_normalize.py`.

## Gat-overzicht (fase 7 — afgesloten)

| Straat   | Was omweg / gat                                           | Canonieke CLI                     |
| -------- | --------------------------------------------------------- | --------------------------------- |
| **mscz** | SVG via `mvsa svg` op `.mscz`                             | `mscz svg`                        |
| **mscz** | PDF via `mvsa pdf` op `.mscz`                             | `mscz pdf`                        |
| **mscz** | normalize via bibliotheek/`layout`                        | `mscz normalize`                  |
| **vsa**  | expliciete `normalize`                                    | n.v.t. (zie tabel hierboven)      |
| **alle** | product-`generated_at`                                    | schema 2 in `write_meta`          |

`mscz products` blijft als bundel; intern dezelfde paden als
`mscz mxl` / `mscz svg` / ….

Kale SVG uit `.mscz`: chrome-strip op tijdelijke kopie (layout `muziek`),
bronbestand ongewijzigd — zie [mvsa-svg](../formats/mvsa-svg.md) /
`export_mscz_to_svg`.

## Fasering

| Fase   | Inhoud                                                                   | Status                                                           |
| ------ | ------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| 1      | Contract-index + matrix + PDF-/meta-afspraak in docs                     | **gedaan** ([contract-index](../formats/contract-index.md))      |
| 2      | `import`-alias + extensie-gates + tests                                  | **gedaan** (`mvsa import` / `mscz import`)                       |
| 3      | `products` + sidecar-meta in tooling                                     | **gedaan** (`mvsa`/`mscz`/`vsa products`)                        |
| 4      | Bibliotheek: meta-check, `pdf.cmd`, frontmatter, oude namen weg          | **gedaan**                                                       |
| 5      | Docs-sync bibliotheek + rommelcheck                                      | **gedaan**                                                       |
| 6a     | Spec products-meta schema 2 + invariante                                 | **gedaan** ([products-meta](../formats/products-meta.md))        |
| 6b     | Tooling: schema 2 schrijven + `freshness()` op product-hashes            | **gedaan** (`src/vsa/products_meta.py`)                          |
| 6c     | Bibliotheek: check/regen op meta; in-file stamps afbouwen                | **gedaan** (sync zonder versheidstempels; meta leidend)          |
| **7a** | Spec: product-`generated_at` + merge-regels in products-meta             | **gedaan** ([products-meta](../formats/products-meta.md))        |
| **7b** | Tooling: schrijf/merge `generated_at` per product-key                    | **gedaan** (`products_meta.write_meta`)                          |
| **7c** | `mscz svg` + `mscz pdf` (+ tests/docs); `.mscz` weg bij `mvsa svg`/`pdf` | **gedaan**                                                       |
| **7d** | Overige ontbrekende straat-product-subs (`mscz normalize`, …)            | **gedaan** (`mscz normalize`)                                    |
| **7e** | Docs/man-pages/scripts: alleen `{straat} {product}`; omwegen weg         | **gedaan** (normalize-check alle straten)                        |

## Gerelateerd

- [Formaten & CLI](../formats/index.md)
- [mvsa-conversions](mvsa-conversions.md)
- [canonical-checklists](../formats/canonical-checklists.md)
- [MSCZ-leesbaarheid](../formats/mscz-leesbaarheid.md)
- [kale-muziek-svg-en-uitgaven](kale-muziek-svg-en-uitgaven.md)
