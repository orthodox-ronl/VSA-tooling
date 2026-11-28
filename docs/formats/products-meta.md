# Products-meta (herkomst-sidecar)

**Contract-id:** products-meta · schema **3** (schema 2 blijft leesbaar).  
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

UTF-8 JSON. Velden: zie §Schema 3. Geen muzikale inhoud.

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

## Schema 3 (normatief)

```json
{
  "schema": 3,
  "bron": "lied.mvsa",
  "bron_sha256": "<hex sha256 van de bronbytes>",
  "invoer": {
    "bron": "<hex sha256 van de bronbytes>",
    "woorden": "<hex sha256 over de gezongen woorden en hun vorm in de woordenlijst, of leeg>",
    "template": "<hex sha256 van het template (alleen .vsa), of leeg>",
    "recept": 1,
    "sha256": "<hex sha256 over bovenstaande vier>"
  },
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
| `schema`                     | Ja        | `3` voor nieuwe sidecars; `2` (zonder `invoer`) blijft leesbaar.          |
| `bron`                       | Ja        | Bestandsnaam van de bron (sibling-naam, geen pad).                        |
| `bron_sha256`                | Ja        | SHA-256 (hex, lowercase) van de **huidige** bronbytes bij schrijven.      |
| `invoer`                     | Schema 3  | Vingerafdruk van alles wat de producten bepaalt (zie §Invoer).            |
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

### Invoer (schema 3)

Eén vingerafdruk per bron: wat bepaalt of afgeleide producten nog kloppen.
Berekend door `vsa.products_invoer.bereken_invoer`. Elk deel staat apart in
de meta, zodat `freshness()` kan zeggen **wat** veranderde.

| Deel       | Wat erin zit                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `bron`     | SHA-256 van de bronbytes (zoals ze op schijf staan, dus ná `validate`).                                                        |
| `woorden`  | De woorden die de bron zingt, met hun toegestane vormen in de woordenlijst. Een ander woord in de lijst verandert dit niet.    |
| `template` | Inhoud van het template van een `.vsa` (`template:` in de frontmatter, anders de gewone keuze). Leeg bij `.mvsa` en `.mscz`.   |
| `recept`   | Getal per bronsoort (`RECEPT_VERSIE` in `vsa.products_invoer`, ook als `vsa.products_meta.RECEPT_VERSIE`).                     |

Woorden in een taal zonder woordenlijst (`@taal ro`) tellen niet mee. De
tooling-commit telt **niet** mee.

**Recept-versie ophogen:** in dezelfde pull request die de uitkomst van een
export bewust wijzigt, met een regel in `CHANGELOG.md`. Daarna zijn alle
producten van die bronsoort `stale` tot ze opnieuw gemaakt zijn.

**Twee standen.** `freshness(bron)` (standaard `invoer="los"`) kijkt alleen
naar de bron-hash, ook bij schema 3, en meldt bij schema 2 "oud schema".
`freshness(bron, invoer="streng")` eist schema 3 en vergelijkt de hele
invoer. Gebruik `streng` pas als bij het controleren dezelfde woordenlijst
actief is als bij het schrijven; anders lijkt elk product verouderd. `upgrade_meta(bron)` zet
schema 2 om naar schema 3 **alleen als alles nu `ok` is**; verouderde
producten blijven ongemoeid en moeten eerst opnieuw gemaakt worden.

Nieuwe schrijfacties zetten `products.*.generated_at`. Bestaande
schema-2-meta zonder per-product-tijdstip mag `freshness()` nog lezen.
Individuele product-subs: `write_meta(..., merge=True)` — zie
[straat-CLIs fase 7](../plans/straat-clis.md).

### Schema 1 (legacy)

Oude sidecars met alleen bestandsnamen (`"mxl": "lied.mvsa.mxl"`) zijn
**stale**: `freshness()` eist schema 2 of 3. Opnieuw `… products` schrijft
schema 3.

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
3. **Invoer wijzigt → meta mag niet oud blijven.** Als de bytes van de bron
   niet meer gelijk zijn aan `bron_sha256`, of (schema 3) een ander deel van
   `invoer` (woorden, template, recept) wijkt af, is de hele sidecar
   **stale**. Geen productregel uit die meta mag dan als “nog geldig” gelden.
4. **Product-hash moet kloppen.** Voor elke vermelde key: het
   bestand `file` bestaat naast de bron, en `sha256_file(file) == sha256`.
   Faalt dat → **stale** of **missing** (niet “ok”).
5. **Geen wees-claims.** Er mag in meta geen productregel staan voor een
   bestand dat niet bij deze export hoort, en geen “ok” claimen voor een
   oude `sha256` nadat de bron of het product is veranderd.

Gevolg: als in meta staat “product met hash \(H_A\) uit bron met hash
\(H_B\)”, dan is dat **waar** op het moment van schrijven; na wijziging
van bron of product is meta niet meer `ok` tot opnieuw `products`.

## Versheidsuitkomsten (lezer)

| Status     | Betekenis                                                                            |
| ---------- | ------------------------------------------------------------------------------------ |
| `ok`       | Meta aanwezig; bron en (schema 3) invoer kloppen; alle vereiste keys: file + hash    |
| `missing`  | Bron of vermeld productbestand ontbreekt                                             |
| `stale`    | Bron, invoer of product-hash wijkt af, of meta ongeldig/incompleet                   |
| `no_meta`  | Sidecar ontbreekt                                                                    |

Diepere inhoudscontrole (bijv. `mxl validate`) blijft een **aparte**
check (`--only-invalid`); die vervangt deze herkomst-sidecar niet.

## Wie schrijft / wie leest

| Rol                                             | Verantwoordelijkheid                                                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Tooling `vsa`/`mvsa`/`mscz products`            | Schrijft sidecar bij elke geslaagde export (universele keys; schema 3)                                         |
| Tooling `{straat} {product}`                    | Merget de bijbehorende product-key(s) (sibling-output; anders overslaan + melding)                             |
| Tooling `freshness()` / `--force`               | Leest sidecar om regen te slaan                                                                                |
| Bibliotheek `products` / `check`                | Mag **alleen lezen** voor orchestratie en publicatiecontrole; geen eigen herkomststempel als bron van waarheid |

## Implementatiestatus

| Onderdeel                             | Status                                                                                 |
| ------------------------------------- | -------------------------------------------------------------------------------------- |
| Schema 2 (product-`sha256`)           | **gedaan** in tooling (`products_meta.py`)                                             |
| Schema 3 (`invoer`, `upgrade_meta`)   | **gedaan** in tooling (stap 6); bibliotheek schakelt over naar `invoer="streng"` later |
| Schema 2 product-`generated_at`       | **gedaan** (`write_meta` / `build_meta`; fase 7b)                                      |
| Merge vanuit individuele product-subs | **gedaan** API; **mscz** + **mvsa** + **vsa** (`musicxml`/`svg`)                       |
| Bibliotheek check/regen op meta       | **gedaan** (stamp alleen fallback `no_meta`)                                           |
| Afbouw in-file versheidstempels       | **gedaan** in `sync_*_products` (vsa/mvsa/mscz)                                        |

## Zie ook

- [contract-index](contract-index.md) — matrix street × producten  
- [straat-CLIs](../plans/straat-clis.md) — fasering  
- [`vsa products`](../reference/cli/products.md) · [`mvsa products`](../reference/cli/mvsa.md#mvsa-products)
