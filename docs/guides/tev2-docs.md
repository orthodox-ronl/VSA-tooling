# TEv2 in tool-docs

VSA-tooling gebruikt TEv2 voor **tool-termen** ([parser](@), [renderer](@), includes, …) in
`docs/terminologie/`. De mensleesbare glossary staat in `docs/glossary.md` (zelfde
patroon als bron: één bronbestand met `{% hrg="vsa-tooling" %}`, geen
`_index.template`/rename). Org-termen uit
[bron](https://orthodox-ronl.github.io/bron/specs/terminologie/) worden via
`termselection: "*@bron"` in de lokale MRG/HRG opgenomen (D1: bron blijft
canoniek). Lokale curated texts kunnen een term herdefiniëren; dan wint die voor
`[term](@)`, terwijl `[term](@bron)` de org-definitie blijft.

**Contributor-note (term bodies):** volg het org
[term-entry-sjabloon](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/term-entry-sjabloon.md)
waar zinvol (voorbeeld, waartoe, verder lezen). Voor org-begrippen in
eindgebruikersprose: voorkeur `[term](@bron)` tenzij je bewust de lokale
herdefinitie bedoelt.

Org-brede contributor-checklist (scripts, pins, tabellen):
[Documentatie bijdragen](https://orthodox-ronl.github.io/bron/manuals/docs-bijdragen/)
(bron).

## Lokaal

Installeer TEv2-tools via de repo-pins (voorkeur):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
npm install
```

Of globaal (zelfde versies als in `package.json`, nu **1.2.0**):

```cmd
npm install -g @tno-terminology-design/trrt @tno-terminology-design/hrgt @tno-terminology-design/mrgt @tno-terminology-design/mrg-import
```

| Script                        | Doel                                                                 |
| ----------------------------- | -------------------------------------------------------------------- |
| `serve`                       | Snelle preview **zonder** TermRef-hover                              |
| `serve-tev2`                  | Preview **met** TEv2 (staging `generated/`, zoals CI)                |
| `build --no-tev2`             | Documentatie bouwen zonder de term-pipeline                          |
| `build`                       | Volledige keten + TermRef-check + MkDocs (= CI-parity)               |

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
serve-tev2
```

`mrg-import` haalt de bron-MRG op (nodig voor `*@bron` in `docs/saf.yaml`).
Lokaal gebruikt `prepare-tev2-docs.py` indien aanwezig de sibling-checkout
`..\bron\docs` (werkt om een Windows-bug in mrg-import met GitHub-URLs heen);
CI blijft de GitHub-`scopedir` gebruiken.

Alleen TEv2+MkDocs zonder serve: `npm run tev2:docs` (= `docs-build-tev2.cmd`).

Na TermRef- of glossary-wijzigingen: **opnieuw** `docs-serve-tev2` / `docs-build-tev2`
(live reload op `docs/` zonder preprocess toont geen hover).

## CI

`docs-pages.yml` (elke push) en `docs-build.yml` (PR / handmatig) draaien de volle
keten inclusief `mrg-import` en `python scripts/check-tev2-termrefs.py generated/docs`
vóór `mkdocs build --strict`. Op push alleen `docs-pages.yml`, zodat TEv2+MkDocs niet
dubbel draait. Pages committeert gegenereerde `docs/mrgs/mrg.vsa-tooling*.yaml`
met `[skip ci]` (geen CI-cascade).

## Versie-pins

| Onderdeel        | Pin / range     | Bestand                 |
| ---------------- | --------------- | ----------------------- |
| MkDocs Material  | `>=9.5,<10`     | `requirements-docs.txt` |
| TEv2 npm-tools   | `1.2.0`         | `package.json`          |

Afstemmen met bron tenzij een bewuste drift-PR.

## TermRefs schrijven

- Tool-termen: `[parser](@)`, `[validator](@)`, …
- Geïmporteerde org-termen zonder lokale herdefinitie: `[exporttype](@)` (of
  `[exporttype](@bron)` — zelfde entry via bron-scope).
- Termen die **lokaal hergedefinieerd** zijn (`zangstuk`, `vsa`, …):
  - `[zangstuk](@)` → definitie in deze repo
  - `[zangstuk](@bron)` → definitie in scope `bron`

Beide vormen blijven bruikbaar. In lokale curated texts voor gedeelde termen
verwijzen we naar `@bron` met een TermRef, zonder de bron-definitie te kopiëren.
Lokale `vsa.md` houdt alleen form phrases `vsa` / `vsa's`, zodat
`[vsa-notatie](@)` en `[vsa-tooling](@)` uniek naar de bron-entries resolven.

Voorbeeld: [exporttype](@) is een geïmporteerde org-term; [zangstuk](@) is de
lokale herdefinitie, terwijl [zangstuk](@bron) naar scope `bron` wijst.

**Geen TermRefs in headings** (`#` … `######`): TRRT maakt HTML-links met
`title="…"`, en MkDocs’ inhoudsopgave toont dan kapotte TOC-labels. Gebruik in
koppen platte showtext; TermRefs horen in de lopende tekst.

Opgeloste TermRefs krijgen class `og-termref` (zie `tev2-config.yaml` +
`stylesheets/extra.css`).

## Markdown-tabellen

Na bulk-wijzigingen:

```cmd
python scripts\align_markdown_tables.py docs/
```

## Hugo / presentatie

TEv2 in de demosite hoort bij [VSA-demo](https://github.com/orthodox-ronl/VSA-demo)
(daar desgewenst deferred). Deze handleiding gaat alleen over **MkDocs tool-docs**.
