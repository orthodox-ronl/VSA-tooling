# Parochie-lokaal — VSA-tooling

**Algemene handleiding (canoniek):** [bron/docs/manuals/parochie-lokaal-zangstukken.md](https://github.com/orthodox-ronl/bron/blob/main/docs/manuals/parochie-lokaal-zangstukken.md)

Terminologie: [bron/docs/specs/terminologie.md](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/terminologie.md).

Dit document beschrijft alleen wat **specifiek voor [VSA-tooling](@bron)** geldt (CLI,
includes, catalogus). Voor een browsable Hugo-voorbeeld: [VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

---

## Fixture-voorbeeld (CI)

```text
examples/consumer-minimal/content-source/
```

[Parochie-lokale representaties](@bron) / [zangstukken](@bron) in een consumer-site:
zie VSA-demo en
[bron — parochie-lokaal](https://github.com/orthodox-ronl/bron/blob/main/docs/manuals/parochie-lokaal-zangstukken.md).

---

## VSA-includes in samenstellingen

### Opgelost catalogus-pad (fase 3)

**Logische id** — [aliassen](@bron) per segment toegestaan:

```markdown
:::include svg id:antifoon-1-weekdagen/liturgikon-weekdagen/Hemelum alt="1e antifoon (Hemelum)":::
```

Prefix `lokaal:` of `bron:` beperkt de zoekscope; `id:` doorzoekt beide (lokaal heeft voorrang bij conflicten).

**Relatief pad** (backward compatible):

```markdown
:::include svg "../../lokaal/antifoon-1-weekdagen/liturgikon-weekdagen/hemelum/repr/hemelum.vsa" alt="1e antifoon (Hemelum)":::
```

### Verwijderd: `zoek=`

`:::include … zoek="…"` en de opdracht `vsa resolve-catalogus` bestaan niet meer. Een
include met `zoek=` geeft een foutmelding. Verwijs met een catalogus-id (`id:…`),
een `lokaal:`-pad of een relatief bestandspad, zoals hierboven beschreven.

### Exporttypes

| Exporttype   | Status                              | Opmerking                                      |
| ------------ | ----------------------------------- | ---------------------------------------------- |
| `svg`        | **Geïmplementeerd**                 | Notatie inline                                 |
| `coria`      | **Geïmplementeerd**                 | Oefenlink                                      |
| `mxl`        | **Geïmplementeerd**                 | Download MusicXML (vanuit VSA-pad)             |
| `mp3-player` | **Gepland** (artefact: `vsa audio`) | Site-knop/include nog open; CLI maakt ``.mp3`` |

---

## Overige markdown

Inline (kort fragment):

```markdown
::: vsa-notatie
…
:::
```

**Opmerking:** annotaties in `.vsa` als `<!-- … -->` (HTML-comment), niet als `[//:]` — dat laatste is een [hoogte-markering](@).

---

## Build-pipeline (VSA-tooling)

| Stap                                                             | [Parochie-lokaal](@bron)                                                                |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Sync bron                                                        | Niet nodig — bestanden in git                                                           |
| [`vsa validate`](../reference/cli/validate.md)                   | Deelt `content-source` recursief                                                        |
| [`vsa build-markdown`](../reference/cli/build-markdown.md)       | Includes op pad / catalogus-pad                                                         |
| Hugo                                                             | Ongewijzigd; **`samenstellingen/`** en **`sjablonen/`** worden overgeslagen             |


Lokaal controleren (tooling):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\consumer-minimal\content-source
serve
```

Hugo-voorbeeldconsumer: [VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

---

## Consumer-site structuur

Zie [consumer-site.md](../manuals/consumer-site.md) en
[hugo-site-structure.md](hugo-site-structure.md) (doorverwijzing naar VSA-demo).
