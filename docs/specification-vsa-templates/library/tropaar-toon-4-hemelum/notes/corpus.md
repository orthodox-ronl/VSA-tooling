# Corpus: tropaarteksten Toon 4 ↔ template `tropaar-toon-4-hemelum`

Niet-normatief onderzoeksdossier.

- Bronteksten: [`docs/plans/onderzoeks-troparen-en-kondaken.md`](../../../../plans/onderzoeks-troparen-en-kondaken.md)
  (sectie Toon 4; `*` = één [template-frase](@) per regel).
- Template: [`../template.yaml`](../template.yaml).
- Mappingcontract: [`../../../mapping-vsa.md`](../../../mapping-vsa.md) (**VSA→template-instance**).
- Detail Elia: [`elia-mapping.md`](elia-mapping.md).

## Wat we hier aan het doen zijn

**Doel van het grotere project:** uit een VSA-tropaar (melodiestem S) + een
toonformule-template SATB MusicXML maken. De PDF/PNG van het toonboek is alleen
nodig om die **template** te schrijven (alle mogelijke formule-slots voor
tropaar in toon X), niet om pitches uit een scan te “raden”.

**VSA→template-instance (besloten):**

| Stem  | Bron van de melodie                          |
| ----- | -------------------------------------------- |
| S     | VSA + [do-context](@)                        |
| A/T/B | template (harmonie/formule), meelopend met S |

Dus: als VSA voor S een optionele noot meeneemt, of een halve noot splitst /
twee gelijke noten tot één duur merget, dan gebeurt **hetzelfde ritmische
besluit** voor A, T en B via de corresponderende template-events.

**Wat dit corpus oplevert:** voor elk van de 13 stukken
`examples/corpus/` — `.vsa` (bron) + `.mscz` /
`.mxl` (uitgewerkt SATB, instance). PDF is lokale MuseScore-export (niet in git).

**Wat het corpus al toont:** op 13 Toon-4-troparen werkt
“één regel = één frase” + cycle `1,2,1,2,…` + slot `laatste` zonder conflict;
de render-pipeline zet A/T/B synchroon mee. Laddergraden in de YAML blijven
`provisional` (pitch-audit open).

## Toewijzingsregel (cycle)

Template: `cycle: ["1", "2"]`, `final: laatste` — equivalent aan
[`text_mapping`](../../../mapping-vsa.md) met `repeat until final`.

Voor een tekst met **n** regels (frasen):

1. Regels `1 .. n−1` lopen **cyclisch** door de cycle (`1`, `2`, `1`, `2`, …).
2. Regel `n` → `laatste`.
3. **Geen** eis dat `n−1` een veelvoud van `len(cycle)` is.

Implementatie: `assign_stanzas_to_phrases()` in
[`src/vsa/template_mapping.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/template_mapping.py).

Uitgebreidere bladen (prefix, embedded cycle, meerdere plannen): zie
[mapping-vsa.md](../../../mapping-vsa.md).

| n regels | Cycle-deel (regels 1..n−1) | Slot      |
| -------- | -------------------------- | --------- |
| 5        | `1 2 1 2`                  | `laatste` |
| 6        | `1 2 1 2 1`                | `laatste` |
| 7        | `1 2 1 2 1 2`              | `laatste` |
| 9        | `1 2 1 2 1 2 1 2`          | `laatste` |

**Patrooncheck (H3):** oneven regels starten vaak zonder `{/…}` (frase `1`);
even regels vaak met `{/…}` (frase `2`, kandidaat `e.st.`). Afwijkingen
staan bij het stuk.

---

## Overzicht corpus

| Id     | Stuk (kort)                       | Regels | Toewijzing                | `**` | Opmerking                           |
| ------ | --------------------------------- | ------ | ------------------------- | ---- | ----------------------------------- |
| T4-01  | Geboorte Johannes Voorloper       | 6      | `1 2 1 2 1` + `laatste`   | nee  | `*` toegevoegd; regels samengevoegd |
| T4-02  | Johannes Shanghai/SF              | 7      | `1 2 1 2 1 2` + `laatste` | nee  |                                     |
| T4-03  | HH. Martelaren                    | 6      | `1 2 1 2 1` + `laatste`   | ja   | `.*` → ` *`                         |
| T4-04  | Mantel Moeder Gods                | 9      | `1 2 … 1 2` + `laatste`   | ja   | langste cycle                       |
| T4-05  | H. Marina                         | 7      | `1 2 1 2 1 2` + `laatste` | ja   |                                     |
| T4-06  | Profeet Elia                      | 7      | `1 2 1 2 1 2` + `laatste` | nee  | baseline walkthrough                |
| T4-07  | Geboorte Moeder Gods              | 7      | `1 2 1 2 1 2` + `laatste` | nee  | feesteigen                          |
| T4-07a | Geboorte Moeder Gods (Liturgikon) | 7      | `1 2 1 2 1 2` + `laatste` | nee  | Liturgikon-variant                  |
| T4-08  | Tempelgang (begin welbehagen)     | 7      | `1 2 1 2 1 2` + `laatste` | nee  | korte regel 6                       |
| T4-09  | Tempelgang (alreine Tempel)       | 7      | `1 2 1 2 1 2` + `laatste` | nee  |                                     |
| T4-10  | Apostel Andreas                   | 5      | `1 2 1 2` + `laatste`     | nee  | kortste                             |
| T4-11  | Nicolaas van Myra                 | 7      | `1 2 1 2 1 2` + `laatste` | nee  | parallel met T4-02                  |
| T4-12  | Engelen (Maandag)                 | 7      | `1 2 1 2 1 2` + `laatste` | nee  | Liturgikon                          |

Alle stukken: genre **tropaar**, toon **4**, mapping naar
`tropaar-toon-4-hemelum` (`pitches_status: provisional`).

---

## T4-01 — Geboorte Johannes Voorloper

```text
[//:] Profeet en Voorloper van {Chris_}{/tus_} {\komst_}, *
{/wij} zijn niet in staat u naar waarde te {lo_.}{\ven_} *
die wij met liefde ver{-&/e_&_}{\ren_}. *
{/Want} de onvruchtbaarheid … opge{he_.}{\ven_} *
door uw roemrijke … Ge{-&/boor_&_}{\te_}. *
// Toen werd de Vleeswording … ver{-&\kon_&_}{/digd_}. [//:]
```

| Regel | Tekst (kort)                              | Frase     | H3 (`{/` start) |
| ----- | ----------------------------------------- | --------- | --------------- |
| 1     | Profeet en Voorloper … komst              | `1`       | nee             |
| 2     | wij zijn niet in staat … loven            | `2`       | ja              |
| 3     | die wij met liefde vereren                | `1`       | nee             |
| 4     | Want de onvruchtbaarheid … opgeheven      | `2`       | ja              |
| 5     | door uw … Geboorte                        | `1`       | nee             |
| 6     | Toen werd de Vleeswording … verkondigd    | `laatste` | nee (`//`)      |

---

## T4-02 — Johannes Shanghai / San Francisco

```text
[//:] Als een {Re_}gel {/van} ge{\loof} *
{/en} een voor-beeld … {\heid_} *
heeft de waar-heid … ge{\toond_}. *
{/Daar}om zijt gij … {\groot_}, *
en door ar-moe-de … {\den_}, *
{/Va}der … Jo{han_.}{\nes_}, *
// bid Chris-tus God … {-&\red_&_}{/den_}. [//:]
```

| Regel | Tekst (kort)                         | Frase     | H3    |
| ----- | ------------------------------------ | --------- | ----- |
| 1     | Als een Regel van geloof             | `1`       | nee   |
| 2     | en een voorbeeld … zachtmoedigheid   | `2`       | ja    |
| 3     | heeft de waarheid … getoond          | `1`       | nee   |
| 4     | Daarom zijt gij … groot              | `2`       | ja    |
| 5     | en door armoede rijk geworden        | `1`       | nee   |
| 6     | Vader … Johannes                     | `2`       | ja    |
| 7     | bid Christus God … te redden         | `laatste` | nee   |

---

## T4-03 — HH. Martelaren

```text
[//:] Uw marte{la_}{/ren}, o {\Heer_}, *
{/heb}ben … ont{van_}{\gen_}. *
Zij hebben … {\heugd_}, *
{/zo}dat … over{won_}{\nen_}, *
en de machteloze … {\schud_}. **
Verlos door hun gebeden … {/len_}. [//:]
```

| Regel | Tekst (kort)                              | Frase     | H3  | Extra        |
| ----- | ----------------------------------------- | --------- | --- | ------------ |
| 1     | Uw martelaren, o Heer                     | `1`       | nee |              |
| 2     | hebben … kroon ontvangen                  | `2`       | ja  |              |
| 3     | Zij hebben … verheugd                     | `1`       | nee |              |
| 4     | zodat … overwonnen                        | `2`       | ja  |              |
| 5     | en de machteloze … afgeschud              | `1`       | nee | daarna `**`  |
| 6     | Verlos door hun gebeden onze zielen       | `laatste` | nee |              |

**Spanning:** regel 1 heeft mid-frase scopes `{la_}{/ren}` — geen
`e.st.`-start; H3 geldt voor **regelstart**, niet mid-regel.

---

## T4-04 — Mantel Moeder Gods (Blachernae)

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Laat ons die vernederd zijn … zonden              | `1`       | nee |
| 2     | nu onze toevlucht … Moeder Gods                   | `2`       | ja  |
| 3     | en tot haar roepen … hart                         | `1`       | nee |
| 4     | o Koningin … help ons                             | `2`       | ja  |
| 5     | Haast u ons te hulp te komen                      | `1`       | nee |
| 6     | want wij zijn in gevaar                           | `2`       | ja  |
| 7     | door het grote aantal … overtredingen             | `1`       | nee |
| 8     | laat uw dienaren niet ledig … heengaan            | `2`       | ja  |
| 9     | want gij zijt onze enige hoop                     | `laatste` | nee |

`**` na regel 8. Goede stress-test: vier volledige `1`/`2`-paren vóór
`laatste`.

---

## T4-05 — H. Marina

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Uw heilige Marina … tot U                         | `1`       | nee |
| 2     | Mijn Bruidegom, U bemin ik                        | `2`       | ja  |
| 3     | en om U te zoeken … Doop                          | `1`       | nee |
| 4     | Ik lijd … heersen mag met U                       | `2`       | ja  |
| 5     | ik sterf voor U … te leven                        | `1`       | nee |
| 6     | aanvaard mij als gift … geofferd                  | `2`       | ja  |
| 7     | Door haar gebeden … onze zielen                   | `laatste` | nee |

---

## T4-06 — Profeet Elia

| Regel | Tekst (kort)                         | Frase     | H3  |
| ----- | ------------------------------------ | --------- | --- |
| 1     | Gij waart een Engel in het vlees     | `1`       | nee |
| 2     | de grondslag der profeten            | `2`       | ja  |
| 3     | en de tweede Voorloper … komst       | `1`       | nee |
| 4     | roemrijke Elia                       | `2`       | ja  |
| 5     | Gij hebt … Elisa                     | `1`       | nee |
| 6     | gij verjaagt … melatsen              | `2`       | ja  |
| 7     | en doet zo ook … vereren             | `laatste` | nee |

Zie [`elia-mapping.md`](elia-mapping.md) voor event-niveau
(H1/H2/H4/H5).

---

## T4-07 — Geboorte Moeder Gods

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Uw Geboorte, o Moeder Gods                        | `1`       | nee |
| 2     | heeft de Vreugde … wereld                         | `2`       | ja  |
| 3     | Want uit U … onze God                             | `1`       | nee |
| 4     | Hij heeft ons … bevrijd                           | `2`       | ja  |
| 5     | en schenkt ons Zijn zegen                         | `1`       | nee |
| 6     | Hij heeft de dood teniet gedaan                   | `2`       | ja  |
| 7     | en Hij verleent ons het eeuwige Leven             | `laatste` | nee |

---

## T4-08 — Tempelgang Moeder Gods (begin welbehagen)

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Heden is het begin … welbehagen                   | `1`       | nee |
| 2     | de voorbereidende Verkondiging … mensen           | `2`       | ja  |
| 3     | De Maagd komt in de Tempel Gods                   | `1`       | nee |
| 4     | en verkondigt … de Christus                       | `2`       | ja  |
| 5     | Tot haar willen ook wij … roepen                  | `1`       | nee |
| 6     | Verheug U                                         | `2`       | ja  |
| 7     | Vervulling van het Heilsplan … Schepper           | `laatste` | nee |

**Spanning:** regel 6 is zeer kort (`{/Ver}{heug__} {\U_}`) — toetst of
frase `2` (recite + cadens) met weinig syllaben nog zinvol is (H5
split/merge / optionals).

---

## T4-09 — Tempelgang Moeder Gods (alreine Tempel)

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | De alreine Tempel van de Verlosser                | `1`       | nee |
| 2     | het kostelijk … Bruidsvertrek                     | `2`       | ja  |
| 3     | de geheiligde Schatkamer … heerlijkheid           | `1`       | nee |
| 4     | wordt heden … Huis des Heren                      | `2`       | ja  |
| 5     | Zij brengt daar … Heilige Geest                   | `1`       | nee |
| 6     | terwijl Zijn Engelen zingen                       | `2`       | ja  |
| 7     | Zie, daar is de hemelse woontent                  | `laatste` | nee |

---

## T4-10 — Apostel Andreas

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Gij zijt de Eerstgeroepene der Apostelen          | `1`       | nee |
| 2     | en de broeder van Petros                          | `2`       | ja  |
| 3     | Bid daarom … Meester van het heelal               | `1`       | nee |
| 4     | om aan de wereld vrede te schenken                | `2`       | ja  |
| 5     | en aan onze zielen de grote genade                | `laatste` | nee |

Kortste cycle: twee `1`/`2`-paren + `laatste`.

---

## T4-11 — Nicolaas van Myra

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Als de Regel des geloofs                          | `1`       | nee |
| 2     | en het voorbeeld der zachtmoedigheid              | `2`       | ja  |
| 3     | heeft de waarheid … getoond                       | `1`       | nee |
| 4     | Daarom zijt gij … groot                           | `2`       | ja  |
| 5     | en door armoede rijk geworden                     | `1`       | nee |
| 6     | Vader … Nikolaas                                  | `2`       | ja  |
| 7     | bid Christus God … te redden                      | `laatste` | nee |

Structureel parallel aan T4-02 (zelfde tropaarformule, andere heilige).

---

## T4-12 — Engelen (Maandag, Liturgikon)

| Regel | Tekst (kort)                                      | Frase     | H3  |
| ----- | ------------------------------------------------- | --------- | --- |
| 1     | Gij Aanvoerders der hemelse Heerscharen           | `1`       | nee |
| 2     | wij onwaardigen bidden tot u                      | `2`       | ja  |
| 3     | dat gij ons beschermt door uw gebeden             | `1`       | nee |
| 4     | en ons beschut … vleugelen                        | `2`       | ja  |
| 5     | Behoed ons … heerlijkheid                         | `1`       | nee |
| 6     | nu wij nedervallen en tot u roepen                | `2`       | ja  |
| 7     | redt ons uit de gevaren … hoge                    | `laatste` | nee |

---

## Corpusbevindingen (voorlopig)

| Bevinding                        | Status     | Toelichting                                                   |
| -------------------------------- | ---------- | ------------------------------------------------------------- |
| Cycle-toewijzing 1-regel-1-frase | houdbaar   | Op alle 13 stukken toepasbaar zonder conflict                 |
| H3 (`{/` ≈ start frase `2`)      | sterk      | Geen tegenvoorbeeld op regelstart in dit corpus               |
| `**` ≈ overgang naar `laatste`   | consistent | T4-03/04/05; slotregel blijft `laatste`                       |
| Korte frase `2` (T4-08 r6)       | open       | H5 / optional events nog te toetsen                           |
| Mid-regel scopes ≠ H3            | feit       | T4-03 r1; H3 alleen op frase-start                            |
| Instance (S uit VSA)                | besloten   | Pipeline in `examples/corpus/` (`.vsa`/`.mscz`/`.mxl`)        |

## Volgende toetsstappen

1. Event-niveau dieper op 2–3 stukken (Martelaren, Engelen, Mantel) —
   H4/H5 (optional + split parallel op A/T/B).
2. T4-08 regel 6 als edge-case voor korte frase `2`.
3. Pitch-audit `template.yaml` → `verified` (template-inhoud, los van
   runtime-S).
