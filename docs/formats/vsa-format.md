# `vsa format` — body-layout (strofen)

**Status:** contract vastgelegd; **CLI actief** (`vsa format`) voor
`--boundary` / `--layout` / `--wrap`.

Schrijfhulp voor de **VSA-body** (onder de YAML-frontmatter): hoe
**strofen/frasen** begrensd en op regels gezet worden. Geen metadata, geen
zoektekst, geen syllabify — dat hoort bij [`vsa kuiser`](kuiser.md#vsa-v).
Geen `vsa normalize` (bestaat niet); dit is de smalle layout-tool.

Semantiek van frasescheiders in de taal: `*` / `**` / `/` / `//` — zie
[`vsa_stanzas`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/vsa_stanzas.py)
en de VSA-specificatie. Sterke scheiding (`**` / `//`) blijft behouden
waar die al zinvol in de bron staat; format herschrijft vooral de
**gewone** strofegrens volgens de gekozen stijl.

## Doel

| Wel                                                      | Niet                                              |
| -------------------------------------------------------- | ------------------------------------------------- |
| Strofegrenzen eenduidig schrijven                        | Frontmatter / `zoektekst` wijzigen                |
| Layout: één strofe per regel of doorlopende tekst        | Pitch/EHM “mooier” maken                          |
| Optioneel soft wrap op zichtbare-tekst-budget (`--wrap`) | Soft `-` / dictionary (→ syllabify / kuiser)      |
| Idempotent bij dezelfde opties                           | Exacte SVG-pixelbreedte garanderen                |

## Opties (normatief)

### `--boundary` — hoe een strofe **eindigt** in de geschreven bron

| Waarde     | Betekenis                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------- |
| `star`     | Gewone grens als `*` (sterke grens blijft `**` waar die al gold)                                  |
| `slash`    | Gewone grens als `/` (sterke grens blijft `//` waar die al gold)                                  |
| `newline`  | Geen expliciete `*`/`/` tussen strofen; **regeleinde** = strofegrens (zie layout + indent-regel)  |

Default: **`star`** (in lijn met template-mapping die `*` verwacht).

### `--layout` — hoe strofen op regels staan

| Waarde     | Betekenis                                                                                                                                 |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `lines`    | Elke strofe op een **nieuwe regel**. Expliciete `*`/`/` mogen; ontbreken ze, dan geldt de newline-grens.                                  |
| `flow`     | **Doorlopende** tekst (strofen op dezelfde regel of aaneengesloten). Vereist expliciete grens `*` of `/` (`--boundary` ≠ `newline`).      |

Default: **`lines`** (leesbaar in de editor).

### Combinaties

| `--boundary` | `--layout lines`                           | `--layout flow`                                      |
| ------------ | ------------------------------------------ | ---------------------------------------------------- |
| `star`       | toegestaan; `*` aan einde strofe (typisch) | toegestaan; `*` tussen strofen op dezelfde stroom    |
| `slash`      | idem met `/`                               | idem met `/`                                         |
| `newline`    | toegestaan; geen verplichte `*`/`/`        | **verboden** — flow zonder marker is niet eenduidig  |

### Indent = voortzetting

- Een regel die **niet** met witruimte begint, start een nieuwe strofe
  (bij `--layout lines` / `--boundary newline`, of na wrap binnen een strofe).
- Een regel die **wel** met witruimte begint, hoort bij de **vorige**
  strofe (print-wrap / voortzetting).

Zelfde idee als `ensure_stanza_stars`. Bij **`--wrap`** is de canonieke
voortzettingsindent **precies 4 spaties** (geen tabs). Die 4 spaties
**tellen mee** in het regelbudget (zie hieronder).

### `--wrap N` — maximale regellengte (zichtbare-tekst-budget)

**Doel:** bronregels begrensen zodat de **zichtbare zangtekst** ongeveer
binnen `N` “breedte-eenheden” blijft — een *soft* stuurknop voor
editorleesbaarheid en (indirect) SVG-tekstbreedte. De voortzettingsindent
meetelt mee, zodat de **rechterkantlijn** van strofe-deelregels min of meer
recht blijft. Geen garantie op exacte SVG-pixels (noten, melisma en
fontmetrics tellen daar ook mee).

| Waarde   | Betekenis                                                         |
| -------- | ----------------------------------------------------------------- |
| weglaten | Geen wrap (huidig gedrag)                                         |
| `0`      | Zelfde als weglaten                                               |
| `N` ≥ 4  | Soft-wrap binnen elke strofe op budget `N` (indent telt mee)      |
| `1`–`3`  | **Verboden** — voortzetting heeft al 4 spaties indent             |

Geldt bij `--layout lines` en `--layout flow` (voortzetting met 4 spaties
is nooit een nieuwe strofe).

Wrap gebeurt **per strofe** (na `--boundary` / `--layout`): eerst de hele
strofe (inclusief eventuele hoogtemarkering en strofe-delimiter), daarna
opsplitsen in regels van budget `N`.

#### Wat telt mee (budget)

| Soort                                              | Budget                                                    |
| -------------------------------------------------- | --------------------------------------------------------- |
| Voortzettingsindent (precies 4 spaties)            | **4** (alleen op deelregels ná de eerste van de strofe)   |
| Letters van lettergrepen (platte tekst + in `{…}`) | 1 per teken                                               |
| Spaties tussen wrap-eenheden / woorden             | 1 per spatie                                              |
| Overige leestekens in de zangtekst                 | 1 per teken                                               |
| Soft lettergreepstreepje `-`                       | 1                                                         |
| Hard koppelteken `=`                               | 1                                                         |
| Frasegrens `*` of `/`                              | 1                                                         |
| Sterke frasegrens `**` of `//`                     | 2                                                         |
| Elke hoogtemarkering `[…:]`                        | **vast 2** (ongeacht inhoud; meerdere markeringen elk +2) |

Op de **eerste** regel van een strofe is het inhoudsbudget dus `N`. Op elke
**voortzettingsregel** blijven `N − 4` eenheden over voor strofe-inhoud
(want de indent neemt al 4).

#### Wat telt **niet** mee

| Soort                         | Voorbeeld                                           |
| ----------------------------- | --------------------------------------------------- |
| Accolades van scopes          | `{` `}`                                             |
| EHM’s                         | `/` `\` `+` enz. **in** een scope                   |
| ELM’s                         | `_` `~` `.` enz. **in** zangpositie/scope           |
| Melisma-`&`                   | `&`                                                 |
| Overige pure VSA-syntaxtekens | die niet tot zangtekst/leesteken/frasegrens behoren |

Het budget is dus **niet** de ruwe bronlengte, maar een reconstructie van
zichtbare zangtekst + expliciete frasegrenzen + vaste markeringstoeslag
(+ indent op voortzettingen).

#### Wrap-algoritme

1. Bepaal de strofe-inhoud (na `--boundary` / `--layout`), inclusief
   eventuele hoogtemarkering en strofe-delimiter aan het eind.
2. Splits in **wrap-eenheden** (“woorden”): aaneengesloten stukken tot de
   volgende **spatie buiten scopes**. Voorbeeld: `Jo{+\han_}{nes}` is
   **één** eenheid; `ont-ferm` (met soft `-`) is **één** eenheid.
3. Vul de regel links uit. Budgetlimiet is steeds `N`. Op de eerste
   stroferegel start het tellen bij 0; op elke voortzetting start het bij
   **4** (de indent). Past de volgende eenheid niet meer
   (`huidig + spatie + eenheid > N`), dan:
   - die eenheid gaat in zijn geheel naar een **nieuwe regel**;
   - die regel begint met **precies 4 spaties**;
   - herhaal tot de strofe af is.
4. Strofe-delimiter (`*` / `/` / `**` / `//`) mag **niet alleen** op een
   nieuwe regel staan: plak die achter de **vorige** deelregel (ook als
   die daardoor soft over `N` gaat).
5. Een inhouds-eenheid die **alleen** al langer is dan het resterende
   budget mag op een eigen (voortzettings)regel staan — niet middenin
   knippen (die regel mag soft over `N`).

## Wat format niet doet

- YAML-frontmatter lezen/schrijven (behoud bytes of herplaats ongewijzigd).
- Zoektekst, syllabificatie, dictionary.
- Betekenis van scopes `{…}`, EHM’s of soft `-` wijzigen (wel meetellen
  soft `-` in het wrap-budget).
- Kuiser-pipeline stil aanroepen.
- Exacte SVG-breedte in pixels forceren.

## CLI

Man-pagina: [`vsa format`](../reference/cli/format.md).

```text
vsa format [-h] [-o OUTPUT] [--check] [--dry-run]
           [--boundary {star,slash,newline}]
           [--layout {lines,flow}]
           [--wrap N]
           path [path …]
```

| Optie        | Rol                                                                              |
| ------------ | -------------------------------------------------------------------------------- |
| `--dry-run`  | Toon geformatteerd resultaat op het scherm; schrijf niets                        |
| `--check`    | Geen schrijven; exit 1 als er iets zou wijzigen (geen volledige preview)         |
| `path`       | Bestand, map of catalogus-id ([input-pad](../reference/cli/input-pad.md))        |
| `-o`         | Uitvoer (één bron); default in-place; niet met `--dry-run`                       |
| `--boundary` | Default `star`                                                                   |
| `--layout`   | Default `lines`                                                                  |
| `--wrap N`   | Max. budget per regel; weglaten/`0` = uit; anders ≥ 4; indent telt mee           |

`--dry-run` en `--check` zijn niet combineerbaar. Details: man-pagina.

## Relatie tot kuiser

[`vsa kuiser`](kuiser.md#vsa-v) roept **`vsa format` niet stil aan**.
Wie layout wil wijzigen, draait `vsa format` apart (of later optioneel
via een expliciete kuiser-vlag — niet in V1–V8).

## Zie ook

- [kuiser.md](kuiser.md) (V\*) · [vsa.md](vsa.md) · [zoektekst.md](zoektekst.md)
- [syllabificatie.md](syllabificatie.md)
- [contract-index](contract-index.md)
