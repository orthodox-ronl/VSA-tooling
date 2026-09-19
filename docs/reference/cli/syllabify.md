# `vsa syllabify` — lettergreepstreepjes in ongescoopte VSA-tekst

Voeg orthografische lettergreepstreepjes toe aan woorden in de
[VSA](@)-brontekst, zodat de bestaande MusicXML-export elk deel als eigen
kwartnoot kan zetten (belangrijk voor Coria: elke lettergreep heeft minstens
één noot nodig).

## Synopsis

```text
vsa syllabify [-h] [--dry-run | --in-place] path
```

## Beschrijving

Reciteertekst staat in veel [vsa-bestanden](@bron) als één woord
(`lijden`, `onbederfelijke`). Cadensstukken zitten vaak al in scopes
(`marte{la_}{/ren}`). `vsa syllabify` hypheneert **alleen** de platte tekst
buiten `{…}` (AST-`TextNode`-inhoud) met Pyphen (`nl_NL`).

- Scopes, toonhoogtemarkers (`[…:]`), YAML-frontmatter en HTML-comments
  blijven staan.
- Binnen scopes blijft `-` een [ELM](@); daar wordt niets gewijzigd.
- Een woord dat al `-` bevat (handmatige zing-deling) blijft ongemoeid.
- Dit is **geen** automatische stap bij `vsa musicxml`: bron en product
  blijven voorspelbaar. Na `--in-place` vernieuw je `.vsa.mxl` via
  `scripts\vsa-products.cmd` of `scripts\check.cmd`.

Orthografische hyphenatie is niet altijd dezelfde als liturgische
zing-deling; controleer twijfelgevallen handmatig.

## Argumenten en opties

| Naam           | Verplicht | Betekenis                                                                 | Default                                      | Beperkingen                         |
| -------------- | --------- | ------------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------- |
| `path`         | Ja        | Pad naar een `.vsa`-bestand.                                              | —                                            | Moet een bestaand `.vsa` zijn.      |
| `--dry-run`    | Nee       | Toon het resultaat op stdout; schrijf het bestand niet.                   | Gedrag zonder `--in-place` (preview)         | Mutueel exclusief met `--in-place`. |
| `--in-place`   | Nee       | Schrijf het gehypheneerde resultaat terug naar `path`.                    | Uit                                          | Mutueel exclusief met `--dry-run`.  |
| `-h`, `--help` | Nee       | Toon hulp voor dit subcommando.                                           | —                                            | —                                   |

## Output

- **Zonder `--in-place`** (en met `--dry-run`): gehypheneerde brontekst op
  **stdout**; op **stderr** een regel
  `(dry-run — N lettergreepstreepje(s); bestand niet geschreven)`.
- **Met `--in-place`**: bestand bijgewerkt indien nodig; op stdout
  `<pad>: N lettergreepstreepje(s) toegevoegd` of `<pad>: geen wijzigingen`.

## Exit status

| Exitcode | Betekenis                                       |
| -------- | ----------------------------------------------- |
| `0`      | Syllabificatie gelukt (ook bij geen wijziging). |
| `1`      | Bestand ontbreekt, geen `.vsa`, of parserfout.  |

## Voorbeelden

Preview:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify examples\minimal\voorbeeld.vsa --dry-run
```

In-place, daarna MusicXML-product vernieuwen:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\bestand.vsa --in-place
scripts\vsa-products.cmd
```

Voorbeeldtransformatie:

| Voor               | Na                    |
| ----               | --                    |
| `lijden`           | `lij-den`             |
| `onbederfelijke`   | `on-be-der-fe-lij-ke` |
| `marte{la_}{/ren}` | `mar-te{la_}{/ren}`   |
