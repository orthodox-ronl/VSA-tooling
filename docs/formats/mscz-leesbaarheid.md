# MSCZ-leesbaarheid (partituur-layout)

Doel: regels zodat een genormaliseerde / gegenereerde `.mscz` **op het blad
leesbaar** blijft — geen tekst in buurmaten, geen verwarrende bogen, geen
rommelige maatnummers. Dit is het layoutprofiel **`partituur`**
(`mvsa mscz --layout partituur`, default), toegepast via `mscz_partituur`.

Andere profielen: zie [`.mscz` — layoutprofielen](mscz.md#layoutprofielen---layout).
Ownership (wie kiest, wie handhaaft):
[reuse — ownership](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

Gerelateerd:

- [Canonieke checklists — MSCZ](canonical-checklists.md#checklist-mscz-partituur-musescore)
- [Template rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md)
- Oefenhoek (bron van A4/typografie):
  `VSA-demo/scripts/mscz-partituur-contract.md`

---

## Acceptatiecriterium

Bij review van `.mscz` / MuseScore-PDF:

1. Recite-tekst **raakt geen buurmaat** (noch vorige, noch volgende).
2. Lettergrepen overlappen elkaar niet en kruisen geen maatstreep zonder
   slur die dat bedoelt.
3. Geen stem-indicaties; lyrics tussen de balken (SA/TB).
4. Geen lege derde balk; G boven / F onder.
5. Geen frase-slurs die als melisma ogen.
6. Maatnummers alleen aan het begin van elk systeem.
7. Melisma: lyric-extender (streep) na de lettergreep op de eerste noot, plus
   melisma-boog (slur) over de noten van die lettergreep.
8. **Geen** accolade/bracket middenin een systeem (alleen bij systeembegin).
9. **Geen** leeg stuk notenbalk (spacermaat) of mid-systeem-HBox vóór een
   `@tekst`-cue; scheiding = dubbele streep + SystemText (of
   `@mscz-newline`).
10. Leidende `|:` maakt **geen** lege rustmaat; herhaalpunten (`:|`) blijven
    zichtbaar.
11. Alle `@tekst`-cues staan als SystemText (ook meerregelig met `...`).

---

## R — Recite-tekst (model A: spacers)

Bron: [rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md)
(één anker per lettergreep; onzichtbare kop, zichtbare lyric).

| #   | Regel                                                                                                                                                                                                                                                                                          |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | **Geen** lange joined lyric onder één recite-noot als die tekst breder is dan de noot/maat.                                                                                                                                                                                                    |
| R2  | Lange recite (`n ≥ 6`): **1–(n−2)–1** — eerste midden-lettergreep op `\|\|O\|\|`; overige midden-lettergrepen elk op een **spacer**.                                                                                                                                                           |
| R3  | Spacers: MuseScore ``visible=0`` **én** ``play=0`` op de nootkop (lyrics blijven); **niet** MusicXML `print-object="no"` op de hele `<note>` (verbergt lyrics in PDF). ``\|\|O\|\|`` = `headType` breve met metrische **randduur** (geen `durationType=breve` — die blaast de maatbreedte op). |
| R4  | **Geen** melisma-extender (`ticks`) of frase-slur onder recite-body.                                                                                                                                                                                                                           |
| R5  | Maatlengte = som van de noten (+ spacers); elke slot ≈ randduur zodat speelduur = `n ×` rand (= Coria). Spacers klinken niet (`play=0`); de ticks blijven voor de layout.                                                                                                                      |
| R6  | Kortere recite (`n < 6`): één zichtbare noot per lettergreep (geen collapse).                                                                                                                                                                                                                  |
| R7  | Melisma same-pitch: **I1** (MusicXML-partituur) — alleen ongestipte standaardduuren ≤ whole of tie-keten; nooit `type=breve` / gestipte sommen in MusicXML (MuseScore-importcorruptie). **I2** — lange holds als tie-keten i.p.v. heraangeslagen hakken. **MSCZ-postprocess** — die tie-ketens samentrekken tot **één compacte noot, inclusief gestipt** (leesbaar 3/4 i.p.v. 2/4+1/4); pure hold zonder slur. |

### Canonieke printvorm 1–(n−2)–1 (MSCZ)

Voor een recite-groep met **zes of meer** lettergrepen (`n ≥ 6`):

| Positie                       | Notatie                                                                                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Eerste lettergreep            | Zichtbare **randnoot** — duur = ELM na `)` (anders kwart)                                                                                                                                  |
| Midden (`n − 2` lettergrepen) | **Eén** stokloze `\|\|O\|\|`: MuseScore `headType` breve op een noot met **randduur** (quarter/half naar ELM); daarna spacers (`visible=0` + `play=0`) voor de overige midden-lettergrepen |
| Laatste lettergreep           | Zichtbare **randnoot** — zelfde duur als de eerste                                                                                                                                         |

Totale speelduur van de collapse = `n ×` randduur — gelijk aan Coria-playback
(één noot per lettergreep).

**Playback / Coria (``.mxl``):** **geen** recite-collapse (M10) — elke
lettergreep een klinkende noot. Same-pitch **melisma** wél samentrekken
(S13/R7), net als op het blad.

---

## L — Lyrics algemeen

| #   | Regel                                                                                                                                                                        |
| --  | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L1  | Eén lyric-laag onder de bovenste balk (tussen SA en TB).                                                                                                                     |
| L2  | Standaard gecentreerd op de nootkop; Source Sans 3, 13 pt (Style).                                                                                                           |
| L3  | Hyphen (`Va-der`) ≠ melisma.                                                                                                                                                 |
| L4  | Melisma: tekst op eerste noot; **lyric-extender** + **melisma-slur** (S2/S4). Geen extender onder recite (R4).                                                               |
| L5  | Maatbreedte volgt tekst; laatste systeem vol (`lastSystemFillLimit=0`).                                                                                                      |

---

## S — Slurs

| #   | Regel                                                                                                                    |
| --  | ------------------------------------------------------------------------------------------------                         |
| S1  | Capella-/import-frasebogen: standaard niet als melisma; weg of genegeerd bij normalisatie.                               |
| S2  | Melisma-slur alleen waar één lettergreep over meerdere noten hoort.                                                      |
| S3  | Geen decoratieve slurs over hele systemen.                                                                               |
| S4  | Echt melisma: **slur (S2) én** lyric-extender (L4). Geen frase-slur zonder melisma; geen slur + extender “voor de sier”. |

---

## M — Maten, nummers, sleutels, maatstrepen

| #   | Regel                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------------------------- |
| M1  | Maatnummers: eerste maat van elk systeem.                                                                                    |
| M2  | Eindmaatstreep per systeem zichtbaar.                                                                                        |
| M3  | Geen zichtbare maatsoort-getallen bij verborgen/`senza-misura`-TimeSig.                                                      |
| M4  | Twee balken SA/TB; G/F; geen partijnamen.                                                                                    |
| M5  | Geen lege derde balk.                                                                                                        |
| M6  | Sectie-einde (`\|\|` in `.mvsa`): dubbele maatstreep (`light-light`); slot = `light-heavy`.                                  |
| M7  | Stokken: S en T **omhoog** (voice 1); A en B **omlaag** (voice 2).                                                           |
| M8  | Melisma-print: same-pitch → compacte noot (MSCZ-postprocess) of tie-keten in MusicXML (S13 / R7); slur alleen bij toonwissels. |
| M9  | Leidende `\|:` → linker forward-repeat op eerste **inhoudsmaat**; geen lege rustmaat ervoor.                                 |
| M10 | `:\|` → backward-repeat met herhaalpunten; niet alleen `light-light` zonder dots.                                            |

---

## C — Cues, gaps, HBox, accolade

Contract: checklist MSCZ **S14–S19**. MuseScore-gedrag dat we vermijden:

| Foutbeeld                                    | Oorzaak (typisch)                                      | Canonieke vorm                                                 |
| -------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| Accolade middenin het systeem                | `HBox` tussen maten van hetzelfde systeem              | **Geen** mid-systeem-HBox (S14, S18)                           |
| Leeg stuk **met** notenbalklijnen vóór cue   | MusicXML-spacermaat / korte rust-only maat             | Spacermaat **weg**; scheiding = `\|\|` + SystemText (S15, S17) |
| Smalle lege maat bij systeembegin / na `\|:` | Leidende `\|:` als aparte lege maat geëxporteerd       | `start_bar` op eerste inhoudsmaat (S16, M9)                    |
| Cue alleen op één balk / verkeerde plaats    | `StaffText` i.p.v. `SystemText`; `<br/>` matcht niet   | Promote naar SystemText; match ook `<br/>` (S19)               |
| Herhaalpunten weg na mid-flow `@tekst`       | `:\|` “opgewaardeerd” naar `light-light` zonder repeat | `:\|` blijft `light-heavy` + backward (S16, M10)               |

| #   | Regel                                                                                                                                                                 |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | Mid-flow `@tekst` (niet begin van MuseScore-systeem): vorige maat **dubbele streep**, cue = **SystemText**. Geen HBox, geen spacermaat.                               |
| C2  | `@tekst` forceert **geen** systeembreuk; gebruik `@mscz-newline` voor een nieuwe regel op het blad.                                                                   |
| C3  | Korte rust-only / `print-object=no`-maten: **strippen** in MSCZ-postprocess; niet vervangen door mid-systeem-HBox.                                                    |
| C4  | Trailing HBox aan staff-eind (vóór `</Staff>` / colofon-VBox): weg.                                                                                                   |
| C5  | Accolade/bracket alleen bij systeembegin.                                                                                                                             |

---

## P — Pagina / systeem (A4)

| #   | Regel                                                                                        |
| --  | ----------------------------------------------------------------------                       |
| P1  | Papier A4 staand; marges 15 mm.                                                              |
| P2  | Geen inspring eerste systeem.                                                                |
| P3  | Verticaal: pagina niet vullen; `minSystemDistance`/`maxSystemDistance` vast (niet “spread”). |
| P4  | Systeembreuk op frase-/ademgrens, niet midden in recite.                                     |
| P5  | Titel/componist in VBox; `frameSystemDistance=14`; cues als **SystemText** (niet StaffText). |
| P6  | Copyright-footer + colofon: checklist PDF P4 (**later**).                                    |

---

## Wat de scripts nu zetten

| Onderdeel                                                                 | Waar                                                                         |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Recite playback = 1 noot / lettergreep                                    | `vsa.mvsa_musicxml` layout `playback`                                        |
| Recite partituur = 1–(n−2)–1; \|\|O\|\| + mute spacers                    | `mvsa_musicxml` + `mscz_partituur._apply_recite_print_conventions`           |
| a–g zonder cijfer = do-octaaf                                             | `pitch_resolver.pitch_in_do_octave` / `mvsa_musicxml._resolve_slot`          |
| Sectie-`\|\|` → `light-light`                                             | `vsa.mvsa_musicxml` (playback én partituur)                                  |
| Mid-flow `@tekst` → `\|\|` + SystemText (geen HBox)                       | `vsa.mvsa_musicxml` + `vsa.mscz_partituur` (S14–S15, S19)                    |
| Leidende `\|:` → `start_bar` (geen lege maat)                             | `vsa.mvsa_validate` / `mvsa_parse` / `mvsa_musicxml` (S16, M16)              |
| Korte rust-spacers strippen; trailing HBox weg                            | `vsa.mscz_partituur` (S17, C3–C4)                                            |
| Melisma collapse/tie-keten (I1+I2 in MusicXML)                            | `mvsa_musicxml._collapse_same_pitch_melisma` / `_pack_safe_divs`             |
| Melisma same-pitch → gestipte compacte noot (MSCZ)                        | `mscz_partituur._collapse_same_pitch_tie_runs`                               |
| Maat-`len` gelijk over staves; geen `durationType=breve`                  | `mscz_partituur._apply_recite_print_conventions` / `_recompute_measure_lens` |
| Stokken S/T↑ A/B↓ (voice 1/2 + backup)                                    | `vsa.mvsa_musicxml` `_emit_staff_voices`                                     |
| A4 + typografie + partijnamen uit + systeemafstanden                      | `vsa.mscz_partituur.apply_partituur_mscz_conventions`                        |
| SA/TB-akkoorden, lege part-namen                                          | partituur-layout in `mvsa_musicxml` / `musicxml_satb_layout`                 |
