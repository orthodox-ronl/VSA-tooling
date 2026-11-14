# Products-meta (herkomst-sidecar)

**Contract-id:** products-meta · schema **2**.  
Canonieke hub voor versheid/herkomst van street-`products`. Elders alleen
linken. Start: [contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                              |
| -------- | --------------------------------------------------- |
| Extensie | `.products-meta.json`                               |
| Rol      | **Sidecar** (herkomst/versheid), geen muziekproduct |
| Sibling  | `{bronnaam}.products-meta.json`                     |
| Wanneer  | Na `{straat} products` of individuele product-subs  |

## Canoniciteit

Canoniek = schema **2** + invarianten hieronder. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

UTF-8 JSON. Velden: zie §Schema 2. Geen muzikale inhoud.

## Syllabificatie

n.v.t.

## Melisma en binding

n.v.t.

## Transliteratie

n.v.t.

## Stemmen en partijen

n.v.t.

## Leesbaarheid

n.v.t.

## Herkomst

Dit bestand **is** de herkomstnorm. Geen parallelle stempel *in*
`.mxl`/`.svg` als bron van waarheid (zie [straat-CLIs](../plans/straat-clis.md)).

## Conversies

Wordt niet “geconverteerd”; wordt **geschreven/gemerged** door exporters.
Lezers: `freshness()` / bibliotheek `check_*`.

## Validatie

`freshness()` → `ok` / `missing` / `stale` / `no_meta` (zie hieronder).

---

## Waartoe (type-specifiek)

De CLI die een afgeleid bestand schrijft, is de enige die betrouwbaar weet
**uit welke bron** dat bestand kwam. Die CLI schrijft daarom dit
stempelbestand. Daarin staan bron-hash, product-hashes en de koppeling.

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
      "sha256": "<hex sha256 van dat productbestand>",
      "generated_at": "<UTC ISO-8601 wanneer dit productbestand geschreven werd>"
    },
    "svg-1": {
      "file": "lied.mvsa-1.svg",
      "sha256": "<hex>",
      "generated_at": "<UTC ISO-8601>"
    }
  }
}
```

| Veld                         | Verplicht | Betekenis                                                                 |
| ---------------------------- | --------- | ------------------------------------------------------------------------- |
| `schema`                     | Ja        | Exact `2` voor dit contract.                                              |
| `bron`                       | Ja        | Bestandsnaam van de bron (sibling-naam, geen pad).                        |
| `bron_sha256`                | Ja        | SHA-256 (hex, lowercase) van de **huidige** bronbytes bij schrijven.      |
| `generated_at`               | Ja        | UTC-tijdstip van deze meta-schrijfactie (informatief).                    |
| `products`                   | Ja        | Object: product-key → productentry. Minimaal één key.                     |
| `products.*.file`            | Ja        | Sibling-bestandsnaam (geen pad).                                          |
| `products.*.sha256`          | Ja        | SHA-256 (hex, lowercase) van de bytes van dat sibling-bestand.            |
| `products.*.generated_at`    | Ja        | UTC-tijdstip waarop **dit** productbestand geschreven werd (informatief). |

**Universele standaardkeys** (zelfde set voor `vsa` / `mvsa` / `mscz`
`products`): `mxl`, `score-ir`, `from-ir`, `mscz`, `mp3`,
`lyrics`, `svg`. Geen `pdf`. Zie
[contract-index — universele productcatalogus](contract-index.md#universele-productcatalogus).

Key `pdf` is geen standaardproduct. `{straat} products` haalt die key
uit een bestaande sidecar (het pdf-bestand zelf wordt niet gewist).
Alleen een losse `vsa pdf`, `mvsa pdf` of `mscz pdf` zet de key weer.
Publicatiecontrole eist het bijbehorende `.vsa.pdf` / `.mvsa.pdf` /
`.mscz.pdf` niet.

SVG-product: altijd key `svg` (één tall compacte sibling `stem.svg`).
Oude bladreeks-keys `svg-1`…`svg-N` worden bij schrijven gedropt.
`freshness(..., required_keys={"svg", …})` accepteert tijdelijk nog
legacy `svg-N` tot products opnieuw is gedraaid.

### Wie schrijft welke keys

- **`{straat} products`** — schrijft de **volledige universele**
  standaardset + top-level `generated_at` (bron = die straat).
- **Individuele product-subs** (bijv. `mscz svg`, `mvsa mp3`) — mogen de
  sidecar **mergen**: bestaande keys van andere producten behouden als
  `bron_sha256` nog klopt; bijgewerkte keys krijgen nieuwe `file` /
  `sha256` / `generated_at`. Wijkt de bron-hash af → treat as stale /
  herschrijf alleen de keys van deze run (of eis `--force` / volle
  `products`); geen stille mix van oude en nieuwe bron.

Nieuwe schrijfacties zetten `products.*.generated_at`. Bestaande
schema-2-meta zonder per-product-tijdstip mag `freshness()` nog lezen.
Individuele product-subs: `write_meta(..., merge=True)` — zie
[straat-CLIs fase 7](../plans/straat-clis.md).

### Schema 1 (legacy)

Oude sidecars met alleen bestandsnamen (`"mxl": "lied.mvsa.mxl"`) zijn
**stale**: `freshness()` eist schema 2. Opnieuw `… products` schrijft
schema 2.

## Invariante (hard)

1. **Schrijver = exporteur.** Alleen tooling street-`products` of een
   individuele product-sub die dezelfde siblings maakt, mag deze sidecar
   **schrijven/mergen**. Consumers mogen lezen; niet “achteraf” een andere
   herkomst claimen zonder opnieuw te exporteren.
2. **Atomaire waarheid per run.** Na een geslaagde `products`-run
   weerspiegelt de sidecar exact de bron en alle standaardproducten van
   die run. Na een individuele product-sub kloppen minstens de keys die
   die sub net schreef (plus behouden keys alleen als bron-hash gelijk
   bleef).
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

| Rol                                             | Verantwoordelijkheid                                                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Tooling `vsa`/`mvsa`/`mscz products`            | Schrijft sidecar bij elke geslaagde export (universele keys; schema 2)                                         |
| Tooling `{straat} {product}`                    | Merget de bijbehorende product-key(s) (sibling-output; anders overslaan + melding)                             |
| Tooling `freshness()` / `--force`               | Leest sidecar om regen te slaan                                                                                |
| Bibliotheek `products` / `check`                | Mag **alleen lezen** voor orchestratie en publicatiecontrole; geen eigen herkomststempel als bron van waarheid |

## Implementatiestatus

| Onderdeel                             | Status                                                            |
| ------------------------------------- | ----------------------------------------------------------------- |
| Schema 2 (product-`sha256`)           | **gedaan** in tooling (`products_meta.py`)                        |
| Schema 2 product-`generated_at`       | **gedaan** (`write_meta` / `build_meta`; fase 7b)                 |
| Merge vanuit individuele product-subs | **gedaan** API; **mscz** + **mvsa** + **vsa** (`musicxml`/`svg`)  |
| Bibliotheek check/regen op meta       | **gedaan** (stamp alleen fallback `no_meta`)                      |
| Afbouw in-file versheidstempels       | **gedaan** in `sync_*_products` (vsa/mvsa/mscz)                   |

## Zie ook

- [contract-index](contract-index.md) — matrix street × producten  
- [straat-CLIs](../plans/straat-clis.md) — fasering  
- [`vsa products`](../reference/cli/products.md) · [`mvsa products`](../reference/cli/mvsa.md#mvsa-products)
