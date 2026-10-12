# Zoektekst in canonieke `.vsa` / `.mvsa`

**Status:** normatief contract (afspraak). Tooling die `zoektekst` vult of
controleert volgt nog; de extractie zelf bestaat al als
[`vsa text`](../reference/cli/text.md).

## Doel

Beheerders moeten in de editor (bijv. VS Code, Ctrl+Shift+F) een
[uitvoeringsvorm](@bron) kunnen vinden op **gewone woorden** uit de gezongen
tekst, ook als ze de id of mapnaam niet precies kennen.

In de notatie-body staan woorden vaak onderbroken door lettergreepstreepjes en
hoogte-/duurmarkeringen. Daarom hoort de **niet-gesyllabiseerde** platte tekst
ook in het bronbestand zelf — niet als handmatige kopie, maar als afgeleid veld.

## Afspraken

| Regel                 | Eis                                                                                                                                                                                                                    |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Veldnaam              | `zoektekst` (niet «lyrics» — dat is de gezongen L-regel / VSA-body)                                                                                                                                                    |
| Plek                  | YAML-frontmatter aan het begin van het bestand (`---` … `---`), **top-level** sleutel                                                                                                                                  |
| Geldt voor            | Canonieke catalogusbronnen: zelfstandige `.vsa` en canonieke `.mvsa`                                                                                                                                                   |
| Inhoud                | De volledige platte gezongen tekst, in documentvolgorde                                                                                                                                                                |
| Bron van waarheid     | De notatie-body (VSA-tekst of L-regel(s)); `zoektekst` is afgeleid                                                                                                                                                     |
| Onderhoud             | Tooling vult of vernieuwt het veld; de beheerder typt `zoektekst` niet handmatig bij                                                                                                                                   |
| Equivalentie          | Genormaliseerd gelijk aan extractie uit de body (zie hieronder) — **zonder** het `zoektekst`-veld zelf mee te lezen                                                                                                    |
| Sibling `.lyrics.txt` | Geen verplicht product naast een canonieke `.vsa` / `.mvsa`. Optioneel blijven voor export uit `.mscz` / `.mxl` of site-build (`vsa text -o`) — zie [naamgeving](canonical-checklists.md#bestandsnaamgeving-conventie) |

## Schrijfwijze

### `.vsa`

```yaml
---
muziek:
  do: F4
  mode: major
identificatie:
  title: Kondak Nikolaas van Myra, toon 3
zoektekst: >-
  Heilige Nikolaas van Myra, gij zijt werkelijk de Hogepriester van Christus.
  Volgens het Evangelie hebt gij uw leven ingezet om onschuldigen te redden
  uit de dood. Daarin hebt gij de heiligheid gevonden, als de Uitdeler der
  Mysteriën van Gods genade.
---

[\\:] Hei-li{/ge} {/Ni}ko{\laas} …
```

Platte of geneste frontmatter (zoals in catalogus-repos) mag; `zoektekst` blijft
een **top-level** sleutel naast `muziek` / `identificatie` of naast platte velden
als `do` / `toon`.

### `.mvsa`

Canonieke `.mvsa`-bronnen gebruiken voor `zoektekst` **dezelfde** YAML-kop.
Overige partituur-metadata blijft bij voorkeur via `@`-keywords (zie
[Metadata-brug](../guides/metadata-brug.md)).

```yaml
---
identificatie:
  title: 2e Antifoon (zondag)
zoektekst: >-
  Eer aan de Vader, de Zoon, en de Heilige Geest. Loof, mijn ziel de Heer,
  ik wil de Heer loven in heel mijn leven, …
---

@do F4
@mode major

L: Eer_&_ aan de Va_-der,_ …
```

**Niet canoniek** als enige plek voor de platte tekst: vrije `#`-commentaren of
HTML-commentaren zonder vast contract.

## Equivalentie met `vsa text`

1. Strip of negeer het `zoektekst`-veld bij extractie uit hetzelfde bestand.
2. Bereken de referentietekst zoals [`vsa text`](../reference/cli/text.md) op
   `.vsa` / `.mvsa` (zachte `-` weg; hard `=` → zichtbaar `-`).
3. Normaliseer beide kanten vóór vergelijking: leading/trailing witruimte weg;
   elke reeks spaties, tabs of newlines wordt één spatie.
4. Na normalisatie moeten `zoektekst` en de body-extractie **gelijk** zijn.

Tooling schrijft bij voorkeur `zoektekst: >-` als één doorlopende alinea. Een
blokscalar `|` met regeleinden mag, zolang de genormaliseerde vorm klopt.

## Wat dit niet is

| Onderwerp                              | Waar anders                                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Catalogus-zoek op titel / rol          | [catalogus zoek-API](https://github.com/orthodox-ronl/bron/blob/main/docs/specs/catalogus-zoek-api.md) |
| Export van alleen woorden naar bestand | [`vsa text -o`](../reference/cli/text.md) (o.a. uit `.mscz` / `.mxl`)                                  |
| Gezongen lettergrepen in de partituur  | L-regel (`.mvsa`) of VSA-body (`.vsa`)                                                                 |

## Tooling

| Stap                            | Status / gedrag                                                                                          |
| ------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `.mvsa`: YAML-frontmatter lezen | **Geïmplementeerd** — `parse_mvsa` / `validate` / `vsa text` strippen de `---`-kop                       |
| `vsa text` op `.vsa` / `.mvsa`  | Body-extractie; `zoektekst` telt niet mee in de referentietekst                                          |
| Vullen / vernieuwen             | **Geïmplementeerd** — [`vsa zoektekst`](../reference/cli/zoektekst.md) (default: in-place)               |
| Controleren                     | **Geïmplementeerd** — `vsa zoektekst --check`; optioneel `mvsa validate --require-zoektekst`             |

## Zie ook

- [`.vsa`](vsa.md) · [`.mvsa`](mvsa.md)
- [YAML frontmatter (VSA)](../specification/syntax.md#yaml-frontmatter-in-vsa-bestanden)
- [MVSA — bestand](../specification-mvsa/syntax.md#1-bestand)
- [Metadata-brug](../guides/metadata-brug.md)
- [`vsa text`](../reference/cli/text.md)
