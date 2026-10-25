# `vsa products` — standaardproducten + meta

Genereer de standaard siblings bij een `.vsa`-bron: Coria-playback-`.mxl`,
muziek-`.svg`, en `{stam}.vsa.products-meta.json` voor herkomst/versheid.

Herkomst-sidecar (schema, invariante): [products-meta](../../formats/products-meta.md).
Contract-matrix: [contract-index](../../formats/contract-index.md). Straatplan:
[straat-CLIs](../../plans/straat-clis.md).

## Synopsis

```text
vsa products [-h] [--force] [--dry-run] path
```

## Beschrijving

Voor elke `.vsa` onder `path` (bestand of map, recursief):

| Product                         | Bestand                         |
| ------------------------------- | ------------------------------- |
| Coria-playback-`.mxl`           | `{stam}.vsa.mxl`                |
| Muziek-SVG (native renderer)    | `{stam}.vsa.svg`                |
| Versheid-meta                   | `{stam}.vsa.products-meta.json` |

**MXL-keten** (gelijk aan wat bibliotheek-sync eerder zelf deed):

1. Tijdelijke [syllabify](syllabify.md) (canonieke `.vsa` blijft ongewijzigd).
2. Export in `playback`-profiel.
3. Coria-finalize (sanitize + voortekens; geen DOCTYPE) — zelfde nabewerking
   als bij [`vsa musicxml`](musicxml.md) in playback.

**SVG** komt uit de **ongewijzigde** bron (geen syllabify), via dezelfde
native renderer als [`vsa svg`](svg.md).

Losse product-subs mergen dezelfde sidecar: [`vsa musicxml`](musicxml.md)
(key `mxl`) en [`vsa svg`](svg.md) (key `svg`), bij sibling-output naast
de `.vsa`.

Slaat over als de meta-hash van de bron nog klopt en de productbestanden
er zijn. `--force` regenereert altijd.

## Argumenten en opties

| Naam           | Verplicht | Betekenis                                       | Default | Beperkingen        |
| -------------- | --------- | ----------------------------------------------- | ------- | ------------------ |
| `path`         | Ja        | `.vsa`-bestand of map (recursief).              | —       | Moet bestaan.      |
| `--force`      | Nee       | Regenereer ook als meta zegt dat alles vers is. | Uit     | —                  |
| `--dry-run`    | Nee       | Alleen tonen wat er zou gebeuren.               | Uit     | Geen bestanden.    |
| `-h`, `--help` | Nee       | Toon hulp.                                      | —       | —                  |

## Output

- **stdout**: regels per product (`mxl` / `svg`) en `Meta: …` bij schrijven;
  of `ok (meta): …` / `dry-run: …` wanneer er niets verandert.
- **Bestanden**: siblings naast de bron (zie tabel).
- **stderr**: include-/exportfouten.

## Exit status

| Exitcode | Betekenis                                      |
| -------- | ---------------------------------------------- |
| `0`      | Alle bronnen verwerkt (of dry-run / meta-ok).  |
| `1`      | Geen bronnen, padfout, of exportfout.          |

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa products examples\minimal\valid-demo.vsa
vsa products examples\minimal --dry-run
vsa products examples\minimal\valid-demo.vsa --force
```

## Zie ook

- [`vsa musicxml`](musicxml.md) — losse MusicXML-export (`--syllabify` optioneel)
- [`vsa syllabify`](syllabify.md) — streepjes in de bron zelf schrijven
- [`vsa svg`](svg.md) — alleen SVG
- [`mvsa products`](mvsa.md#mvsa-products) · `mscz products` — andere straten
- [contract-index](../../formats/contract-index.md) · [`.vsa`](../../formats/vsa.md)
