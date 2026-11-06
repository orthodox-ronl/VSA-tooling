# Walkthrough: Tropaar Profeet Elia (toon 4) ↔ template `tropaar-toon-4`

Niet-normatief onderzoeksdossier. Hypotheses: H1–H7 in
[`../../../mapping-vsa.md`](../../../mapping-vsa.md) (**VSA→template-instance**). Corpus:
[`corpus.md`](corpus.md). VSA:
[`../examples/corpus/T4-06-profeet-elia.vsa`](../examples/corpus/T4-06-profeet-elia.vsa).

**In één zin (deze toets):** gegeven template + Elia-VSA voor S, kunnen A/T/B
synchroon meelopen — en levert dat een geloofwaardige SATB-MusicXML op?

## VSA-bron

```text
[//:] Gij waart een {En_}gel {/in} het {\vlees_} *
{/de} grondslag der pro{fe_}{\ten_} *
en de tweede Voorloper van {Chris_}{/tus_} {\komst_}, *
{/roem}rijke E{li_}{\a_} *
Gij hebt uit den hoge uw geest gezonden op E{-&/li_&_}{\sa_} *
{/gij} verjaagt ziekten en reinigt me{laat_}{\sen_}: *
en doet zo ook genezing opwellen voor allen die u ver{-&\e_&_}{/ren_} [//:]
```

`do: F4`, `mode: major` → `[//:]` start op **mi** (= A4).

## Frase-toewijzing (cycle)

Template: `cycle: [1, 2]`, `final: laatste` → 7 regels:

| Regel | Tekst (kort)                     | Frase     |
| ----- | -------------------------------- | --------- |
| 1     | Gij waart een Engel in het vlees | `1`       |
| 2     | de grondslag der profeten        | `2`       |
| 3     | en de tweede Voorloper … komst   | `1`       |
| 4     | roemrijke Elia                   | `2`       |
| 5     | Gij hebt … Elisa                 | `1`       |
| 6     | gij verjaagt … melatsen          | `2`       |
| 7     | en doet zo ook … vereren         | `laatste` |

---

## Regel 1 ↔ frase `1` (instance-toets)

### S uit VSA (feit, parser)

`[//:] Gij waart een {En_}gel {/in} het {\vlees_}`

| Syllabe | S-pitch  | Duur   |
| ------- | -------- | ------ |
| Gij     | A4 (mi)  | kwart  |
| waart   | A4       | kwart  |
| een     | A4       | kwart  |
| En      | A4       | half   |
| gel     | A4       | kwart  |
| in      | Bb4 (fa) | kwart  |
| het     | Bb4      | kwart  |
| vlees   | A4 (mi)  | half   |

### Template-events frase `1` (referentie)

| #   | Role    | ELM | Anker   | S (template) | A     | T      | B      |
| --- | ------- | --- | ------- | ------------ | ----- | ------ | ------ |
| 1   | open    | `~` | —       | mi           | do    | sol-1  | do-1   |
| 2   | recite  | `~` | —       | mi           | do    | sol-1  | do-1   |
| 3   | cadence | `~` | —       | mi           | do    | sol-1  | la-2   |
| 4   | cadence | `_` | `l.st.` | fa           | re    | re-1   | re-2   |
| 5   | cadence | `_` | —       | mi           | do    | do-1   | do-1   |
| 6   | cadence | `_` | —       | `#re`        | ti-1  | ti-2   | ti-3   |

### Slot-koppeling (hypothese → werkafspraak voor dit bewijs)

| Syllabe | S (VSA)     | Template-slot                          | A/T/B-akkoord                         | Regel   |
| ------- | ----------- | -------------------------------------- | ------------------------------------- | ------- |
| Gij     | mi kwart    | recite (#2; open #1 opgeslokt)         | do / sol-1 / do-1                     | H1      |
| waart   | mi kwart    | recite (herhaal)                       | idem                                  | H1      |
| een     | mi kwart    | recite (herhaal)                       | idem                                  | H1      |
| En      | mi half     | cadence-pre (#3); duur uit VSA         | do / sol-1 / **la-2**                 | H5      |
| gel     | mi kwart    | zelfde slot #3 (aanhouden)             | idem                                  | H5      |
| in      | fa kwart    | `l.st.` (#4); half→kwart (H5)          | re / re-1 / re-2                      | H2      |
| het     | fa kwart    | **geen nieuw slot**: #4 aanhouden      | idem                                  | *nieuw* |
| vlees   | mi half     | cadence (#5); slot #6 (`#re`) **over** | do / do-1 / do-1                      | H5      |

**In één zin:** A/T/B kunnen synchroon met S — door template-slots te herhalen
als S op dezelfde graad blijft, en trailing slots over te slaan als S ze niet
aandoet.

### Spanningen (eerlijk)

1. Template-S na `l.st.` wil `fa → mi → #re`; VSA-S doet `fa → fa → mi`. Onder
   instance: VSA wint; slot `#re` blijft ongebruikt in dit voorbeeld.
2. Basswisseling recite (`do-1`) → pre-cadens (`la-2`) op `En` is een
   **interpretatie** (welk moment B beweegt); PDF-audit kan dat bijstellen.
3. Alle template-graden blijven `provisional`.

### MusicXML-bewijs

Automatische pipeline (alle 7 regels):
[`../examples/corpus/T4-06-profeet-elia.mscz`](../examples/corpus/T4-06-profeet-elia.mscz)
/
[`../examples/corpus/T4-06-profeet-elia.mxl`](../examples/corpus/T4-06-profeet-elia.mxl).

- Vier partijen S/A/T/B (MXL); MuseScore-MSCZ: SA/TB-chords.
- Lyrics op alle stemmen; pitches `provisional`.

---

## Regel 2 ↔ frase `2` (nog hypothese)

| Syllaben          | Event-role | Anker          | Opmerking                                                         |
| ----------------- | ---------- | -------------- | ----------------------------------------------------------------- |
| *(geen)*          | link       | —              | `optional: true` overgeslagen (H4)                                |
| de                | cadence    | `e.st.`        | VSA `{/de}` — H3                                                  |
| grondslag der pro | recite     | —              | H1                                                                |
| fe / ten          | cadence    | `l.st.` + slot | VSA 2 scopes vs template-cadens → H5 split/merge (parallel A/T/B) |

Regel 2 zit in de automatische MSCZ (optional link overgeslagen, `{/de}` = `e.st.`).

## Bevinding

| Vraag                                         | Antwoord                                                       |
| --------------------------------------------- | -------------------------------------------------------------- |
| Kunnen A/T/B synchroon met Elia-S (regel 1)?  | **Ja**, met hold/skip-regels hierboven                         |
| Is de template-cadens 1:1 met VSA-S?          | **Nee** (geen `#re`; extra `fa` op `het`)                      |
| Is dit productie-MXL?                         | **Nee** — pitches blijven `provisional`; wel automatische MSCZ |

## Volgende

1. Menselijke pitch-audit van frase `1` tegen PDF (vooral B op pre-cadens en
   of `#re` ooit verplicht is).
2. Event-niveau op overige corpusstukken (zie [`corpus.md`](corpus.md)).
