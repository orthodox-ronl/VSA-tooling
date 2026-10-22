# `vsa svg` — .vsa naar SVG renderen

!!! note "Waartoe"
    Eén of meer `.vsa`-bestanden snel als SVG-afbeelding bekijken (scherm of
    afdruk). Geen Markdown-pipeline — daarvoor [`vsa process`](process.md) of
    [`vsa build-markdown`](build-markdown.md).

## Synopsis

```text
vsa svg [-h] [--config CONFIG] [--max-line-width MAX_LINE_WIDTH] input output
```

**Invoer:** `input` mag één `.vsa` **of** een map zijn (recursief). Bij
meerdere bronnen is `output` een **uitvoermap**; bestandsnamen volgen
``<bronnaam>.svg`` (bijv. ``lied.vsa.svg``). Zie
[Invoer bestand of map](input-pad.md).

## Beschrijving

`vsa svg` leest `.vsa`, lost `@include-vsa` op indien aanwezig, parset de
[VSA-notatie](@bron) en rendert naar SVG. Dit commando verwerkt **geen**
Markdownblokken — voor Markdown met [VSA-blokken](@) gebruik je
[`vsa process`](process.md) of [`vsa build-markdown`](build-markdown.md).

`vsa svg` valideert de invoer niet expliciet vooraf; een parsefout leidt tot
een foutmelding en exitcode `1`. Draai bij twijfel eerst
[`vsa validate`](validate.md).

## Argumenten en opties

| Naam                              | Verplicht | Betekenis                                                             | Default                                       | Beperkingen                     |
| --------------------------------- | --------- | --------------------------------------------------------------------- | --------------------------------------------- | ------------------------------- |
| `input`                           | Ja        | `.vsa`-bestand of map met `.vsa`-bestanden.                           | —                                             | Moet bestaan.                   |
| `output`                          | Ja        | SVG-bestand, of uitvoermap bij meerdere bronnen.                      | —                                             | Bij één bron: map moet bestaan. |
| `--config CONFIG`                 | Nee       | Pad naar een alternatief `vsa.toml`.                                  | Auto-detectie van `vsa.toml`                  | —                               |
| `--max-line-width MAX_LINE_WIDTH` | Nee       | Maximale SVG-regelbreedte voordat wordt afgebroken.                   | `max-line-width` uit `vsa.toml`, anders `800` | Getal (float)                   |
| `-h`, `--help`                    | Nee       | Toon hulp voor dit subcommando.                                       | —                                             | —                               |

## Output

- **stdout**: `SVG geschreven naar: <pad>` per geschreven bestand.
- **Bestand**: `output` (één bron) of bestanden in de uitvoermap (meerdere).
- Geen Markdown wordt gelezen of geschreven.

## Exit status

| Exitcode | Betekenis                              |
| -------- | -------------------------------------- |
| `0`      | SVG succesvol geschreven.              |
| `1`      | Pad ontbreekt, lege map, of parsefout. |

## Voorbeelden — succes

```cmd
vsa svg examples\minimal\050_svg_demo.vsa tmp\demo.svg
```

Verwachte output:

```text
SVG geschreven naar: tmp\demo.svg
```

Het bestand `tmp\demo.svg` wordt aangemaakt (map `tmp\` moet al bestaan).
Bekijk het resultaat direct:

```cmd
start tmp\demo.svg
```

Met een aangepaste regelbreedte:

```cmd
vsa svg examples\minimal\100_multiline_demo.vsa tmp\demo-smal.svg --max-line-width 400
```

```text
SVG geschreven naar: tmp\demo-smal.svg
```

Map → meerdere SVG’s:

```cmd
vsa svg examples\minimal tmp\svg-batch
```

!!! note "Validatie vs. SVG"
    `examples\minimal\050_svg_demo.vsa` faalt op `vsa validate` (semantische
    hoogte-mismatch), maar rendert wel gewoon met `vsa svg` — dit commando
    voert geen semantische controle uit. Draai `vsa validate` eerst als je
    zeker wilt zijn van [geldige VSA-notatie](@).

## Voorbeelden — falen

```cmd
vsa svg pad\dat\niet\bestaat.vsa tmp\demo.svg
```

Verwachte richting (stderr): pad niet gevonden; exitcode `1`.

Fix: controleer het invoerpad, bijvoorbeeld met `dir`.

Parsefout (onafgesloten [scope](@)) — voorbeeldinvoer met `{tekst` zonder `}`:

```cmd
vsa svg kapot.vsa tmp\out.svg
```

Verwachte richting: foutmelding op stderr, exitcode `1`.

Fix: draai eerst `vsa validate kapot.vsa` voor exacte foutcode en
regel/kolom; herstel de [VSA-notatie](@bron); daarna opnieuw `vsa svg`.

## Zie ook

- [Invoer bestand of map](input-pad.md)
- [`vsa validate`](validate.md) — controleer [VSA-notatie](@bron) vóór het renderen.
- [`vsa process`](process.md) — SVG's genereren uit meerdere Markdownbestanden.
- [`vsa build-markdown`](build-markdown.md) — SVG's + Hugo-Markdown in één stap.
- Workflow-uitleg: [svg-export.md](../../guides/svg-export.md)
- Bron-contract (SVG als exporttype): [conversie-vsa-svg](https://orthodox-ronl.github.io/bron/reference/conversie-vsa-svg/), [exporttype-svg](https://orthodox-ronl.github.io/bron/reference/exporttype-svg/)
