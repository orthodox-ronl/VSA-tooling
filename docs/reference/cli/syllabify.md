# `vsa syllabify` — lettergreepstreepjes in ongescoopte VSA-tekst

Voeg orthografische lettergreepstreepjes toe aan woorden in de
[VSA](@)-brontekst, zodat de bestaande MusicXML-export elk deel als eigen
kwartnoot kan zetten (belangrijk voor Coria: elke lettergreep heeft minstens
één noot nodig). Met `--unsyllabify` doe je het omgekeerde: streepjes weer
weghalen.

## Synopsis

```text
vsa syllabify [-h] [--dry-run | --in-place] [--extension EXT] [--unsyllabify] path
```

## Beschrijving

Reciteertekst staat in veel [vsa-bestanden](@bron) als één woord
(`lijden`, `onbederfelijke`). Cadensstukken zitten vaak al in scopes
(`marte{la_}{/ren}`). `vsa syllabify` hypheneert **alleen** de platte tekst
buiten `{…}` (AST-`TextNode`-inhoud) met Pyphen (`nl_NL`).

- Scopes, toonhoogtemarkers (`[…:]`), YAML-frontmatter en HTML-comments
  blijven staan.
- Binnen scopes blijft `-` een [ELM](@); daar wordt niets gewijzigd — ook
  niet bij `--unsyllabify`.
- Een woord dat al `-` bevat (handmatige zing-deling) blijft bij hypheneren
  ongemoeid; bij `--unsyllabify` verdwijnen die streepjes wél uit ongescoopte
  tekst.
- Dit is **geen** automatische stap bij `vsa musicxml`: bron en product
  blijven voorspelbaar. Na schrijven vernieuw je `.vsa.mxl` via
  `scripts\vsa-products.cmd` of `scripts\check.cmd`.

`path` mag één `.vsa`-bestand zijn of een **map**. Bij een map zoekt het
commando recursief alle `*.vsa`-bestanden (zoals [`vsa validate`](validate.md)
dat voor `.vsa` doet).

Orthografische hyphenatie is niet altijd dezelfde als liturgische
zing-deling; controleer twijfelgevallen handmatig.

### Schrijfmodi

| Modus                          | Gedrag                                                                  |
| ------------------------------ | ----------------------------------------------------------------------- |
| Geen schrijfflag / `--dry-run` | Niets schrijven. Eén bestand: resultaat op stdout. Map: statusregels.   |
| `--in-place`                   | Overschrijf elk bronbestand.                                            |
| `--extension EXT`              | Schrijf naast het bronbestand: `xyz.vsa` → `xyz` + genormaliseerde EXT. |

`--in-place` en `--extension` mag je niet combineren. Met `--extension` mag
je wel `--dry-run` gebruiken om alleen te tonen wat er zou gebeuren.

Bestanden waarvan de naam al op de doelextensie eindigt (bijv. `xyz.syl.vsa`
bij `--extension .syl.vsa`) worden overgeslagen, zodat je geen
`xyz.syl.syl.vsa` krijgt.

## Argumenten en opties

| Naam              | Verplicht | Betekenis                                                                                         | Default                              | Beperkingen                                      |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------ |
| `path`            | Ja        | Pad naar een `.vsa`-bestand of een map met `.vsa`-bestanden.                                      | —                                    | Moet bestaan.                                    |
| `--dry-run`       | Nee       | Toon het resultaat zonder bestanden te schrijven.                                                 | Gedrag zonder schrijfmodus (preview) | Mutueel exclusief met `--in-place`.              |
| `--in-place`      | Nee       | Schrijf het resultaat terug naar elk bronbestand.                                                 | Uit                                  | Niet combineren met `--extension`.               |
| `--extension EXT` | Nee       | Schrijf naar sibling-bestanden met deze extensie (`.syl.vsa` of `syl.vsa` → `xyz.syl.vsa`).       | Uit                                  | Moet eindigen op `.vsa`; niet met `--in-place`.  |
| `--unsyllabify`   | Nee       | Verwijder lettergreepstreepjes uit ongescoopte tekst i.p.v. ze toe te voegen.                     | Uit (hypheneren)                     | Scopes / ELM-`-` blijven staan.                  |
| `-h`, `--help`    | Nee       | Toon hulp voor dit subcommando.                                                                   | —                                    | —                                                |

## Output

- **Eén bestand, dry-run**: gehypheneerde (of ont-syllabifyde) brontekst op
  **stdout**; op **stderr** een regel
  `(dry-run — N lettergreepstreepje(s) toegevoegd|verwijderd; bestand niet geschreven)`.
- **Map, dry-run**: per bestand een statusregel op stdout, bijv.
  `pad\a.vsa -> pad\a.syl.vsa: 2 lettergreepstreepje(s) toegevoegd (dry-run)`.
- **Schrijven (`--in-place` of `--extension`)**: per bestand een statusregel
  op stdout (`<bron>: …` of `<bron> -> <doel>: …`).

## Exit status

| Exitcode | Betekenis                                                                     |
| -------- | ----------------------------------------------------------------------------- |
| `0`      | Alle bestanden verwerkt (ook bij geen wijziging of overgeslagen siblings).    |
| `1`      | Pad ontbreekt, geen `.vsa` gevonden, ongeldige flags/extensie, of parserfout. |

## Voorbeelden

Preview van één bestand:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify examples\minimal\voorbeeld.vsa --dry-run
```

Hele map in-place hypheneren:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify examples\minimal --in-place
```

Naar sibling-extensie `.syl.vsa` (bron blijft ongewijzigd):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\xyz.vsa --extension .syl.vsa
```

Dat schrijft `pad\naar\xyz.syl.vsa`. Zelfde resultaat met `--extension syl.vsa`.

Lettergreepstreepjes weer verwijderen (alleen TextNode-tekst):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\xyz.syl.vsa --unsyllabify --in-place
```

Na schrijven MusicXML-product vernieuwen:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\bestand.vsa --in-place
scripts\vsa-products.cmd
```

Voorbeeldtransformatie:

| Voor               | Na (syllabify)        | Na (`--unsyllabify`) |
| ------------------ | --------------------- | -------------------- |
| `lijden`           | `lij-den`             | `lijden`             |
| `onbederfelijke`   | `on-be-der-fe-lij-ke` | `onbederfelijke`     |
| `marte{la_}{/ren}` | `mar-te{la_}{/ren}`   | `marte{la_}{/ren}`   |
