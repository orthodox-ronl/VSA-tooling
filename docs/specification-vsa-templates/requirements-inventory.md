# Requirements-inventory

Feature-eisen afgeleid uit toonboekbladen (vers-, stichier-, tropaarmelodieën),
**zonder** canonieke pitchlijsten uit AI/OMR. Doel: wat een [vsa-template](@)
minimaal moet kunnen uitdrukken.

Kolommen:

- **Waargenomen** — komt voor op blad(en)
- **Nodig in template-taal** — moet uitdrukbaar zijn
- **Status** — `required` / `optional` / `open`

## Structuur en navigatie

| Feature                         | Waargenomen                         | Nodig in template-taal              | Status     |
| ------------------------------- | ----------------------------------- | ----------------------------------- | ---------- |
| Frase met id                    | `(1)`, `(2)`, `laatste`, …          | `phrases[].id`                      | required   |
| Variante frase-id               | `(1a)`, `(2a)`                      | ids zoals `"1a"`, `"2a"`            | required   |
| Bibliotheekfrase buiten cycle   | `1a` in tekstvoorbeeld toon 1       | frase in `phrases`, niet in cycle   | required   |
| Genummerde frasen               | circels 1–4                         | string-ids                          | required   |
| Slotfrase                       | label `laatste`                     | id `laatste` (cycle-form)           | required   |
| Herhalingscyclus                | `\|\|: 1, 2 :\|\| laatste`          | `cycle` + `final`                   | required   |
| Langere cyclus                  | `\|\|: 1,2,3 :\|\| laatste`         | zelfde `cycle`-model                | required   |
| Vaste frasevolgorde             | toon 3: `1,3,1,2,3,1,4,laatste`     | `sequence` (+ truncatie op `laatste`) | required |
| Genre-equivalentie              | Groningen toon 5: tropaar = kondak; PDF-stichier blijft apart | `same_as` / `also_used_as` | required   |
| Herhaalpunten / dubbele streep  | begin/eind van cycle-blok           | impliciet via `cycle`               | required   |

## Muzikale events

| Feature                         | Waargenomen                         | Nodig in template-taal                         | Status     |
| ------------------------------- | ----------------------------------- | ---------------------------------------------- | ---------- |
| Vaste nootduur                  | achtste, kwart, half, hele          | `duration` incl. `eighth`                      | required   |
| Reciteertoon                    | breve / “box”-kop                   | `role: recite`, variabele syllaben             | required   |
| Openingskwart vóór recite       | zelfde pitch als recite             | `role: open` of eerste vaste event             | required   |
| Optionele noot                  | noot tussen haakjes                 | `optional: true`                               | required   |
| Anker `e. st.`                  | pijl + label                        | `anchor: e.st.`                                | required   |
| Anker `l. st.`                  | pijl + label                        | `anchor: l.st.`                                | required   |
| Anker `vl. st.`                 | pijl + label (vers/stichier)        | `anchor: vl.st.`                               | required   |
| Anker `l. lgr.`                 | pijl + label (melisma)              | `anchor: l.lgr.`                               | required   |
| Pre-cadens / cadensnoten        | reeks na recite                     | `role: cadence` (+ volgorde)                   | required   |
| Stemmen SATB                    | twee notenbalken                    | `pitches` als laddergraden                     | required   |
| Voortekening                    | mol/kruis op blad                   | afleidbaar uit `do`+`mode`; optioneel hintveld | optional   |
| Do-context                      | (VSA-praktijk / export)             | `do` + `mode` (verplicht)                      | required   |
| Duur t.o.v. standaard           | VSA-ELMs                            | `duration` als ELM (`~` `_` `_.` …)            | required   |

## Metadata / identificatie

| Feature                         | Waargenomen                         | Nodig in template-taal              | Status     |
| ------------------------------- | ----------------------------------- | ----------------------------------- | ---------- |
| Genre                           | Tropaar / Stichier / Vers           | `genre`                             | required   |
| Toon (glas)                     | Toon 1 … 8                          | `tone`                              | required   |
| Bronverwijzing                  | PDF/pagina                          | `source` (vrij tekstveld)           | optional   |
| Pitch-betrouwbaarheid           | menselijke correctie nodig          | `pitches_status`                    | optional   |

## Koppeling aan tekst (later / mapping-laag)

| Feature                         | Waargenomen                         | Nodig in template-taal              | Status     |
| ------------------------------- | ----------------------------------- | ----------------------------------- | ---------- |
| Syllaben op recite              | n lettersgrepen op breve            | mapping, niet in core pitch-list    | open       |
| Anker ↔ klemtoon                | `l. st.` op laatste streek          | mapping-hypotheses                  | open       |
| Split/merge van noten           | ½↔2×¼ bij te veel/weinig tekst      | mapping of auteur in VSA            | open       |

## Expliciet niet uit AI-pitches

Absolute toonhoogtes horen niet in event-pitches; gebruik `do`/`mode` + graden.
Openingsakkoord tropaar toon 4 (menselijk): S=`mi`, A=`do`, T=`sol-1`, B=`do-1`
bij `do: F4` (T-octaaf nog te bevestigen).
