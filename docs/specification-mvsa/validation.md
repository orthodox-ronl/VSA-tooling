# Validatie (draft)

**Status:** draft v0.

## CLI

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa validate examples\mvsa
vsa mvsa validate examples\mvsa\alleluia-toon-8.mvsa
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa --section schets-a-bladcijfer -o generated\intocht-a.mxl
```

`validate`: exitcode `0` = geen errors (warnings mogen). Exitcode `1` = minstens één error.

`musicxml`: exporteert SATB MusicXML (`.mxl` of `.musicxml`). Faalt als validate
errors heeft. Alleen primaire `L` als lyric-laag; geen blokhergebruik.

## Ernst (voorstel)

| Niveau      | Gebruik                                                        |
| ----------- | -------------------------------------------------------------- |
| **error**   | Structuur of sync klopt niet; verdere verwerking onbetrouwbaar |
| **warning** | Canonieke vorm geschonden maar eenduidig herstelbaar           |
| **info**    | Stijladvies                                                    |

## Structuur

1. Elke LSATB-inhoudsregel begint met een geldige
   [regelidentifier](syntax.md#regelidentifier): `stemidentifier` + optionele
   EHM + `:`. De stemidentifier is `[A-Za-z0-9_-]+` en eindigt niet op `_` of
   `-`. Begint die met `L`/`l`, dan is het een lyrics-regel; anders een
   stemregel. Een EHM op een lyrics-regelidentifier (`L/:`) is een **error**.
2. Binnen een sectie hebben alle LSATB-systemen dezelfde regelidentifiers
   (inclusief eventuele EHM) in dezelfde volgorde.
3. Elk LSATB-systeem eindigt op elke LSATB-regel met `|` of `||` (of
   toegestane specialisatie).
3a. Een **lege regel** binnen of direct na LSATB-inhoud **eindigt** het lopende
    LSATB-systeem. Lege regels horen dus **niet** tussen `L:` en `S:` van
    hetzelfde systeem; wél tussen twee systemen (primaire scheiding). Optioneel
    mag `@---` (met commentaar) of een andere directive hetzelfde doen.
    `#`-commentaar mag wél tussen markers van hetzelfde systeem.
4. Een **sectie** (`@sectie` of anoniem) eindigt door: (a) `||` of `:||` op alle
   LSATB-regels van een systeem (expliciet midden in het bestand); of (b) een
   nieuwe `@sectie` — de **laatste maatstreep** van het vorige laatste systeem
   (`|` of `||`, …) is dan het sectie-einde; of (c) einde van het bestand (EOF);
   of (d) sluiten van een `::: mvsa-notatie` / `::: mvsa`-fence (zelfde als EOF).
   Geen warning `MVSA-SECTIE-IMPLICIT` meer voor (b)/(c)/(d).
   **Uitzondering:** speelblokken (`@blok`) — geen `||`-eis tussen blokken
   (zie [Speelplan](speelplan.md)).
5. `@sectie` *id* voldoet aan `[a-z][a-z0-9_-]*`.
5a. `@blok` / `@speelplan`: zie [Speelplan](speelplan.md). Eén `@speelplan` per
    bestand; geen `@sectie`/anonieme muziek naast een speelplan; geen
    herhaalstrepen in speelplan-blokken.

## Sync

6. Per maat: alle lyrics-regels en alle stemregels hebben hetzelfde aantal
   lengte-posities (recite = 1; melisma-slots tellen mee).
7. Parallelle lyrics (`L` en `L1` in hetzelfde systeem) hebben per maat dezelfde
   positietelling.
8. Elk hoogte-slot op een stemregel is een geldig hoogte-token (EHM, absolute
   toon/laddergraad, of aanhouden `-`/`~`). L-duur-ELM’s zoals `_` op de stem
   zijn een **error** (`MVSA-HOOGTE`), met marker, maat, positie en slot.
8a. Optioneel eindanker direct na een maatstreep (geen spatie): zie
   [Syntax — eindanker](syntax.md#eindanker-aan-de-maatstreep). Ongeldige anker-
   tekst of mismatch met de berekende lopende toon: **error** (`MVSA-BAR-ANKER`).
   Een kale streep is geen anker. Lyrics-regels met een anker-suffix: error.

## Directives / keywords

9. Onbekende `@`-keywords (geldige vorm, niet in
   [Keywords](keywords.md)): **warning**. Ongeldige keyword-vorm (bijv. `@1foo`):
   ook **warning**. Gedefinieerd in v0: sticky (`@do`, `@mode`, `@oct`,
   `@start`), layout (`@tekst`, `@mscz-newline`, `@sectie`, `@blok`,
   `@speelplan`, `@---`), actieve metadata (`@title`, `@ondertitel`,
   `@composer`, `@tekstdichter`, `@arrangeur`, `@vertaler`, `@bron`,
   `@copyright`), en gereserveerde metadata (`@toon`, `@taal`, `@genre`,
   `@opmerkingen`).
10. Sticky / `@tekst` / metadata met ongeldige waarde: **error**
    (`MVSA-META` voor string-metadata). `@mscz-newline` met argumenten:
    **error**. `@tekst` of `@mscz-newline` zonder volgend LSATB-systeem:
    **warning**.

## Canonieke vorm (warning)

11. Ontbrekende woordstreepjes binnen een woord, of streepjes tussen woorden
    (nog niet volledig geautomatiseerd).
12. Maatstrepen niet op alle LSATB-regels herhaald terwijl de kuiser ze eenduidig
    had kunnen syncen — of, na kuiser, alsnog inconsistent: error.

## Buiten v0-validatie / export-beperkingen

- Volledige controle op enharmonische/`#`/`b`-spellingen t.o.v. `@mode` (norm
  staat in [Syntax — kruis en mol](syntax.md#kruis-en-mol); tooling volgt
  gefaseerd);
- Muzikale “juistheid” t.o.v. een blad (alleen telling en vorm bij validate);
- blokhergebruik-referenties (`@voices`, `L'`, deelbereiken);
- parallelle lyric-nummers (`L1` als tweede `<lyric number>`);
- MSCZ-export.
