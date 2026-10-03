# Directives en bracket-dispatch

Bracket-directives zijn tokens tussen `[` en `]`. Zij moeten vroeg in de parsing worden herkend, zodat wraptokens, hoogte-markers en toekomstige directives niet door elkaar lopen.

## Categorieën

| Categorie             | Voorbeelden                       | Betekenis                                                       |
| --------------------- | --------------------------------- | --------------------------------------------------------------- |
| Hoogtemarkers         | `[:]`, `[/:]`, `[//:]`            | Positionele toon- of hoogte-informatie (zichtbaar op het blad). |
| Toonhoogte-overgang   | `[//:/]`, `[/://]`, `[:/]`        | Stille cursor-sprong; niet renderen.                            |
| Control tokens        | `[*]`, `[/]`                      | Structurele of renderergerichte controle.                       |
| Optionele vorm        | `[*?]`, `[/?]`                    | Voorwaardelijke of tolerante control tokens.                    |
| Toekomstig            | `[token:param]`                   | Uitbreidbare generieke directivevorm.                           |

## Dispatchmodel

```text
bracket-token
  ↓
classificeer token
  ├── hoogte-marker
  ├── toonhoogte-overgang
  ├── control-token
  ├── onbekende directive
  └── syntaxfout
```

## Ontwerpregel

De parser moet eerst bepalen welk type bracket-token is aangetroffen. Pas daarna mag inhoudelijke verwerking plaatsvinden.

Dat voorkomt dat tokens zoals `[/]` of `[*]` per ongeluk als gewone hoogte- of wrapsyntax worden geïnterpreteerd.
