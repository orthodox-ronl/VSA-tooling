# Straat-CLIs en producten (plan)

Status: fases **1–5 gedaan**; fase **6** (products-meta schema 2 +
tooling/bibliotheek op meta-hashes) **open** — normatieve spec:
[products-meta.md](../formats/products-meta.md).

Dit plan is **niet** de plek voor print-/melisma-/layout-regels. Die staan
in de [contract-index](../formats/contract-index.md) en de hubs die daar
genoemd worden.

## Doelbeeld

Eén CLI per **straat** (bronfamilie):

| Straat (docs) | CLI      | Alias                |
| ------------- | -------- | -------------------- |
| vsa           | `vsa`    | —                    |
| mvsa          | `mvsa`   | —                    |
| mscz          | `mscz`   | —                    |
| manueel       | `manual` | `manueel` → `manual` |

Per straat: individuele product-subs, `products` (alles + sidecar-meta),
`normalize` (bestaand contract), `import` (catalogus-vrij;
`{doel} import bron.{ext}` ≡ `{bron} {doel}`).

Bibliotheek: orchestratie (`all-products` / check op meta), `bieb`,
`scripts\pdf.cmd` → `index.md.pdf`. Geen blijvende shims voor afgeschafte
namen. Frontmatter: `manueel` / `manual` i.p.v. `artefacten_handmatig`.

## Versheid (sidecar-meta)

**Canonieke spec:** [products-meta.md](../formats/products-meta.md).

Doelbeeld (schema **2**): tooling schrijft bron-hash **én** hashes van
elk afgeleid bestand. Invariante: claim “product \(H_A\) uit bron \(H_B\)”
klopt, of meta is niet `ok`. Bibliotheek leest meta; zet geen parallelle
herkomststempel als bron van waarheid.

Tooling schrijft schema **2** (fase 6b). Schema-1-sidecars tellen als
stale tot opnieuw `products`.

```json
{
  "schema": 2,
  "bron": "lied.mvsa",
  "bron_sha256": "…",
  "generated_at": "…",
  "products": {
    "mxl": { "file": "lied.mvsa.mxl", "sha256": "…" },
    "svg": { "file": "lied.mvsa.svg", "sha256": "…" }
  }
}
```

Diepere `mxl validate` blijft apart (`--only-invalid`).

## Contracten

Normatieve inhoudsopgave + straat×product-tabel:
**[contract-index](../formats/contract-index.md)**.

OSMD / Score-IR vallen onder dezelfde checklists (bedoelde vorm); emit
verschilt alleen waar de hub dat toelaat ([osmd-s8-recite](osmd-s8-recite.md),
[partituur-ir](partituur-ir.md)).

## Fasering

| Fase | Inhoud                                                          | Status                                                      |
| ---- | --------------------------------------------------------------- | ----------------------------------------------------------- |
| 1    | Contract-index + matrix + PDF-/meta-afspraak in docs            | **gedaan** ([contract-index](../formats/contract-index.md)) |
| 2    | `import`-alias + extensie-gates + tests                         | **gedaan** (`mvsa import` / `mscz import`)                  |
| 3    | `products` + sidecar-meta in tooling                            | **gedaan** (`mvsa`/`mscz`/`vsa products`)                   |
| 4    | Bibliotheek: meta-check, `pdf.cmd`, frontmatter, oude namen weg | **gedaan**                                                  |
| 5    | Docs-sync bibliotheek + rommelcheck                             | **gedaan**                                                  |
| 6a   | Spec products-meta schema 2 + invariante                        | **gedaan** ([products-meta](../formats/products-meta.md))   |
| 6b   | Tooling: schema 2 schrijven + `freshness()` op product-hashes   | **gedaan** (`src/vsa/products_meta.py`)                     |
| 6c   | Bibliotheek: check/regen op meta; in-file stamps afbouwen       | **gedaan** (sync zonder versheidstempels; meta leidend)     |

## Gerelateerd

- [Formaten & CLI](../formats/index.md)
- [mvsa-conversions](mvsa-conversions.md)
- [canonical-checklists](../formats/canonical-checklists.md)
- [MSCZ-leesbaarheid](../formats/mscz-leesbaarheid.md)
