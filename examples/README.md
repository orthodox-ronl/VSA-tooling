# VSA-tooling — examples

Fixtures voor tests, regressie en CI-smoke. Geen volledige Hugo-site — die staat in
[VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

| Map                   | Doel                                                              |
| --------------------- | ----------------------------------------------------------------- |
| `minimal/`            | Kleine geldige VSA- en Markdown-voorbeelden                       |
| `regression/`         | Golden files (AST, SVG, MusicXML, validatie)                      |
| `edge-cases/`         | Randgevallen en foutscenario's                                    |
| `expected-fail/`      | Invoer die bewust moet falen bij validate                         |
| `consumer-minimal/`   | CI-smoke: `vsa validate` + `vsa build-markdown`                   |
| `docs-walkthroughs/`  | Fixtures voor docs mini-walkthroughs (SVG, validate, Coria)       |
| `site-demo/`          | Kleine Markdown-fixtures (geen Hugo-build)                        |
| `site-demo-invalid/`  | Ongeldige site-fixtures voor tests                                |
| `mvsa/`               | Experimentele meerstemmige invoer (niet door `vsa` geparsed)      |

Volledige presentatiesite: [VSA-demo](https://github.com/orthodox-ronl/VSA-demo).
