# Straat-CLIs en producten (plan)

Status: fases **1–5 gedaan** (contract-index, `import`, `products` + meta,
bibliotheek meta/`pdf.cmd`/`manueel`, wrappers weg, docs-sync).

Dit plan is **niet** de plek voor print-/melisma-/layout-regels. Die staan
in de [contract-index](../formats/contract-index.md) en de hubs die daar
genoemd worden.

## Doelbeeld

Eén CLI per **straat** (bronfamilie):

| Straat (docs) | CLI | Alias |
| --- | --- | --- |
| vsa | `vsa` | — |
| mvsa | `mvsa` | — |
| mscz | `mscz` | — |
| manueel | `manual` | `manueel` → `manual` |

Per straat: individuele product-subs, `products` (alles + sidecar-meta),
`normalize` (bestaand contract), `import` (catalogus-vrij;
`{doel} import bron.{ext}` ≡ `{bron} {doel}`).

Bibliotheek: orchestratie (`all-products` / check op meta), `bieb`,
`scripts\pdf.cmd` → `index.md.pdf`. Geen blijvende shims voor afgeschafte
namen. Frontmatter: `manueel` / `manual` i.p.v. `artefacten_handmatig`.

## Versheid (sidecar-meta)

```json
{
  "schema": 1,
  "bron": "lied.mvsa",
  "bron_sha256": "…",
  "generated_at": "…",
  "products": { "mxl": "lied.mvsa.mxl", "svg": "lied.mvsa.svg" }
}
```

Stale = meta ontbreekt of `bron_sha256` past niet; missing = pad in
`products` ontbreekt. Diepere `mxl validate` blijft apart (`--only-invalid`).

## Contracten

Normatieve inhoudsopgave + straat×product-tabel:
**[contract-index](../formats/contract-index.md)**.

OSMD / Score-IR vallen onder dezelfde checklists (bedoelde vorm); emit
verschilt alleen waar de hub dat toelaat ([osmd-s8-recite](osmd-s8-recite.md),
[partituur-ir](partituur-ir.md)).

## Fasering

| Fase | Inhoud | Status |
| --- | --- | --- |
| 1 | Contract-index + matrix + PDF-/meta-afspraak in docs | **gedaan** ([contract-index](../formats/contract-index.md)) |
| 2 | `import`-alias + extensie-gates + tests | **gedaan** (`mvsa import` / `mscz import`) |
| 3 | `products` + sidecar-meta in tooling | **gedaan** (`mvsa`/`mscz`/`vsa products`) |
| 4 | Bibliotheek: meta-check, `pdf.cmd`, frontmatter, oude namen weg | **gedaan** |
| 5 | Docs-sync bibliotheek + rommelcheck | **gedaan** |

## Gerelateerd

- [Formaten & CLI](../formats/index.md)
- [mvsa-conversions](mvsa-conversions.md)
- [canonical-checklists](../formats/canonical-checklists.md)
- [MSCZ-leesbaarheid](../formats/mscz-leesbaarheid.md)
