# VSA-tooling gebruiken vanuit andere repositories

Deze pagina is de **integratiehandleiding**: hoe je `vsa-tool` in een andere repo
installeert en in CI gebruikt. Volledig werkend voorbeeld:
[VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

## Direct met `pip`

```cmd
python -m pip install "vsa-tool[rendering] @ git+https://github.com/orthodox-ronl/VSA-tooling.git@main"
```

Voor productie bij voorkeur een **tag** i.p.v. `@main`, bijvoorbeeld `@v0.1.0`
(wanneer die bestaat).

Daarna:

```cmd
vsa --version
vsa validate content
vsa svg input.vsa output.svg
```

Markdown + SVG:

```cmd
vsa build-markdown content generated\content generated\static\vsa --assets-url-prefix /vsa
```

Extra `[rendering]` is nodig voor SVG (Pillow + fonts in het package/repo).

## Minimale consumer-layout

```text
mijn-repo/
  content/                 # of content-source/
    voorbeeld.md           # Markdown met ::: vsa-notatie
  generated/               # build-output (niet committen)
  .github/workflows/
    render.yml             # zie hieronder
```

Geen Hugo verplicht: alleen `validate` / `svg` / `musicxml` volstaat voor
batchconversie. Hugo (of MkDocs) komt pas bij een publicatiesite — zie
[Consumer-site](../manuals/consumer-site.md).

## In GitHub Actions (render)

```yaml
name: Render VSA

on:
  push:
  workflow_dispatch:

jobs:
  vsa:
    uses: orthodox-ronl/VSA-tooling/.github/workflows/vsa-render-reusable.yml@main
    with:
      input_dir: content
      output_dir: generated/vsa/content
      assets_dir: generated/vsa/static/vsa
      assets_url_prefix: /vsa
      output_mode: img
```

De workflow valideert en uploadt gegenereerde Markdown/SVG als artifact.

## GitHub Pages deploy

Na een site-build upload je het artifact en roep je de herbruikbare
deploy-workflow aan. Die draait `check-publication-output.py` (tenzij
overgeslagen) en pusht via `peaceiris/actions-gh-pages@v4` naar `gh-pages`.

**Repo-instelling:** Settings → Pages → Deploy from a branch → `gh-pages` → `/`
(niet “GitHub Actions”).

```yaml
name: Deploy site

on:
  push:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      # … bouw naar public/ …
      - uses: actions/upload-artifact@v7
        with:
          name: pages-site
          path: public
          if-no-files-found: error

  deploy:
    needs: build
    uses: orthodox-ronl/VSA-tooling/.github/workflows/pages-deploy-reusable.yml@main
    with:
      artifact_name: pages-site
      publish_dir: site
      destination_dir: preview
      url_prefix: /mijn-repo/preview/
      pages_url: https://orthodox-ronl.github.io/mijn-repo/preview/
    permissions:
      contents: write
```

| Input                    | Verplicht            | Toelichting                                      |
| ------------------------ | -------------------- | ------------------------------------------------ |
| `artifact_name`          | ja                   | Naam van `upload-artifact` in de build-job       |
| `publish_dir`            | nee (default `site`) | Downloadpad; moet `index.html` bevatten          |
| `destination_dir`        | nee                  | subdirectory op gh-pages (bijv. `preview` of branch-slug); leeg = root |
| `url_prefix`             | ja                   | Publiek pad voor linkcheck, bv. `/koor/preview/` |
| `keep_files`             | nee (default `true`) | `true` als subdirectory-deploys en productie `gh-pages` delen |
| `skip_publication_check` | nee                  | Alleen als de caller zelf al heeft gecontroleerd |
| `pages_url`              | nee                  | URL in log na deploy                             |
| `vsa_tooling_ref`        | nee (default `main`) | Ref voor check-script                            |

Productie-deploy (root van `gh-pages`; sibling-mappen zoals `preview/` en
branch-previews die niet in de nieuwe site-build zitten blijven behouden):

```yaml
  deploy:
    needs: build
    uses: orthodox-ronl/VSA-tooling/.github/workflows/pages-deploy-reusable.yml@main
    with:
      artifact_name: pages-site
      publish_dir: site
      url_prefix: /mijn-repo/
      pages_url: https://orthodox-ronl.github.io/mijn-repo/
    permissions:
      contents: write
```

## Referentie-implementaties

| Repo                                                                         | Wat je ziet                       |
| ---------------------------------------------------------------------------- | --------------------------------- |
| [VSA-demo](https://github.com/orthodox-ronl/VSA-demo)                   | Volledige Hugo-consumer + Pages   |
| Deze repo `docs-pages.yml`                                                   | MkDocs tool-docs op Pages         |
| [bron docs-pages](https://github.com/orthodox-ronl/bron)                | MkDocs + dezelfde deploy-reusable |

## Org-grenzen (D1)

Installeer de tool hier; **dupliceer geen** org-specs. Terminologie en
zangstuk-formaat: [bron — specs](https://orthodox-ronl.github.io/bron/specs/).
