# `vsa syllabify` — lettergreepstreepjes in VSA-tekst

**Norm:** zing-deling hoort in de canonieke bron — zie
[syllabificatie](../../formats/syllabificatie.md) (soft `-` versus hard `=`,
strip per product, uitzonderingslijst voor bewust eenlettergrepige woorden).

Dit commando is de **schrijfhulp**: het zet (of met `--unsyllabify`: verwijdert)
orthografische lettergreepstreepjes in de [VSA](@)-brontekst, zodat elke
lettergreep als eigen tekstpositie / noot zichtbaar is (Coria: minstens één
noot per lettergreep; streepjes markeren woorddoorloop). Controleer het
resultaat altijd handmatig; Pyphen is geen liturgische eindredacteur.

## Synopsis

```text
vsa syllabify [-h] [--dry-run] [--in-place] [--extension EXT] [--unsyllabify]
              [--config PAD] [--syllable-dictionary PAD] path
```

## Beschrijving

Reciteertekst staat in veel [vsa-bestanden](@bron) als één woord
(`lijden`, `onbederfelijke`). Cadensstukken zitten vaak al in scopes
(`marte{la_}{/ren}`). `vsa syllabify` hypheneert elk woord met Pyphen
(`nl_NL`), inclusief woorden die over platte tekst en scopes heen lopen.
Staat het lemma al in `syllable_dictionary.nl.txt`, dan wint die canonieke
vorm (hoofdletters van de bron blijven). Na hypheneren controleert het
commando dezelfde dictionary-codes als validate
(`VSA-SYLLABLE-DICT-MISMATCH` / `UNKNOWN`). Op een TTY kun je meteen
corrigeren: bron vervangen naar de canonieke vorm, of een (hyphen-)vorm
accepteren in de lijst — zie
[syllabificatie](../../formats/syllabificatie.md).

Binnen **platte** tekst komen soft `-` tussen lettergrepen
(`Voorloper` → `Voor-lo-per`). Op de grens met een scope komt **geen**
streepje: `Jo{+\han_}{/nes_}` blijft zo (niet `Jo-{+\han_}-{/nes_}`), want
de accolade is al de lettergreepgrens.

- De inhoud van scopes (zangelement, [EHM](@), [ELM](@)) blijft onaangeroerd.
  Verouderde brugstreepjes `-` naast `{`/`}` worden bij syllabify weggehaald.
- Toonhoogtemarkers (`[…:]`), YAML-frontmatter (inclusief `zoektekst`) en
  HTML-comments blijven staan. Interactieve dictionary-vervangingen raken
  alleen de VSA-body — nooit `zoektekst` (die hoort **zonder** soft `-`).
- Binnen scopes blijft `-` een [ELM](@); daar wordt niets gewijzigd — ook
  niet bij `--unsyllabify`.
- Een woord dat al `-` bevat en helemaal buiten scopes staat (handmatige
  zing-deling) blijft bij hypheneren ongemoeid; bij `--unsyllabify`
  verdwijnen die streepjes wél. Over scope-grenzen heen worden breekpunten
  opnieuw uit Pyphen afgeleid.
- **Hard streepje:** schrijf een orthografisch koppelteken als `=` in de
  bron (`mede=eeuwige`). Syllabify hypheneert de delen apart
  (`me-de=eeu-wi-ge`); `--unsyllabify` houdt `=`; `vsa text` / MusicXML /
  SVG tonen een gewoon streepje. Zachte `-` verdwijnen in zoektekst, `=`
  niet (wordt `-`).
- Dit is **geen** verplichte stille products-stap in het doelbeeld: de
  deling staat in de bron ([syllabificatie](../../formats/syllabificatie.md)).
  Los `vsa mxl` syllabificeert alleen met `--syllabify`. Na vastleggen in
  de bron vernieuw je siblings met `vsa products`.

`path` mag één `.vsa`-bestand zijn of een **map**. Bij een map zoekt het
commando recursief alle `*.vsa`-bestanden (zoals [`vsa validate`](validate.md)
dat voor `.vsa` doet). Andere extensies (bijv. `.mvsa`) worden geweigerd —
gebruik [`mvsa syllabify`](mvsa.md#mvsa-syllabify) / [`mvsa validate`](mvsa.md#mvsa-validate)
voor L-lyrics in `.mvsa`.

Orthografische hyphenatie is niet altijd dezelfde als liturgische
zing-deling; controleer twijfelgevallen handmatig. Woorden die Pyphen als
meerlettergrepig ziet maar één lettergreep moeten blijven, horen op de
uitzonderingslijst in de syllabificatie-norm — niet “stil” ongesplitst
laten zonder die lijst.

### Schrijfmodi

Zelfde patroon als [`vsa zoektekst`](zoektekst.md) / [`mvsa kuiser`](mvsa.md#mvsa-kuiser):
**default schrijft in-place**; `--dry-run` toont alleen een preview.

| Modus             | Gedrag                                                                  |
| ----------------- | ----------------------------------------------------------------------- |
| (geen flag)       | Overschrijf elk bronbestand (in-place).                                 |
| `--dry-run`       | Niets schrijven. Eén bestand: resultaat op stdout. Map: statusregels.   |
| `--in-place`      | Expliciet in-place (zelfde als default; handig in scripts).             |
| `--extension EXT` | Schrijf naast het bronbestand: `xyz.vsa` → `xyz` + genormaliseerde EXT. |

`--in-place` en `--extension` mag je niet combineren. Met `--extension` mag
je wel `--dry-run` gebruiken om alleen te tonen wat er zou gebeuren.

Bestanden waarvan de naam al op de doelextensie eindigt (bijv. `xyz.syl.vsa`
bij `--extension .syl.vsa`) worden overgeslagen, zodat je geen
`xyz.syl.syl.vsa` krijgt.

## Argumenten en opties

| Naam              | Verplicht | Betekenis                                                                               | Default          | Beperkingen                                     |
| ----------------- | --------- | --------------------------------------------------------------------------------------- | ---------------- | ----------------------------------------------- |
| `path`            | Ja        | Pad naar een `.vsa`-bestand of een map met `.vsa`-bestanden.                            | —                | Moet bestaan.                                   |
| `--dry-run`       | Nee       | Toon het resultaat zonder bestanden te schrijven.                                       | Uit (schrijven)  | —                                               |
| `--in-place`      | Nee       | Schrijf terug naar elk bronbestand (default-gedrag).                                    | Aan (impliciet)  | Niet combineren met `--extension`.              |
| `--extension EXT` | Nee       | Schrijf naar sibling-bestanden (`.syl.vsa` of `syl.vsa` → `xyz.syl.vsa`).               | Uit              | Moet eindigen op `.vsa`; niet met `--in-place`. |
| `--unsyllabify`   | Nee       | Verwijder lettergreepstreepjes (ook brugstreepjes rond scopes) i.p.v. ze toe te voegen. | Uit (hypheneren) | Scope-inhoud / ELM-`-` blijven staan.           |
| `-h`, `--help`    | Nee       | Toon hulp voor dit subcommando.                                                         | —                | —                                               |

## Output

- **Eén bestand, dry-run**: gehypheneerde (of ont-syllabifyde) brontekst op
  **stdout**; op **stderr** een regel
  `(dry-run — N lettergreepstreepje(s) toegevoegd|verwijderd; bestand niet geschreven)`.
- **Map, dry-run**: per bestand een statusregel op stdout, bijv.
  `pad\a.vsa -> pad\a.syl.vsa: 2 lettergreepstreepje(s) toegevoegd (dry-run)`.
- **Schrijven (default / `--in-place` / `--extension`)**: per bestand een
  statusregel op stdout (`<bron>: …` of `<bron> -> <doel>: …`).

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

Hele map in-place hypheneren (default schrijft):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify examples\minimal
```

Naar sibling-extensie `.syl.vsa` (bron blijft ongewijzigd):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\xyz.vsa --extension .syl.vsa
```

Dat schrijft `pad\naar\xyz.syl.vsa`. Zelfde resultaat met `--extension syl.vsa`.

Lettergreepstreepjes weer verwijderen (brugstreepjes rond scopes inbegrepen):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\xyz.syl.vsa --unsyllabify
```

Canonieke bronnen horen gesyllabificeerd te zijn
([syllabificatie](../../formats/syllabificatie.md)). Typische workflow:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa syllabify pad\naar\bestand.vsa --dry-run
vsa syllabify pad\naar\bestand.vsa
vsa products pad\naar\bestand.vsa --force
```

Los `vsa mxl --syllabify` blijft optioneel voor tijdelijke export zonder de
bron te wijzigen; [`vsa products`](products.md) doet **geen** stille
syllabify meer.

Voorbeeldtransformatie:

| Voor                   | Na (syllabify)        | Na (`--unsyllabify`) |
| ---------------------- | --------------------- | -------------------- |
| `lijden`               | `lij-den`             | `lijden`             |
| `onbederfelijke`       | `on-be-der-fe-lij-ke` | `onbederfelijke`     |
| `marte{la_}{/ren}`     | `mar-te{la_}{/ren}`   | `marte{la_}{/ren}`   |
| `Jo{+\han_}{/nes_}`    | `Jo{+\han_}{/nes_}`   | `Jo{+\han_}{/nes_}`  |
| `ver-{/heer}-{\lijkt}` | `ver{/heer}{\lijkt}`  | `ver{/heer}{\lijkt}` |
| `{/heb}ben`            | `{/heb}ben`           | `{/heb}ben`          |

## Zie ook

- [syllabificatie](../../formats/syllabificatie.md) — norm (bron leidend)
- [`vsa products`](products.md) — products volgen de bron-deling
- [`vsa mxl --syllabify`](musicxml.md) — optionele tijdelijke export-syllabify
- [`vsa text`](text.md) — platte gezongen tekst
