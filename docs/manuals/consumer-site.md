# Consumer-site — waar hoort wat

!!! note "Voor wie / wanneer"
    **Voor:** consumer-site builder die wil weten wat in welke repo hoort.
    **Wanneer:** je hangt Hugo + `vsa-tool` aan elkaar.
    **Niet:** een volledige Hugo-cursus — die hoort bij
    [VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

**Antwoord in het kort:** tooling = package/CLI (validate, conversies,
layoutprofielen); presentatievoorbeeld = VSA-demo; bibliotheek/productbeleid
= consumer-repo’s; [zangstukken](@bron)/org-specs = [bron-repository](@bron).

Ownership (wat hoort waar, bibliotheek-id, layoutprofielen):
[Integratie — reuse](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

## Waar hoort wat

| Repo                                                           | Rol                                          |
| -------------------------------------------------------------- | -------------------------------------------- |
| **[VSA-tooling](@bron)** (deze docs)                           | Package, CLI, specs, [fixtures](@)           |
| **[VSA-demo](https://github.com/orthodox-ronl/VSA-demo)**      | Voorbeeld-Hugo-site + Pages                  |
| **[bron](https://github.com/orthodox-ronl/bron)**              | [Zangstukken](@bron) en org-specs            |

## Minimale keten (tooling)

```text
content-source/*.md  (+ .vsa)
        ↓
  vsa validate
        ↓
  vsa build-markdown  →  content/ + static/vsa/
        ↓
  hugo  →  public/
```

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\consumer-minimal\content-source
vsa build-markdown examples\consumer-minimal\content-source generated\ci\content generated\ci\static\vsa
```

Voor een rijkere Markdown + Coria-oefenlink (lokale kopie tropaar toon 3):

```cmd
vsa build-markdown examples\docs-walkthroughs\coria-oefenlink generated\docs-walkthrough-coria\content generated\docs-walkthrough-coria\static\vsa
```

Zie [MusicXML-export — Coria-walkthrough](../guides/musicxml-export.md#walkthrough-lokale-fixture).

## Lokaal (voorbeeldconsumer)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-demo
test
scripts\serve-hugo.cmd
```

Documentatie: [VSA-demo README](https://github.com/orthodox-ronl/VSA-demo/blob/main/README.md).

## Zie ook

- Installatie en CI: [Integratie — reuse](../guides/reuse-vsa-tooling.md)
- CLI: [CLI-taken](../guides/cli-taken.md), [CLI-referentie](../reference/cli/index.md)
- Navigatie-placeholders: [hugo-navigation-placeholders](../guides/hugo-navigation-placeholders.md)
