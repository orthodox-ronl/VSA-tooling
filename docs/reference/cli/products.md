# `vsa products` — standaardproducten + meta

Genereer de standaard siblings bij een `.vsa`-bron, plus
`{stam}.vsa.products-meta.json` voor herkomst en versheid.

Geen partituur-PDF. Download en print van een pagina gaan via
[`markdown pdf`](markdown.md) (`index.md.pdf`). Een losse partituur-PDF
maak je met [`vsa pdf`](pdf.md), [`mvsa pdf`](mvsa.md#mvsa-pdf) of
[`mscz pdf`](mscz.md), niet met `products`.

Herkomst-sidecar (schema, invariante): [products-meta](../../formats/products-meta.md).
Contract-matrix: [contract-index](../../formats/contract-index.md). Straatplan:
[straat-CLIs](../../plans/straat-clis.md).

## Synopsis

```text
vsa products [-h] [--force] [--dry-run] [--quiet] [--skip-svg] [--musescore PATH] path
```

## Beschrijving

Voor elke `.vsa` onder `path` (bestand of map, recursief):

| Product                         | Bestand                         |
| ------------------------------- | ------------------------------- |
| Coria-playback-`.mxl`           | `{stam}.vsa.mxl`                |
| Score-IR                        | `{stam}.vsa.score-ir.json`      |
| MusicXML uit Score-IR           | `{stam}.vsa.from-ir.musicxml`   |
| Partituur-`.mscz`               | `{stam}.vsa.mscz`               |
| Preview-mp3                     | `{stam}.vsa.mp3`                |
| Gezongen tekst                  | `{stam}.vsa.lyrics.txt`         |
| Muziek-SVG (native renderer)    | `{stam}.vsa.svg`                |
| Versheid-meta                   | `{stam}.vsa.products-meta.json` |

Geen `{stam}.vsa.pdf`. MuseScore is nodig voor `.mscz`, `.mp3` en de
Score-IR-keten. De SVG komt uit de VSA-renderer zelf.

**MXL-keten** (gelijk aan wat bibliotheek-sync eerder zelf deed):

1. Tijdelijke [syllabify](syllabify.md) (canonieke `.vsa` blijft ongewijzigd).
2. Export in `playback`-profiel.
3. Coria-finalize (sanitize + voortekens; geen DOCTYPE) — zelfde nabewerking
   als bij [`vsa mxl`](musicxml.md) in playback.

**SVG** komt uit de **ongewijzigde** bron (geen syllabify), via dezelfde
native renderer als [`vsa svg`](svg.md).

Losse product-subs mergen dezelfde sidecar: [`vsa mxl`](musicxml.md)
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
| `--quiet`      | Nee       | Geen voortgangsregels op stdout.                | Uit     | Fouten op stderr.  |
| `--skip-svg`   | Nee       | Sla native SVG over.                            | Uit     | —                  |
| `--musescore`  | Nee       | Pad naar MuseScore (mscz, mp3, Score-IR).       | auto    | —                  |
| `-h`, `--help` | Nee       | Toon hulp.                                      | —       | —                  |

## Output

- **stdout**: een regel per product en `Meta: …` bij schrijven;
  of `ok (meta): …` / `dry-run: …` wanneer er niets verandert.
  Met `--quiet` blijft stdout leeg (fouten blijven op stderr).
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

- [`vsa mxl`](musicxml.md) — losse MusicXML-export (`--syllabify` optioneel)
- [`vsa syllabify`](syllabify.md) — streepjes in de bron zelf schrijven
- [`vsa svg`](svg.md) — alleen SVG
- [`mvsa products`](mvsa.md#mvsa-products) · `mscz products` — andere straten
- [contract-index](../../formats/contract-index.md) · [`.vsa`](../../formats/vsa.md)
