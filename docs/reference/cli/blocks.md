# `vsa blocks` — VSA-blokken in Markdown vinden

Vind [VSA-blokken](@) in een Markdownbestand en toon optioneel hun [metadata](@),
body en [AST](@).

## Synopsis

```text
vsa blocks [-h] [--json] path
```

## Beschrijving

`vsa blocks` leest één Markdownbestand en zoekt naar [VSA-blokken](@). Dit
commando parset de gevonden blokken niet semantisch — het telt en (met `--json`)
inspecteert ze.

Gebruik dit om te controleren of blokken herkend worden, of om [metadata](@)/body/[AST](@)
te bekijken tijdens het debuggen. Voor normaal dagelijks gebruik heb je
`--json` meestal niet nodig.

## Argumenten en opties

| Naam             | Verplicht | Betekenis                                                        | Default           | Beperkingen   |
| ---------------- | --------- | ---------------------------------------------------------------- | ----------------- | ------------- |
| `path`           | Ja        | Markdownbestand om te doorzoeken.                                | —                 | Moet bestaan. |
| `--json`         | Nee       | Toon [metadata](@), body en [AST](@) per gevonden blok als JSON. | Uit (telt alleen) | —             |
| `-h`, `--help`   | Nee       | Toon hulp voor dit subcommando.                                  | —                 | —             |

## Output

- **stdout zonder `--json`**: één regel, `<n> VSA-blok(ken) gevonden`.
- **stdout met `--json`**: een JSON-lijst; per blok een object met de velden
  in de tabel hieronder.
- Er worden geen bestanden geschreven.

| JSON-veld      | Betekenis                                                                   |
| -------------- | --------------------------------------------------------------------------- |
| `start_line`   | Beginregel van het blok in het Markdownbestand.                             |
| `end_line`     | Eindregel van het blok in het Markdownbestand.                              |
| `metadata`     | Effectieve blokinstellingen (`do`, `mode`, `tempo`, …, inclusief defaults). |
| `body`         | De rauwe VSA-inhoud van het blok.                                           |
| `ast`          | Interne parserstructuur van de body.                                        |

## Exit status

| Exitcode | Betekenis                                                           |
| -------- | ------------------------------------------------------------------- |
| `0`      | Commando succesvol uitgevoerd (ook als er 0 blokken gevonden zijn). |
| `1`      | Onverwachte fout (bijv. bestand niet leesbaar).                     |

## Voorbeelden — succes

```cmd
vsa blocks examples\minimal\031_markdown_block_metadata.md
```

Verwachte output:

```text
1 VSA-blok(ken) gevonden
```

Met `--json`:

```cmd
vsa blocks examples\minimal\031_markdown_block_metadata.md --json
```

Verwachte output (verkort):

```json
[
  {
    "start_line": 3,
    "end_line": 9,
    "metadata": {
      "do": "C4",
      "mode": "major",
      "tempo": "120",
      "musicxml-profile": "playback"
    },
    "body": "[:] {/Hei_}{/lig_} is de Heer. [:]",
    "ast": {
      "type": "Document",
      "nodes": [
        { "type": "PitchMarkerNode", "height_modifier": [] }
      ]
    }
  }
]
```

Geen bestanden worden geschreven; de output verschijnt alleen op het scherm.

## Voorbeelden — falen

```cmd
vsa blocks pad\dat\niet\bestaat.md
```

Verwachte output (stderr):

```text
[Errno 2] No such file or directory: 'pad\\dat\\niet\\bestaat.md'
```

Exitcode: `1`.

Fix: controleer het pad, bijvoorbeeld met `dir`.

## Wanneer gebruik je `--json`?

| Situatie                                   | Gebruik            |
| ------------------------------------------ | ------------------ |
| Controleren of blokken herkend worden      | Zonder `--json`    |
| Metadata/body/[AST](@) bekijken (debuggen) | Met `--json`       |

## Zie ook

- [`vsa parse`](parse.md) — [AST](@) van een los `.vsa`-bestand (buiten Markdown).
- [`vsa process`](process.md) — SVG's genereren uit dezelfde [VSA-blokken](@).
- Outputreferentie (JSON-velden): [outputs.md](../outputs.md)
- Blokmetadata: [metadata.md](../metadata.md)
