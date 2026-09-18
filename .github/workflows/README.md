# GitHub Actions-workflows (VSA-tooling)

Overzicht van alle workflows in deze map: **wanneer** ze draaien, **waarvoor** je ze gebruikt, en wat je **lokaal** kunt doen in plaats daarvan.

## Snel kiezen

| Ik wil…                                 | Workflow                    | Hoe starten                        |
| --------------------------------------- | --------------------------- | ---------------------------------- |
| Controleren of code groen is (Windows)  | `vsa-ci.yml`                | Automatisch bij push/PR            |
| Controleren of MkDocs bouwt (Linux)     | `docs-build.yml`            | Automatisch bij push/PR            |
| Documentatiesite (MkDocs) publiceren    | `docs-pages.yml`            | Automatisch bij elke push          |
| Release-wheel/sdist + smoke-artifact    | `release-artifacts.yml`     | Actions → handmatig + versienummer |
| Pages deploy vanuit een andere org-repo | `pages-deploy-reusable.yml` | Alleen via `workflow_call`         |
| VSA renderen vanuit een andere org-repo | `vsa-render-reusable.yml`   | Alleen via `workflow_call`         |

## Wat draait automatisch bij een push?

1. **vsa-ci.yml** — Windows: checkout `bron` → bootstrap → pytest + consumer-minimal
2. **docs-pages.yml** — TEv2 + MkDocs → `/` (`main`) of `/preview/` (andere branches)

**docs-build.yml** draait bij **pull_request** (en handmatig), niet bij push — voorkomt
dubbele TEv2/MkDocs-runs naast docs-pages.

MRG auto-commits gebruiken `[skip ci]` zodat die push geen nieuwe CI-cascade start.

Concurrency: `cancel-in-progress: true` op docs-workflows en op
`pages-deploy-reusable` (gh-pages-writes), zodat verouderde/queued deploys niet
15–30 min blijven hangen.

Handmatig: `release-artifacts`, `docs-build` (`workflow_dispatch`).

---

## Workflows in detail

### `docs-pages.yml` — Deploy documentation (MkDocs)

| Veld       | Waarde                                                                                |
| ---------- | ------------------------------------------------------------------------------------- |
| Trigger    | `push` (alle branches)                                                                |
| Runner     | `ubuntu-latest`                                                                       |
| Doel       | TEv2 (mrg-import/mrgt/hrgt/trrt) + `mkdocs build --strict` → Pages `/` of `/preview/` |
| Publiceert | Ja (`pages-deploy-reusable`; MRG auto-commit + `[skip ci]`)                           |
| Lokaal     | `build`                                                         |

Productie (main → root): de reusable workflow kopieert eerst sibling-deploys
van `gh-pages` (bijv. `/preview/`, `/{branch}/`) die niet in de nieuwe
site-build zitten, en deployt daarna met `keep_files=false` (schone root,
geen wezen zoals oude `terminologie/index.html`). Subdirectory-deploys
vervangen alleen hun `destination_dir` (`keep_files` naar keuze).

### `vsa-ci.yml` — VSA CI

| Veld       | Waarde                                                              |
| ---------- | ------------------------------------------------------------------- |
| Trigger    | `push`, `pull_request`                                              |
| Runner     | `windows-latest`                                                    |
| Doel       | Checkout `bron` + `scripts\ci.cmd` (pytest, consumer-minimal)       |
| Publiceert | Nee                                                                 |
| Lokaal     | `scripts\ci.cmd` (vereist sibling `..\bron` of `vendor\bron`)       |

### `docs-build.yml` — Docs build (MkDocs smoke)

| Veld       | Waarde                                       |
| ---------- | -------------------------------------------- |
| Trigger    | `pull_request`, `workflow_dispatch`          |
| Runner     | `ubuntu-latest`                              |
| Doel       | TEv2 + `mkdocs build --strict` (geen deploy) |
| Publiceert | Nee                                          |
| Lokaal     | `build`                |

### `release-artifacts.yml`

pytest + wheel/sdist + build van `examples/consumer-minimal`.

### `pages-deploy-reusable.yml` / `vsa-render-reusable.yml`

Ongewijzigd herbruikbaar voor org-repo's. Zie [reuse-vsa-tooling.md](../../docs/guides/reuse-vsa-tooling.md).

---

## Diagram

```text
push
├── vsa-ci.yml          → pytest + consumer-minimal (Windows)
└── docs-pages.yml      → TEv2 + MkDocs → gh-pages:/ of /preview/

pull_request
├── vsa-ci.yml          → pytest + consumer-minimal (Windows)
└── docs-build.yml      → TEv2 + mkdocs --strict (Linux, geen deploy)

handmatig
├── docs-build.yml
└── release-artifacts.yml → wheel/sdist + consumer-minimal artifact
```
