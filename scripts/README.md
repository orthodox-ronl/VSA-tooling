# Scripts voor VSA Tooling

Uitvoerbare commando's in `scripts/` (op het zoekpad als `.\scripts`).
De leesbare handleiding voor beheerders staat op de documentatiesite:
[Scripts (cmd)](../docs/formats/scripts.md). Org-conventie:
https://github.com/orthodox-ronl/bron/blob/main/docs/specs/repo-scripts.md

Scripts mogen redactionele `content-source` niet herschrijven.
CI gebruikt `examples\consumer-minimal\content-source`.

Start altijd vanuit de repo-map:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
```

## Notatie

| Commando   | Bron                 | Doel                                                                  |
| ---------- | -------------------- | --------------------------------------------------------------------- |
| `mvsa`     | `.mvsa`              | valideren, `products`, losse `pdf` (geen standaardproduct)            |
| `mxl`      | `.mxl` / `.musicxml` | valideren, normaliseren, omzetten                                     |
| `mscz`     | `.mscz`              | `products`, losse `pdf`                                               |
| `markdown` | `.md`                | `pdf` → `index.md.pdf`, plus `svg` en `text`                          |
| `vsa`      | `.vsa`               | valideren, `products`, losse `pdf` (geen `scripts\vsa.cmd`)           |

`products` schrijft geen `.vsa.pdf` / `.mvsa.pdf` / `.mscz.pdf`.
Pagina-afdruk: `markdown pdf …` → `index.md.pdf`.

## Repository

| Commando                 | Doel                                                             |
| ------------------------ | ---------------------------------------------------------------- |
| `test`                   | pytest (`test -v` voor meer detail; niet `test-verbose`)         |
| `check`                  | CI-spiegel: pytest + consumer-minimal validate/build-markdown    |
| `serve`                  | MkDocs-preview zonder TEv2                                       |
| `serve-tev2`             | MkDocs-preview met TEv2                                          |
| `build`                  | TEv2 + MkDocs `--strict`                                         |
| `build --no-tev2`        | MkDocs zonder TEv2                                               |
| `check-docs`             | docs-hygiëne + vaste voorbeeld-SVG’s                             |
| `clean`                  | tijdelijke Python-bestanden weg                                  |
| `import`                 | zip uit Downloads uitpakken in de repo                           |
| `run-example`            | `vsa` op één voorbeeld-`.vsa`                                    |
| `migrate-metadata`       | dry-run; met `--apply` `@toon` en optioneel `--tempo` op `.mvsa` |
| `install-rendering-deps` | controle of het SVG-lettertype werkt                             |

Oude namen die alleen doorverwijzen: `ci` → `check`, `docs-serve` →
`serve`, `docs-build` → `build --no-tev2`, `bootstrap` → geen aparte
stap. Geen `vsa-products.cmd`.

**Content-migratie metadata** (bibliotheek of tooling-voorbeelden), eerst
zonder `--apply`:

```cmd
cd /d C:\Git\orthodox-ronl\bibliotheek
C:\Git\orthodox-ronl\VSA-tooling\scripts\migrate-metadata.cmd content-source

cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\migrate-metadata.cmd examples\mvsa --apply
```

Alleen `@toon` als die uit `@title` (`Toon N`) of pad (`toon-N`) volgt.
Met `--tempo` ook `@tempo 130` als die ontbreekt (export-default is al 130).
