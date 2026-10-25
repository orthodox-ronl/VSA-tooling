# Products-meta (herkomst-sidecar)

**Contract-id:** products-meta · schema **2**.  
Canonieke hub voor versheid/herkomst van street-`products`. Elders alleen
linken. Overzicht: [contract-index](contract-index.md).

## Waartoe

De CLI die een afgeleid bestand schrijft, is de enige die betrouwbaar weet
**uit welke bron** dat bestand kwam. Die CLI schrijft daarom een
**stempelbestand** (sidecar) naast de bron. Daarin staan:

- de bron (bestandsnaam + inhouds-hash);
- elk afgeleid product (bestandsnaam + inhouds-hash);
- de koppeling: dit product hoort bij die bron-hash.

Geen parallelle herkomstnorm in bibliotheek-stempels *in* `.mxl`/`.svg`
als bron van waarheid voor versheid (dat is consumer-restant tot
afbouw; zie [straat-CLIs](../plans/straat-clis.md)).

## Bestandslocatie

Sibling van de bron:

```text
{bronnaam}.products-meta.json
```

Voorbeelden: `lied.vsa.products-meta.json`, `lied.mvsa.products-meta.json`,
`lied.mscz.products-meta.json`.

## Schema 2 (normatief)

```json
{
  "schema": 2,
  "bron": "lied.mvsa",
  "bron_sha256": "<hex sha256 van de bronbytes>",
  "generated_at": "<UTC ISO-8601>",
  "products": {
    "mxl": {
      "file": "lied.mvsa.mxl",
      "sha256": "<hex sha256 van dat productbestand>"
    },
    "svg-1": {
      "file": "lied.mvsa-1.svg",
      "sha256": "<hex>"
    }
  }
}
```

| Veld                      | Verplicht | Betekenis                                                                 |
| ------------------------- | --------- | ------------------------------------------------------------------------- |
| `schema`                  | Ja        | Exact `2` voor dit contract.                                              |
| `bron`                    | Ja        | Bestandsnaam van de bron (sibling-naam, geen pad).                        |
| `bron_sha256`             | Ja        | SHA-256 (hex, lowercase) van de **huidige** bronbytes bij schrijven.      |
| `generated_at`            | Ja        | UTC-tijdstip van deze meta-schrijfactie (informatief).                    |
| `products`                | Ja        | Object: product-key → `{ "file", "sha256" }`. Minimaal één key.           |
| `products.*.file`         | Ja        | Sibling-bestandsnaam (geen pad).                                          |
| `products.*.sha256`       | Ja        | SHA-256 (hex, lowercase) van de bytes van dat sibling-bestand.            |

Product-keys per straat: zie [contract-index](contract-index.md) (tabel
`mvsa`/`mscz`/`vsa products`). Bladreeks-SVG: `svg` of `svg-1`, `svg-2`, …

### Schema 1 (legacy)

Oude sidecars met alleen bestandsnamen (`"mxl": "lied.mvsa.mxl"`) zijn
**stale**: `freshness()` eist schema 2. Opnieuw `… products` schrijft
schema 2.

## Invariante (hard)

1. **Schrijver = exporteur.** Alleen tooling street-`products` (of een
   gelijkwaardige export die dezelfde siblings maakt) mag deze sidecar
   **overschrijven**. Consumers mogen lezen; niet “achteraf” een andere
   herkomst claimen zonder opnieuw te exporteren.
2. **Atomaire waarheid.** Na een geslaagde `products`-run weerspiegelt de
   sidecar exact de bron en de productbestanden die bij die run horen.
3. **Bron wijzigt → meta mag niet oud blijven.** Als de bytes van de bron
   niet meer gelijk zijn aan `bron_sha256`, is de hele sidecar **stale**.
   Geen productregel uit die meta mag dan als “nog geldig” gelden.
4. **Product-hash moet kloppen (schema 2).** Voor elke vermelde key: het
   bestand `file` bestaat naast de bron, en `sha256_file(file) == sha256`.
   Faalt dat → **stale** of **missing** (niet “ok”).
5. **Geen wees-claims.** Er mag in meta geen productregel staan voor een
   bestand dat niet bij deze export hoort, en geen “ok” claimen voor een
   oude `sha256` nadat de bron of het product is veranderd.

Gevolg: als in meta staat “product met hash \(H_A\) uit bron met hash
\(H_B\)”, dan is dat **waar** op het moment van schrijven; na wijziging
van bron of product is meta niet meer `ok` tot opnieuw `products`.

## Versheidsuitkomsten (lezer)

| Status     | Betekenis (schema 2)                                                                 |
| ---------- | ------------------------------------------------------------------------------------ |
| `ok`       | Meta aanwezig; `bron_sha256` = huidige bron; alle vereiste keys: file bestaat + hash |
| `missing`  | Bron of vermeld productbestand ontbreekt                                             |
| `stale`    | Bron-hash of product-hash wijkt af, of meta ongeldig/incompleet                      |
| `no_meta`  | Sidecar ontbreekt                                                                    |

Diepere inhoudscontrole (bijv. `mxl validate`) blijft een **aparte**
check (`--only-invalid`); die vervangt deze herkomst-sidecar niet.

## Wie schrijft / wie leest

| Rol                                  | Verantwoordelijkheid                                                                                           |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Tooling `vsa`/`mvsa`/`mscz products` | Schrijft sidecar bij elke geslaagde export (schema 2: inclusief product-hashes)                                |
| Tooling `freshness()` / `--force`    | Leest sidecar om regen te slaan                                                                                |
| Bibliotheek `products` / `check`     | Mag **alleen lezen** voor orchestratie en publicatiecontrole; geen eigen herkomststempel als bron van waarheid |

## Implementatiestatus

| Onderdeel                         | Status                                      |
| --------------------------------- | ------------------------------------------- |
| Schema 2 (product-`sha256`)       | **gedaan** in tooling (`products_meta.py`)  |
| Bibliotheek check/regen op meta   | **gedaan** (stamp alleen fallback `no_meta`)|
| Afbouw in-file versheidstempels   | **gedaan** in `sync_*_products` (vsa/mvsa/mscz) |

## Zie ook

- [contract-index](contract-index.md) — matrix street × producten  
- [straat-CLIs](../plans/straat-clis.md) — fasering  
- [`vsa products`](../reference/cli/products.md) · [`mvsa products`](../reference/cli/mvsa.md#mvsa-products)
