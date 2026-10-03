# Directives en document-samenstelling

Dit document consolideert de specificaties voor [control tokens](@), [renderer directives](@), comments, includes en samengestelde VSA-documenten.

Deze onderdelen zijn syntactische of structurele uitbreidingen rond de VSA-kernnotatie.


---

## Bron: `docs/spec-control-tokens.md`

# Spec addendum – Control Tokens / Renderer Directives

## Doel

Maak onderscheid tussen:

1. gewone tekst
2. [hoogte-markeringen](@)
3. [renderer-directives](@)

## Hoogte-markering

```text
[<EHM>:]
```

Voorbeelden:

```text
[:]
[/:]
[//:]
[\:]
```

Deze hebben uitsluitend betrekking op toonhoogte en worden op het blad getoond.

## Toonhoogte-overgang

```text
[<oude-EHM>:<nieuwe-EHM>]
```

Voorbeelden: `[//:/]`, `[/://]`, `[:/]`. Dit is geen [hoogte-markering](@):
de body eindigt niet op `:` vlak vóór `]`, en het token wordt niet gerenderd.
Zie [syntax](syntax.md) en [semantics](semantics.md).

## Control tokens

```text
[/]
[*]
[/?]
[*?]
```

Deze zijn geen [hoogte-markeringen](@).

## Semantiek

Control tokens vertegenwoordigen een abstracte intentie.

| Token | Abstracte betekenis      |
| ----- | ------------------------ |
| [*]   | phrase_rest              |
| [/]   | phrase_boundary          |
| [*?]  | optional_phrase_rest     |
| [/?]  | optional_phrase_boundary |

## Renderer-afhankelijk gedrag

### SVG

Mogelijke interpretaties:

- zichtbaar teken
- regelafbreking
- zachte regelafbreking
- negeren

volledig configureerbaar.

### MusicXML

Mogelijke interpretaties:

- breath mark
- barline
- system break
- negeren

volledig configureerbaar.

## EBNF

```ebnf
bracket-token ::=
      height-marker
    | pitch-transition
    | control-token ;

height-marker ::= "[" [ EHM ] ":]" ;

pitch-transition ::= "[" [ EHM ] ":" EHM "]" ;

control-token ::=
      "[/]"
    | "[*]"
    | "[/?]"
    | "[*?]" ;
```

## Ontwerpregel

Control tokens krijgen geen universele betekenis.

Renderers bepalen zelf hoe de abstracte betekenis wordt uitgewerkt.

---

## Bron: `docs/spec/include-vsa.md`

# `@include-vsa` — VSA inline includes

Status: **geïmplementeerd** (`id=` / `lokaal=` / **`zoek=`**).

Normatief zoek-contract (bron): [catalogus-zoek-api.md](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/catalogus-zoek-api.md).

---

## Syntax

In [VSA-notatie](@bron) (één regel):

```vsa
refrein: @include-vsa zoek="Troparion"
refrein: @include-vsa id=troparion-geboorte-moeder-gods/troparion-geboorte-moeder-gods/liturgikon
refrein: @include-vsa lokaal=cherubijnenhymne/kastorski/groningen/groningen-vsa
```

Parameters **`zoek=`**, **`id=`**, **`lokaal=`** — wederzijds exclusief; geen pad.

Alleen de substring `@include-vsa …` wordt vervangen; `refrein: ` blijft staan.

---

## Resolve

| Parameter | Bron                                                           |
| --------- | -------------------------------------------------------------- |
| `id=`     | `catalogus` — beide herkomsten; lokaal wint bij conflict       |
| `lokaal=` | `catalogus` — parochie `lokaal/`                               |
| `zoek=`   | `catalogus.zoek` (+ `ZoekContext` uit ouder-`.vsa` `default:`) |

Expand: lees doel-`.vsa`, strip frontmatter, splice body **in-memory** (brondocument ongewijzigd).

| Uitkomst catalogus                 | `@include-vsa` / [`vsa validate`](../reference/cli/validate.md) |
| ---------------------------------- | --------------------------------------------------------------- |
| Geen match                         | **Fout**                                                        |
| Meerdere matches                   | **Fout** (`AmbiguousError`)                                     |
| Eén match + `ook_gevonden_in_bron` | **Waarschuwing** (build mag doorgaan)                           |

Bij ambiguïteit:

1. [`catalogus zoek --lijst`](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/#catalogus-zoek) met dezelfde context.
2. Verfijn `zoek=` of `default.*` in ouder-`.vsa`.
3. Of schakel over naar **`@include-vsa lokaal=…`** / **`id=…`** na review.

---

## Context (`default.*`)

`default.*` in **dezelfde** frontmatter als `@include-vsa`. Conventie:

- **`zoek=`** in sjablonen/sessies: liturgische rol in de zoekstring; feest in `default.gelegenheid`.
- **`@include-vsa zoek=`** in `.vsa`: context uit **ouder**-`.vsa` frontmatter.

Zie [catalogus-zoek-api — twee contextlagen](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/catalogus-zoek-api.md).

---

## Implementatiestatus

| Onderdeel                                                                                                                      | Status              |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| `expand_include_vsa` in [`include_vsa.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/include_vsa.py)      | **Geïmplementeerd** |
| `@include-vsa id=` / `lokaal=`                                                                                                 | **Geïmplementeerd** |
| `@include-vsa zoek=`                                                                                                           | **Geïmplementeerd** |
| Integratie validate / svg / musicxml / build-markdown                                                                          | **Geïmplementeerd** |

---

## Bron: `docs/spec/vsa-comments.md`

# VSA-commentaar

Binnen een `::: vsa-notatie` blok mag HTML-commentaar voorkomen:

```text
<!-- dit is commentaar -->
```

## Regels

- De oorspronkelijke brontekst blijft ongewijzigd.
- Commentaar blijft behouden in de bron.
- Commentaar is uitsluitend bedoeld voor de broncode.
- Commentaar heeft geen invloed op parsing.
- Commentaar heeft geen invloed op validatie.
- Commentaar heeft geen invloed op rendering.
- Commentaar heeft geen invloed op [afgeleide](@bron) artefacten.
- Commentaar mag niet als tekstnode worden behandeld.
- Commentaar mag niet als whitespace worden behandeld.
- Commentaar mag niet als newline worden behandeld.
- Commentaar mag geen invloed hebben op positionering, spacing of layout.
- Commentaar mag niet in SVG, HTML, JSON, MusicXML of andere [afgeleide](@bron) artefacten terechtkomen.

---

## Bron: `docs/spec-vsa-document-samenstellen.md`

# VSA Document Samenstellen — specificatie

## Doel

Een auteur schrijft bronbestanden in Markdown met VSA-uitbreidingen.
Uit die bronbestanden wordt gegenereerd:

- **een HTML-pagina** die normaal in een browser werkt
- **hetzelfde HTML-bestand**, maar met A4-opmaak actief bij afdrukken (`@media print`)

Er is geen aparte print-pipeline; één HTML-bestand dient beide doelen.

---

## Invoerformaat

Basis: Markdown met GFM-extensies (tabellen, doorhalen), en uitgebreid met de volgende directives.

### VSA-blok (bestaand)

    ::: vsa-notatie
    [VSA-inhoud]
    :::

Wordt door [`vsa build-markdown`](../reference/cli/build-markdown.md) omgezet naar SVG en ingevoegd als shortcode of `<img>`.

### Paginabreuk

    :::pagebreak:::

- In HTML: `<div class="pagebreak"></div>`
- In browser: onzichtbaar
- Bij afdrukken: CSS zorgt voor een harde A4-paginabreuk

### Transclusion (include)

    :::include pad/naar/bestand.ext:::

    :::include <exporttype> "pad/naar/bron" [parameters]:::

Exporttypes: `svg` (alleen `.vsa`); `coria` en `mxl` (`.vsa`, of native `.mxl` /
`.musicxml`). `:::coria` blijft een synoniem voor `:::include coria`. Zie
[exportcontracten](https://orthodox-ronl.github.io/bron/reference/exportcontracten/)
([exporttypen](@bron)).
Plain `:::include bestand.mxl:::` (zonder exporttype) is niet toegestaan.

Het pad is **relatief aan het includerende bestand** (niet aan de projectroot), **of**
een logische referentie via **catalogus** (fase 3):

    :::include svg id:zangstuk-id/variant-id/uitvoeringsvorm-id [parameters]:::
    :::include svg lokaal:…:::
    :::include svg bron:zangstuk-id/source-id:::
    :::include svg zoek="Troparion" [parameters]:::

**Fase 4 — catalogus-zoek:** `zoek="…"` in sjablonen/sessies; [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md)
vervangt vóór build door `bron:…` / `lokaal:…`. Open `zoek=` in build → **fout**.
Zie [catalogus-samenstelling-zangstuk](https://orthodox-ronl.github.io/bron/specs/catalogus-samenstelling-zangstuk/)
en [parochie-lokaal-vsa.md](../guides/parochie-lokaal-vsa.md).

Segmenten mogen [aliassen](@bron) zijn (`Hemelum` → `hemelum`). Zie
[catalogus-cli](https://orthodox-ronl.github.io/bron/reference/catalogus-cli/).

Ondersteunde bestandstypen:

| Extensie                                 | Behandeling                                                                   |
| ---------------------------------------- | ----------------------------------------------------------------------------- |
| `.md`, `.markdown`                       | Inhoud wordt als Markdown ingevoegd; eigen includes worden recursief opgelost |
| `.vsa`                                   | Wordt behandeld als een `:::vsa-notatie:::` blok en omgezet naar SVG          |
| `.svg`                                   | Wordt ingevoegd als `<img src="...">`                                         |
| `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` | Wordt ingevoegd als `<img src="...">`                                         |

### Coria-oefenlink

    :::coria "pad/naar/melodie.vsa" [label="…"] [mode="auto|html|mxl"]:::
    :::include coria "pad/naar/score.mxl" [label="…"] [mode="auto|html|mxl"]:::

Pad relatief aan het includerende bestand, zoals bij `:::include`.

- Bron `.vsa`: als `{stem}.coria.html` naast het vsa-bestand staat → Coria-HTML
  (`static/coria/…`). Anders → afgeleide `.mxl` via `play_from_url`
  (`/vsa/mxl/…/{stem}.mxl`).
- Bron `.mxl` / `.musicxml`: het bestand zelf (`/mxl/…` inclusief extensie).
  Optioneel `{stem}.coria.html` naast dat bestand. Build kopieert native
  MusicXML naar `static/mxl/…`.

Wordt bij `build-markdown` omgezet naar Hugo-shortcode `coria-html` of `coria`.

### Conditionele inhoud

    :::web-only:::
    [inhoud die alleen op de website verschijnt]
    :::end-web-only:::

    :::print-only:::
    [inhoud die alleen bij afdrukken verschijnt]
    :::end-print-only:::

- `web-only` — verborgen bij afdrukken, zichtbaar in browser
- `print-only` — verborgen in browser, zichtbaar bij afdrukken

### Samen op één pagina

    :::keep-together:::
    [inhoud die bij afdrukken bij elkaar gehouden wordt]
    :::end-keep-together:::

    :::keep-together scale="70%":::
    [inhoud met verkleinde SVGs]
    :::end-keep-together:::

- In browser: geen zichtbaar effect
- Bij afdrukken: CSS voorkomt een paginabreuk binnen het blok
  (`break-inside: avoid`)
- Als de inhoud groter is dan één pagina, verplaatst de browser het hele blok
  naar de volgende pagina; past het dan nog steeds niet, dan wordt de
  `avoid`-instructie genegeerd
- De optionele parameter `scale="<waarde>"` schaalt alle [VSA-notaties](@bron) binnen
  het blok naar de opgegeven breedte (bijv. `"70%"`); de hoogte schaalt
  proportioneel mee omdat de SVGs een `viewBox` hebben. Gebruik dit wanneer
  twee of meer SVGs samen op één pagina moeten passen.

Blok-directives worden Hugo-shortcodes (`{{< web-only >}}`, enz.). De
shortcode-templates renderen de innerlijke markdown via `Page.RenderString`
(zonder extra lege regels in de bron). Witruimte in content-source is daarmee
**niet** van invloed op de afdruk-layout; alleen expliciete HTML/CSS (zoals
`scale` op `keep-together`) beïnvloedt paginering.

---

## Sluitingstags

Elk blok-directive eindigt met een **directief-specifieke sluitingstag**:

| Opening               | Sluiting                  |
| --------------------- | ------------------------- |
| `:::web-only:::`      | `:::end-web-only:::`      |
| `:::print-only:::`    | `:::end-print-only:::`    |
| `:::keep-together:::` | `:::end-keep-together:::` |

Een verkeerde of ontbrekende sluitingstag geeft een foutmelding met de naam
van het openingsblok.

Nesting (een blok-directive binnen een ander blok-directive) is niet
toegestaan en levert een foutmelding op.

---

## Recursieve transclusion

Een included bestand mag zelf ook includes bevatten.
De verwerker lost dit van buiten naar binnen op.

**Regels:**

- Kringverwijzingen (A → B → A) worden gedetecteerd via een include-stack
  en afgebroken met een foutmelding die de kring toont
- Hetzelfde bestand mag meerdere keren worden included (geen kring);
  elk gebruik levert een zelfstandige kopie van de inhoud op
- Een `:::pagebreak:::` in een included bestand werkt identiek
  aan een paginabreuk in het hoofdbestand
- Blok-directives (`web-only`, `print-only`, `keep-together`) in included
  bestanden werken identiek aan die in het hoofdbestand
- [VSA-blokken](@) in included bestanden worden verwerkt als onderdeel
  van het uiteindelijke document; elk blok krijgt een unieke SVG-bestandsnaam

**Voorbeeld:**

````
boek.md :::include hoofdstuk-1.md::: :::include hoofdstuk-2.md:::

hoofdstuk-1.md (in submap hoofdstuk-1/) :::pagebreak::: :::include "melodie.vsa"::: :::include noot.md:::
````

Verwerking: `boek.md` → `hoofdstuk-1.md` → `melodie.vsa` + `noot.md`
                        → `hoofdstuk-2.md`

---

## Uitvoer

De verwerking loopt via de bestaande [`vsa build-markdown`](../reference/cli/build-markdown.md)-stap, uitgebreid met:

1. **Include-resolutie** — recursief, vóór alle andere verwerking
2. **Paginabreuk-omzetting** — `:::pagebreak:::` → HTML-markering
3. **Blok-directives** — omgezet naar Hugo shortcodes
4. **VSA-rendering** — ongewijzigd; [VSA-blokken](@) (ook uit included `.vsa`-bestanden)
   worden omgezet naar SVG

Hugo verwerkt daarna het gegenereerde Markdown-bestand tot HTML.

---

## CSS voor afdrukken

```css
@media print {
    @page {
        size: A4;
        margin: 2cm;
    }

    /* Paginabreuk */
    .pagebreak {
        page-break-before: always;
    }

    /* Website-chrome verbergen */
    .site-header,
    .site-nav,
    .nav-buttons,
    footer {
        display: none;
    }

    /* Conditionele inhoud */
    .web-only { display: none; }

    /* Samen op één pagina */
    .keep-together {
        break-inside: avoid;
        page-break-inside: avoid;
    }

    /* Schaling van SVGs binnen keep-together (via scale-parameter) */
    .keep-together .vsa-notation {
        width: var(--vsa-scale, auto);
    }
}

/* print-only standaard verborgen in browser */
.print-only { display: none; }

@media print {
    .print-only { display: block; }
}
```

---

## Exporttypen (normatief contract)

Authoring-syntax voor **export** (niet conversie) is contractueel vastgelegd in de
**[bron-repository](@bron)**:

- [Exportcontracten](https://orthodox-ronl.github.io/bron/reference/exportcontracten/)
- Per type: [svg](https://orthodox-ronl.github.io/bron/reference/exporttype-svg/),
  [coria](https://orthodox-ronl.github.io/bron/reference/exporttype-coria/),
  [mxl](https://orthodox-ronl.github.io/bron/reference/exporttype-mxl/)

Conversie ([`vsa svg`](../reference/cli/svg.md), [`vsa musicxml`](../reference/cli/musicxml.md)):
[Conversiemechanismen](https://orthodox-ronl.github.io/bron/reference/conversiemechanismen/)
([conversiemechanisme](@bron)).

### Implementatiestatus (VSA-tooling)

| Syntax                                        | Status                                                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `:::include "melodie.vsa"`                    | Geïmplementeerd (SVG via [VSA-blok](@))                                                                |
| `:::coria "melodie.vsa"`                      | Geïmplementeerd                                                                                        |
| `:::include svg\|coria\|mxl "…"`              | Geïmplementeerd; zie demo `export-demo.md`                                                             |
| `:::include svg id:…` / `lokaal:…` / `bron:…` | Geïmplementeerd (fase 3); zie demo `antifonen-hemelum.md`                                              |
| `:::include <type> zoek="…"`                  | Geïmplementeerd (fase 4); resolve via [`vsa resolve-catalogus`](../reference/cli/resolve-catalogus.md) |
| `coria` / `mxl` op `bron:` catalogus-pad      | Beperkt — `.vsa` buiten content-root                                                                   |

Parameters (`alt`, `scale`, `label`, `mode`) — volledige beschrijving per [exporttype](@bron)
in bron-docs; korte samenvatting blijft in sectie 3 en 3b hierboven.
