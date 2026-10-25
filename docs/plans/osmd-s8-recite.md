# OSMD-schermketen voor S8-recite (plan)

| Veld            | Waarde                                                                                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Status**      | **afgerond** (runs 0–4): A1-marker + OSMD-adapter; S8-SVG-bypass weg; CI groen                                                                                                                   |
| **Doel**        | Scherm toont S8-recite via OSMD + from-ir; bibliotheek mag `.mvsa.svg` missen voor `.mvsa` + from-ir                                                                                             |
| **Referentie**  | Catalogus `alleluia/9a-toon-8/groningen` — sibling `.mvsa.svg` vs gewenste OSMD-look                                                                                                             |
| **Context**     | Start: tooling tempo/S8 in from-ir; bibliotheek had tijdelijke SVG-bypass. Eind: A1 marker + adapter, bypass weg.                                                                                |
| **Gerelateerd** | [contract-index](../formats/contract-index.md), [partituur-ir](partituur-ir.md) §4.4/§7, [canonical-checklists S8](../formats/canonical-checklists.md), bibliotheek `schermpartituur.md` §2/§5.1 |

---

## 0. Antwoord eerst

**Probleem (opgelost):** from-ir zet S8-spacers als MusicXML
`<notehead>none</notehead>`. MuseScore snapt dat; OSMD/VexFlow niet.
Oplossing **A1:** die tag is een stabiele **marker**; de bibliotheek-OSMD-
adapter (`score-osmd.js`) verbergt spacer-koppen; geen `.mvsa.svg`-bypass
meer. CI: `s8-alleluia-hide-check.mjs`.

**Eindbeeld (Alleluia 9a toon 8 Groningen, S8-recite):** Al = kwart → le =
breve (stokloos) → middenlettergrepen = **alleen tekst** (geen koppen, geen
streepjes) → 3e «al» = kwart → cadens. Zelfde informatiedichtheid als de
sibling `.mvsa.svg`; pixel-perfecte MuseScore-pariteit is geen eis.

**Architectuur (vast):** **één from-ir = OSMD-profiel (A)** + **A1** —
marker in tooling, adapter + CI in bibliotheek. Score-IR blijft
`print.spacer` / `print.breveHead`.

---

## 1. Les uit de tijdelijke keten

| Wat we probeerden                                | Waarom het niet structureel is                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| MuseScore-semantiek in from-ir (`notehead none`) | OSMD/VexFlow tekent die printlaag niet zoals MuseScore                   |
| JS-hide na render (bibliotheek)                  | Breekbaar, moeilijk te testen, blijft MuseScore-XML misbruiken           |
| Scherm = `.mvsa.svg` bij S8                      | Was tijdelijke bypass; **weg** na groene A1-adapter                      |

**Afspraak:** print/blad blijft MuseScore (`mvsa svg` / MSCZ). Scherm =
Score-IR → from-ir → OSMD + A1-adapter (S8).

---

## 2. Architectuurkeuze

### 2.1 Drie opties

| Optie                                      | Idee                                                            | Voor                                                                            | Tegen                                                                                                                |
| ------------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **A. from-ir = OSMD-profiel** (aanbevolen) | Zelfde sibling; andere S8-MusicXML-mapping die OSMD eert        | Geen extra artifact; from-ir was al OSMD-kanaal; bibliotheek-fallback verdwijnt | Huidige tests die `notehead none` eisen moeten mee                                                                   |
| **B. `print-object` op noot/kop**          | Spacers met MusicXML `print-object` i.p.v. `notehead none`      | Standaard MusicXML                                                              | Op **hele** `<note>` verdwijnen lyrics (bekend S8/R3-risico); OSMD-gedrag per attribuut onzeker — peilen vóór kiezen |
| **C. Sibling XML**                         | Bijv. `{stam}.mvsa.from-ir.osmd.musicxml` naast huidige from-ir | Oude from-ir onaangetast; A/B zonder catalogus-breuk                            | Derde product-artifact; publicatiecontrole + shortcode + docs groeien; dubbele waarheid                              |

### 2.2 Besluitkader + peiling (run 1 gedaan)

Spike: `examples/spikes/osmd-s8-peiling/` in de repo (geen MkDocs-pagina;
alleen lokaal/peiling). OSMD **1.9.3**, zelfde lijn als bibliotheek-scherm;
geen post-render JS.
Patroon: Al (kwart) → le (breve) → lu/i/a (spacers) → al (kwart).

| Variant                    | Encoding                                              | Spacer-koppen in OSMD | Lyrics Al…al |
| -------------------------- | ----------------------------------------------------- | --------------------- | ------------ |
| `01-notehead-none`         | Huidige from-ir: `stem none` + `notehead none`        | **zichtbaar** (3/3)   | compleet     |
| `02-print-object-note`     | `print-object="no"` op hele `<note>`                  | **zichtbaar** (3/3)   | compleet     |
| `03-print-object-notehead` | `<notehead print-object="no">normal</notehead>`       | **zichtbaar** (3/3)   | compleet     |
| `04-stemless-normal-head`  | Controle: alleen `stem none`                          | **zichtbaar** (3/3)   | compleet     |
| `05-rest-with-lyric`       | `<rest/>` + lyric (structureel alternatief)           | rust-glyph (erger)    | compleet     |

Meting: per `g.vf-stavenote` de bbox-oppervlakte van `.vf-notehead`; spacer-
slots met oppervlakte ≫ 0 = zichtbare kop. Samenvatting:
`examples/spikes/osmd-s8-peiling/out/peiling-summary.json` (lokaal na
`npm run probe`; `out/` staat in `.gitignore`).

#### Besluit (run 1)

1. **B afgewezen** als from-ir-emit: OSMD eert `print-object` hier niet om
   koppen te verbergen; lyrics blijven wél (anders dan MuseScore-PDF bij
   `print-object=no` op de hele noot).
2. **`notehead none` alleen is geen OSMD-printlaag:** variant 01 tekent
   dezelfde zichtbare spacer-koppen als normale stemloze koppen (04).
3. **C niet nodig** om attr-redenen: een tweede sibling-XML met dezelfde
   visibility-trucs helpt OSMD niet.
4. **A blijft de architectuur** (één `{stam}.mvsa.from-ir.musicxml`), maar
   “OSMD-vriendelijke mapping” is **geen** MusicXML-visibility-attribuut.
   Run 2 koos **A1** (marker + adapter).

#### Besluit (run 2): **A1 gekozen**

| Id     | Status      | Strategie                                                                                                                                     |
| ------ | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **A1** | **gekozen** | Stabiele spacer-**marker** in from-ir (`stem none` + `notehead none`, lyrics op de noot) + gespecificeerde OSMD-adapter in bibliotheek + CI   |
| A2     | afgewezen   | Andere partituurvorm — niet nodig zolang A1 het eindbeeld haalt                                                                               |
| A3     | afgewezen   | Headless scherm-SVG i.p.v. live OSMD                                                                                                          |

**Tooling (deze run):** from-ir-emit ongewijzigd qua tags; docs +
`test_from_ir_s8_emits_spacer_noteheads` vastleggen A1-marker (lyric blijft;
geen `print-object=no` op spacer-`<note>`).

**Bibliotheek (run 3, gedaan):** adapter = productgedrag; SVG-bypass weg.

**Non-goals:** tweede Score-IR; Coria-playback wijzigen; MuseScore-partituur-MXL
(S8 spacers in MSCZ) herschrijven; pixel-match SVG↔OSMD.

### 2.3 Score-IR blijft stabiel

```text
.mvsa → Score-IR (print.spacer / breveHead) → from-ir MusicXML → OSMD + A1-adapter
```

- IR-velden `print.spacer` / `print.breveHead` / `stemless` blijven.
- from-ir spacer-marker: `stem none` + `notehead none` + lyric; OSMD alleen
  tekent de eindvorm ná de scherm-adapter.
- MuseScore-keten (partituur-MXL → MSCZ → `mvsa svg`) blijft S8/R3 zoals nu.

---

## 3. Scope: tooling vs bibliotheek

| Repo            | Doet                                                                                                                                                                                             | Doet niet in dit plan                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| **VSA-tooling** | Peiling + from-ir S8-emit; unit/contract-tests; man-pagina / format-hub / checklist-noot; spike of fixture tegen OSMD waar nuttig                                                                | Bibliotheek-templates; catalogus-regen van alle siblings |
| **bibliotheek** | **Gedaan:** SVG-bypass weg; A1-adapter + CI; `schermpartituur` §2/§5.1                                                                                                                           | Eigen MusicXML-herschrijf; tweede schermmotor            |

**Volgorde (afgerond):** tooling marker-contract → bibliotheek adapter +
“from-ir wint altijd bij `.mvsa`” (ook S8).

---

## 4. Acceptatiecriteria (product)

Voor `alleluia/9a-toon-8/groningen` op het scherm met alleen
`.mvsa` + `.from-ir.musicxml` (geen `.mvsa.svg` nodig voor S8):

1. OSMD toont de S8-recite-vorm: kwart → breve → midden **alleen tekst** →
   kwart → cadens (informatiedichtheid zoals sibling `.mvsa.svg`).
2. Geen zichtbare “lege” nootkoppen of stokjes op spacer-posities.
3. Lyrics van middenlettergrepen blijven leesbaar.
4. Speelplan-nav / andere §4-schermeisen blijven (geen regressie).
5. Publicatiecontrole / koormap: from-ir zonder verplichte `.mvsa.svg` voor
   dit stuk.

---

## 5. Tests

### 5.1 VSA-tooling (A1 — gedaan in run 2)

| Laag     | Wat                                                                                                                             |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Contract | `test_from_ir_s8_emits_spacer_noteheads`: spacer = `stem none` + `notehead none` + lyric; geen `print-object=no` op spacer-note |
| Docs     | `score-ir.md`, checklist S8, `mvsa score-ir`, `partituur-ir` §4.4 — A1-marker expliciet                                         |

### 5.2 Bibliotheek (run 3)

| Laag       | Wat                                                                              |
| ---------- | -------------------------------------------------------------------------------- |
| Spec       | `schermpartituur.md`: SVG-bypass §2/§5.1 weg; adapter = A1-productgedrag         |
| Steekproef | Catalogusblad + koormap-slot Alleluia 9a-8 zonder verplichte `.mvsa.svg`         |
| CI         | `s8-alleluia-hide-check`: houden/hernoemen als adapter-assert (niet “geen hide”) |

---

## 6. Gefaseerde runs (opdrachtregels)

Elke run = **één** mijlpaal. Geen “doe alles”. Plak de opdrachtregel in een
nieuwe chat (juiste repo-root).

### Run 0 — dit document (klaar bij merge van dit plan)

```text
Alleen plan docs/plans/osmd-s8-recite.md (+ README/nav). Geen code.
```

### Run 1 — peiling (VSA-tooling, geen product-emit)

**Waarom duur als je meteen emit herschrijft:** OSMD-gedrag per MusicXML-truc
is empirisch; verkeerde keuze = herstel-loop.

```text
Repo: VSA-tooling.
Alleen peiling S8→OSMD: 2–4 MusicXML-varianten (o.a. notehead none vs
print-object-op-kop vs lyric-drager zonder kop) in spike/browser of minimale
fixture. Schrijf uitslag + aanbevolen mapping in docs/plans/osmd-s8-recite.md
§2 (Besluit). Geen wijziging product-from-ir, geen bibliotheek.
```

### Run 2 — A1 marker-contract (VSA-tooling) — **gedaan**

```text
Repo: VSA-tooling.
Alleen A1: marker-contract in docs/tests; from-ir houdt notehead none.
Geen bibliotheek-bypass-verwijdering.
```

### Run 3 — bibliotheek schermketen — **gedaan**

SVG-bypass weg; A1-adapter (DOM-stemrijen) + `s8-alleluia-hide-check` in
`check`/Pages-CI; `schermpartituur` §2/§5.1.

### Run 4 — docs/norm afronden — **gedaan**

Plan-status + cross-links; S8-schermgap gesloten.

**Goedkoper formuleren:** zeg expliciet *«alleen run N — …»*.

---

## 7. Docs (wat wanneer)

| Wanneer | Document                                                                                                                            | Actie                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Run 0   | `docs/plans/osmd-s8-recite.md`, `plans/README.md`, mkdocs-nav                                                                       | Plan + vindbaarheid              |
| Run 1   | Dit plan §2 Besluit                                                                                                                 | Empirische keuze vastleggen      |
| Run 2   | `docs/formats/score-ir.md`, checklist S8-zin over from-ir, `docs/reference/cli/mvsa.md` (from-ir), eventueel `partituur-ir.md` §4.4 | Emit-contract synchroon met code |
| Run 3   | bibliotheek `schermpartituur` §2/§5.1 + adapter/CI                                                                                  | SVG-bypass eruit; A1 norm        |
| Run 4   | Dit plan + [kale-muziek](kale-muziek-svg-en-uitgaven.md) / [partituur-ir](partituur-ir.md)                                          | Gap-status gesloten              |

Terminologie: `zangstuk-id` → `variant-id` → `uitvoeringsvorm-id` →
`representatie-id`; geen ad-hoc “scherm-IR”.

---

## 8. Risico’s en open peilpunten

| Risico                                               | Mitigatie                                                                 |
| ---------------------------------------------------- | ------------------------------------------------------------------------- |
| OSMD eert geen MusicXML-visibility voor spacers      | Bevestigd in run 1; A1-adapter (gekozen) — geen B/C-attr                  |
| A1 “blijft JS-hack”                                  | Mitigated: marker-contract + schermpartituur §5.1 + CI (adapter = norm)   |
| Nav-/volta-regressie bij XML-wijziging               | Bestaande from-ir nav-tests + bibliotheek nav-check meenemen in run 2/3   |
| Verwarren MuseScore-MXL en from-ir                   | Docs: from-ir = scherm/OSMD; partituur-MXL/MSCZ = blad                    |
| Tempo/`<sound tempo>` recent                         | Niet terugdraaien; S8-pad orthogonaal houden                              |

**Geen open S8-schermgap meer.** Korte recite (`n < 6`) blijft ongewijzigd.
Verdere schermwerk (CoriB, cue-pariteit SVG↔OSMD) hoort elders — niet hier.

---

## 9. Succescheck

- [x] Architectuur A/B/C + aanbeveling
- [x] Scope tooling vs bibliotheek
- [x] Tests per repo
- [x] Gefaseerde runs met kopieerbare opdrachtregels
- [x] Docs-matrix
- [x] Run 1 peiling (B afgewezen; visibility-attrs werken niet in OSMD)
- [x] Run 2 A1 marker-contract (docs + tests)
- [x] Run 3 bibliotheek (bypass weg; adapter + CI)
- [x] Run 4 plan-status + cross-links
