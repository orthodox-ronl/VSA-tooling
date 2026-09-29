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

### `:::include` met `zoek=` (catalogus)

Status: **geïmplementeerd** — resolve-stap vóór build (of auto-resolve in `build-markdown`
voor publishbare paden).

Normatief contract (bron): [catalogus-samenstelling-zangstuk.md](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/catalogus-samenstelling-zangstuk.md).

Handleiding Rene: [sjabloon schrijven](https://github.com/orthodox-ronl/bron/blob/main/docs/manuals/catalogus/sjabloon-schrijven.md).

#### Bedoeld gedrag

1. Sjabloon of sessie-markdown bevat `:::include <exporttype> zoek="Troparion" …` —
   nog **geen** pad.
2. Frontmatter **`default.*`** levert context (`gelegenheid` in de **sessie**,
   `gelegenheidstype` in het sjabloon).
3. [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md) roept [`catalogus zoek`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek) aan per unieke
   `zoek=`-waarde (+ [exporttypen](@bron) blijven aparte regels).
4. Uitvoer: dezelfde regels met **`bron:…`** / **`lokaal:…`** i.p.v. `zoek=`.
5. Pas daarna [`vsa build-markdown`](../reference/cli/build-markdown.md) / Hugo.

**Harde regel:** open `zoek=` in een bestand dat door build-markdown gaat → **fout**.

#### Voorbeeld (invoer — sessie, mixed session)

```markdown
---
default:
  gelegenheid: geboorte-moeder-gods
  gelegenheidstype: vast-feest
---

### Kondakion

:::include svg zoek="Kondakion" alt="Kondakion":::
:::include coria zoek="Kondakion" label="Oefenen" mode="auto":::
```

Geen `default.uitvoeringsvorm` — feest-stukken uit bron (`liturgikon`); lokaal-stukken
(zoals Cherubijnenhymne) via disambiguation in `zoek=` of aparte sessie-defaults.

#### Voorbeeld (uitvoer na resolve)

```markdown
:::include svg bron:kondak-geboorte-moeder-gods/kondak-geboorte-moeder-gods/liturgikon alt="Kondakion":::
```

**Coria op `bron:`** — catalogus-pad klopt, maar build faalt zolang `.vsa` buiten
`--content-root` ligt. **SVG** op `bron:` werkt; **coria** op `lokaal:` werkt.

#### Exporttypes

| Exporttype   | Status                              | Opmerking                                      |
| ------------ | ----------------------------------- | ---------------------------------------------- |
| `svg`        | **Geïmplementeerd**                 | Notatie inline                                 |
| `coria`      | **Geïmplementeerd**                 | Oefenlink                                      |
| `mxl`        | **Geïmplementeerd**                 | Download MusicXML (vanuit VSA-pad)             |
| `mp3-player` | **Gepland** (artefact: `vsa audio`) | Site-knop/include nog open; CLI maakt ``.mp3`` |

Meerdere regels met **dezelfde** `zoek=` → één catalogus-zoekactie, meerdere includes.

#### Implementatie

- [Parser](@): `markdown_include.py` — weigert open `zoek=` in build.
- Resolve: [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md) (CLI).
- Afhankelijkheid: **`catalogus`** uit bron-repo ([`catalogus zoek`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek)).

---

## [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md)

Status: **geïmplementeerd**.

Doel: markdown met **`zoek=`** omzetten naar markdown met **catalogus-pad** —
tussenstap vóór [`vsa validate`](../reference/cli/validate.md) /
[`vsa build-markdown`](../reference/cli/build-markdown.md) op sjablonen en sessies
(tenzij `build-markdown` auto-resolve voor publishbare bestanden).

### Syntax

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa resolve-catalogus pad\naar\samenstelling.md ^
  --content-root pad\naar\content-source ^
  --bron-root ..\bron
```

| Flag             | Betekenis                                                                                                                                                                  |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<pad.md>`       | Invoer (sessie of sjabloon met `zoek=`)                                                                                                                                    |
| `--content-root` | Parochie content-source (met `lokaal/`)                                                                                                                                    |
| `--bron-root`    | [Bron-repository](@bron) (`zangstukken/`)                                                                                                                                  |
| `--output`       | Optioneel ander uitvoerbestand; default: overschrijven invoer of `.resolved.md`                                                                                            |
| `--dry-run`      | Alleen rapport, geen schrijven                                                                                                                                             |
| `--interactive`  | Review bij ambiguïteit (**gepland**; nu: `AmbiguousError` + [`catalogus zoek --lijst`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek))      |

### Wat het commando doet

1. Yaml-frontmatter parsen → **`default.*`**.
2. Alle `:::include … zoek="…"` regels vinden (niet in code fences).
3. Per `zoek=` + context: [`catalogus zoek`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek) (bron-package).
4. Bij unieke match: vervang `zoek="…"` door `bron:…` / `lokaal:…`.
5. Bij ambiguïteit: **`AmbiguousError`** (strict); review via [`catalogus zoek --lijst`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek).
6. Schrijf opgelost bestand.

### Relatie tot `catalogus` CLI

| Tool                                                                                                                                        | Rol                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [`catalogus zoek`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek) `"Kondakion" --default-gelegenheid …`      | Lage API — één zoekactie                                                                                                                       |
| [`catalogus index validate`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-index-validate)                        | Index controleren vóór bulk-resolve                                                                                                            |
| [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md)                                                                            | Markdown-processor voor Rene — roept [`catalogus zoek`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek) aan      |

Zie [bron — catalogus CLI](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/).

### Pipeline

```text
sjabloon.md (zoek=, geen gelegenheid)
    → sessie.md (+ default.gelegenheid)
    → vsa resolve-catalogus
    → sessie-opgelost.md (bron:/lokaal:)
    → vsa validate
    → (kopie naar publishbare map — demo slaat samenstellingen/ over)
    → vsa build-markdown
    → Hugo
```

GUI (gepland): dezelfde stappen — resolve vóór preview/export.

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
| [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md) | **Geïmplementeerd** — verplicht als `zoek=` aanwezig (of auto in build)                 |
| [`vsa validate`](../reference/cli/validate.md)                   | Deelt `content-source` recursief                                                        |
| [`vsa build-markdown`](../reference/cli/build-markdown.md)       | Includes op pad / catalogus-pad — **geen** open `zoek=`                                 |
| Hugo                                                             | Ongewijzigd; **`samenstellingen/`** en **`sjablonen/`** worden overgeslagen             |


Lokaal controleren (tooling):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\consumer-minimal\content-source
scripts\docs-serve.cmd
```

Hugo-voorbeeldconsumer: [VSA-demo](https://github.com/orthodox-ronl/VSA-demo).

---

## Consumer-site structuur

Zie [consumer-site.md](../manuals/consumer-site.md) en
[hugo-site-structure.md](hugo-site-structure.md) (doorverwijzing naar VSA-demo).
