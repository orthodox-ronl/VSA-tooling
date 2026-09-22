# Validatie (draft)

**Status:** draft v0. Er is nog geen `vsa`-commando dat `.mvsa` valideert; deze
regels zijn het contract voor een toekomstige validator.

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

8. Onbekende `@`-directives: error of warning (v0: error voor alles behalve
   `@do`, `@mode`, `@oct`, `@sectie`).
9. `@do` / `@mode` / `@oct` met ongeldige waarde: error.

## Canonieke vorm (warning)

10. Ontbrekende woordstreepjes binnen een woord, of streepjes tussen woorden.
11. Maatstrepen niet op alle LSATB-regels herhaald terwijl de kuiser ze eenduidig
    had kunnen syncen — of, na kuiser, alsnog inconsistent: error.

## Buiten v0-validatie

- Muzikale “juistheid” t.o.v. een blad (alleen telling en vorm);
- blokhergebruik-referenties;
- export naar MusicXML/MSCZ.
