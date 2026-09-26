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

1. Elke LSATB-inhoudsregel begint met een geldige marker `[LSATB]\d*:`.
2. Binnen een sectie hebben alle LSATB-systemen dezelfde markers in dezelfde
   volgorde.
3. Elk LSATB-systeem eindigt op elke LSATB-regel met `|` of `||` (of
   toegestane specialisatie).
4. Een sectie eindigt alleen als alle LSATB-regels van dat systeem `||` of
   `:||` tonen op de eindpositie.
5. `@sectie` *id* voldoet aan `[a-z][a-z0-9_-]*`.

## Sync

6. Per maat: alle lyrics-regels en alle stemregels hebben hetzelfde aantal
   lengte-posities (recite = 1; melisma-slots tellen mee).
7. Parallelle lyrics (`L` en `L1` in hetzelfde systeem) hebben per maat dezelfde
   positietelling.

## Directives

8. Onbekende `@`-directives: error (v0 toegestaan: `@do`, `@mode`, `@oct`,
   `@sectie`, `@start`).
9. `@do` / `@mode` / `@oct` met ongeldige waarde: error.

## Canonieke vorm (warning)

10. Ontbrekende woordstreepjes binnen een woord, of streepjes tussen woorden
    (nog niet volledig geautomatiseerd).
11. Maatstrepen niet op alle LSATB-regels herhaald terwijl de kuiser ze eenduidig
    had kunnen syncen — of, na kuiser, alsnog inconsistent: error.

## Buiten v0-validatie / export-beperkingen

- Volledige controle op enharmonische/`#`/`b`-spellingen t.o.v. `@mode` (norm
  staat in [Syntax — kruis en mol](syntax.md#kruis-en-mol); tooling volgt
  gefaseerd);
- Muzikale “juistheid” t.o.v. een blad (alleen telling en vorm bij validate);
- blokhergebruik-referenties (`@voices`, `L'`, deelbereiken);
- parallelle lyric-nummers (`L1` als tweede `<lyric number>`);
- MSCZ-export.
