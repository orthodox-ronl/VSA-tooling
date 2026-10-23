# `vsa svg` — .vsa naar muziek-only SVG

!!! note "Waartoe"
    Eén of meer `.vsa`-bestanden als SVG-afbeelding voor het **scherm**
    (alleen notatie, geen titel). Zelfde productrol als
    [`mvsa svg`](mvsa.md#mvsa-svg) → `.mvsa.svg`: sibling
    `<bronnaam>.vsa.svg` naast de bron. Geen Markdown-pipeline — daarvoor
    [`vsa process`](process.md) of [`vsa build-markdown`](build-markdown.md).

## Synopsis

```text
vsa svg [-h] [--config CONFIG] [--max-line-width MAX_LINE_WIDTH]
        [-o OUTPUT] input
```

**Invoer:** `input` mag één `.vsa` **of** een map zijn (recursief). Default
per bron: sibling ``<bronnaam>.vsa.svg`` (zie [derived pad](../../formats/vsa-svg.md)).
`-o` / `--output` alleen bij precies één bronbestand. Zie
[Invoer bestand of map](input-pad.md).

## Beschrijving

`vsa svg` leest `.vsa`, lost `@include-vsa` op indien aanwezig, parset de
[VSA-notatie](@bron) en rendert naar SVG via de native VSA-renderer
(andere visuals dan MuseScore-`mvsa svg`, dezelfde rol: muziek-only op
scherm). Dit commando verwerkt **geen** Markdownblokken — voor Markdown
met [VSA-blokken](@) gebruik je [`vsa process`](process.md) of
[`vsa build-markdown`](build-markdown.md).

`vsa svg` valideert de invoer niet expliciet vooraf; een parsefout leidt tot
een foutmelding en exitcode `1`. Draai bij twijfel eerst
[`vsa validate`](validate.md).

## Argumenten en opties

| Naam                              | Verplicht | Betekenis                                                             | Default                                       | Beperkingen                          |
| --------------------------------- | --------- | --------------------------------------------------------------------- | --------------------------------------------- | ------------------------------------ |
| `input`                           | Ja        | `.vsa`-bestand of map met `.vsa`-bestanden.                           | —                                             | Moet bestaan.                        |
| `-o` / `--output` OUTPUT          | Nee       | Uitvoer-``.svg``.                                                     | Sibling ``<naam>.vsa.svg`` naast elke bron    | Alleen bij precies één bronbestand.  |
| `--config CONFIG`                 | Nee       | Pad naar een alternatief `vsa.toml`.                                  | Auto-detectie van `vsa.toml`                  | —                                    |
| `--max-line-width MAX_LINE_WIDTH` | Nee       | Maximale SVG-regelbreedte voordat wordt afgebroken.                   | `max-line-width` uit `vsa.toml`, anders `800` | Getal (float)                        |
| `-h`, `--help`                    | Nee       | Toon hulp voor dit subcommando.                                       | —                                             | —                                    |

## Output

- **stdout**: `SVG geschreven naar: <pad>` per geschreven bestand.
- **Bestand**: sibling ``.vsa.svg`` of het pad uit `-o`.
- Geen Markdown wordt gelezen of geschreven.

## Exit status

| Exitcode | Betekenis                              |
| -------- | -------------------------------------- |
| `0`      | SVG succesvol geschreven.              |
| `1`      | Pad ontbreekt, lege map, of parsefout. |

## Voorbeelden — succes

Sibling naast de bron (bibliotheek-productnaam):

```cmd
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa
```

Verwachte richting: `….svg-phrase-kort.vsa.svg` naast het `.vsa`.

Expliciet pad:

```cmd
vsa svg examples\minimal\050_svg_demo.vsa -o tmp\demo.svg
```

```text
SVG geschreven naar: tmp\demo.svg
```

Met een aangepaste regelbreedte:

```cmd
vsa svg examples\minimal\100_multiline_demo.vsa -o tmp\demo-smal.svg --max-line-width 400
```

Map → sibling-SVG per `.vsa` in die boom:

```cmd
vsa svg examples\minimal
```

!!! note "Validatie vs. SVG"
    `examples\minimal\050_svg_demo.vsa` faalt op `vsa validate` (semantische
    hoogte-mismatch), maar rendert wel gewoon met `vsa svg` — dit commando
    voert geen semantische controle uit. Draai `vsa validate` eerst als je
    zeker wilt zijn van [geldige VSA-notatie](@).

## Voorbeelden — falen

```cmd
vsa svg pad\dat\niet\bestaat.vsa
```

Verwachte richting (stderr): pad niet gevonden; exitcode `1`.

Fix: controleer het invoerpad, bijvoorbeeld met `dir`.

Parsefout (onafgesloten [scope](@)) — voorbeeldinvoer met `{tekst` zonder `}`:

```cmd
vsa svg kapot.vsa
```

Verwachte richting: foutmelding op stderr, exitcode `1`.

Fix: draai eerst `vsa validate kapot.vsa` voor exacte foutcode en
regel/kolom; herstel de [VSA-notatie](@bron); daarna opnieuw `vsa svg`.

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [vsa-SVG (formaat)](../../formats/vsa-svg.md) — sibling-product naast `.vsa`
- [`mvsa svg`](mvsa.md#mvsa-svg) — zelfde productrol voor `.mvsa` (MuseScore)
- [`vsa validate`](validate.md) — controleer [VSA-notatie](@bron) vóór het renderen.
- [`vsa process`](process.md) — SVG's genereren uit meerdere Markdownbestanden.
- [`vsa build-markdown`](build-markdown.md) — SVG's + Hugo-Markdown in één stap.
- Workflow-uitleg: [svg-export.md](../../guides/svg-export.md)
- Bron-contract (SVG als exporttype): [conversie-vsa-svg](https://orthodox-ronl.github.io/bron/reference/conversie-vsa-svg/), [exporttype-svg](https://orthodox-ronl.github.io/bron/reference/exporttype-svg/)
