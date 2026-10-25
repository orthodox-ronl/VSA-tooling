# OSMD-schermketen voor S8-recite (plan)

| Veld            | Waarde                                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Status**      | plan; **geen code** tot expliciete OK per run                                                                                                    |
| **Doel**        | Scherm toont S8-recite via OSMD + from-ir; bibliotheek mag `.mvsa.svg` missen voor `.mvsa` + from-ir                                             |
| **Referentie**  | Catalogus `alleluia/9a-toon-8/groningen` — sibling `.mvsa.svg` vs gewenste OSMD-look                                                             |
| **Context**     | Tooling `2f24bdc3d` (tempo/S8 in Score-IR/from-ir); bibliotheek `4c292ef76` (tijdelijk scherm = `.mvsa.svg` bij `<notehead>none</notehead>`)     |
| **Gerelateerd** | [contract-index](../formats/contract-index.md), [partituur-ir](partituur-ir.md) §4.4/§7, [canonical-checklists S8](../formats/canonical-checklists.md), bibliotheek `schermpartituur.md` §2/§5.1 |

---

## 0. Antwoord eerst

**Probleem:** from-ir zet S8-spacers als MusicXML `<notehead>none</notehead>`.
MuseScore snapt dat; OSMD/VexFlow niet. JS die koppen verhult is geen
structurele fix. De bibliotheek toont daarom tijdelijk `.mvsa.svg` zodra
from-ir `notehead none` bevat.

**Eindbeeld (Alleluia 9a toon 8 Groningen, S8-recite):** Al = kwart → le =
breve (stokloos) → middenlettergrepen = **alleen tekst** (geen koppen, geen
streepjes) → 3e «al» = kwart → cadens. Zelfde informatiedichtheid als de
sibling `.mvsa.svg`; pixel-perfecte MuseScore-pariteit is geen eis.

**Aanbevolen architectuur:** **één from-ir = OSMD-profiel** — de bestaande
sibling `{stam}.mvsa.from-ir.musicxml` krijgt een S8-emit die OSMD wél
tekent. Score-IR blijft `print.spacer` / `print.breveHead`. Geen derde
sibling-XML en geen site-JS als primaire oplossing.

---

## 1. Les uit de tijdelijke keten

| Wat we probeerden                                | Waarom het niet structureel is                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| MuseScore-semantiek in from-ir (`notehead none`) | OSMD/VexFlow tekent die printlaag niet zoals MuseScore                   |
| JS-hide na render (bibliotheek)                  | Breekbaar, moeilijk te testen, blijft MuseScore-XML misbruiken           |
| Scherm = `.mvsa.svg` bij S8                      | Werkt nu; blokkeert “from-ir genoeg voor scherm” en dwingt MuseScore-SVG |

**Afspraak:** print/blad blijft MuseScore (`mvsa svg` / MSCZ). Scherm blijft
Score-IR → from-ir → OSMD. S8-gap zit in de **from-ir-emit**, niet in de
site als eerste fixplaats.

---

## 2. Architectuurkeuze

### 2.1 Drie opties

| Optie                                      | Idee                                                            | Voor                                                                            | Tegen                                                                                                                |
| ------------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **A. from-ir = OSMD-profiel** (aanbevolen) | Zelfde sibling; andere S8-MusicXML-mapping die OSMD eert        | Geen extra artifact; from-ir was al OSMD-kanaal; bibliotheek-fallback verdwijnt | Huidige tests die `notehead none` eisen moeten mee                                                                   |
| **B. `print-object` op noot/kop**          | Spacers met MusicXML `print-object` i.p.v. `notehead none`      | Standaard MusicXML                                                              | Op **hele** `<note>` verdwijnen lyrics (bekend S8/R3-risico); OSMD-gedrag per attribuut onzeker — peilen vóór kiezen |
| **C. Sibling XML**                         | Bijv. `{stam}.mvsa.from-ir.osmd.musicxml` naast huidige from-ir | Oude from-ir onaangetast; A/B zonder catalogus-breuk                            | Derde product-artifact; publicatiecontrole + shortcode + docs groeien; dubbele waarheid                              |

### 2.2 Besluitkader (run 1 peilt, run 2 kiest definitief)

1. **Peil in spike** (één maat / Alleluia-fragment) welke MusicXML-vorm OSMD
   tekent als: alleen lyric zichtbaar, geen kop, geen stok, geen streepje —
   zonder post-render JS.
2. Als peiling **B** betrouwbaar maakt (lyrics blijven): mag B de emit van A
   zijn.
3. Alleen **C** als A de huidige from-ir-consumenten breekt (nav-CI,
   externe tools) én die niet in dezelfde tooling-run meegenomen kunnen.

**Non-goals:** tweede Score-IR; Coria-playback wijzigen; MuseScore-partituur-MXL
(S8 spacers in MSCZ) herschrijven; pixel-match SVG↔OSMD.

### 2.3 Score-IR blijft stabiel

```text
.mvsa → Score-IR (print.spacer / breveHead) → from-ir MusicXML → OSMD
```

- IR-velden `print.spacer` / `print.breveHead` / `stemless` blijven.
- Alleen de **MusicXML-mapping** van die velden voor from-ir verandert
  (OSMD-vriendelijk).
- MuseScore-keten (partituur-MXL → MSCZ → `mvsa svg`) blijft S8/R3 zoals nu.

---

## 3. Scope: tooling vs bibliotheek

| Repo            | Doet                                                                                                                                                                                             | Doet niet in dit plan                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| **VSA-tooling** | Peiling + from-ir S8-emit; unit/contract-tests; man-pagina / format-hub / checklist-noot; spike of fixture tegen OSMD waar nuttig                                                                | Bibliotheek-templates; catalogus-regen van alle siblings |
| **bibliotheek** | Ná groene tooling: temporary SVG-bypass voor `notehead none` **verwijderen**; `schermpartituur` §2/§5.1 bijwerken; steekproef Alleluia 9a-8; JS-hide/regressie-scripts opschonen of herbestemmen | Eigen MusicXML-herschrijf; tweede schermmotor            |

**Volgorde (hard):** eerst tooling emit + tests groen → dan bibliotheek
schermketen terug naar “from-ir wint altijd bij `.mvsa`”.

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

### 5.1 VSA-tooling (verplicht bij emit-wijziging)

| Laag              | Wat                                                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Unit              | from-ir XML: spacers/breve krijgen de **nieuwe** OSMD-mapping; geen regressie op non-S8                                                    |
| Contract          | Score-IR → from-ir blijft S8 1–(n−2)–1 in IR; alleen emit-tags wijzigen                                                                    |
| Fixture           | Mini-`.mvsa` of bestaande S8-fixture; assert op afwezigheid van misleidende tags (`notehead none` alleen als peiling dat nog nodig blijkt) |
| Handmatig / spike | Browser of bestaande `examples/spikes/partituur-browser/` op Alleluia-fragment                                                             |

Bestaande test `test_from_ir_s8_emits_spacer_noteheads` **herscrijven** naar
het gekozen OSMD-contract (niet stil laten falen).

### 5.2 Bibliotheek (ná tooling)

| Laag       | Wat                                                                 |
| ---------- | ------------------------------------------------------------------- |
| Spec       | `schermpartituur.md`: S8-uitzondering §2/§5.1 schrappen of “gedaan” |
| Steekproef | Catalogusblad + koormap-slot Alleluia 9a-8 zonder SVG-bypass        |
| CI | `s8-alleluia-hide-check` / JS-finalize: verwijderen of omzetten naar
  “geen hide nodig”-assert |

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

### Run 2 — from-ir emit + tests (VSA-tooling)

```text
Repo: VSA-tooling.
Stap: pas from-ir S8-mapping aan volgens osmd-s8-recite Besluit (run 1).
Unit/contract-tests bijwerken; docs synchroon (score-ir, checklist S8-noot,
mvsa man/CLI waar from-ir genoemd). Geen bibliotheek. Geen bulk-catalogus.
```

### Run 3 — bibliotheek schermketen (bibliotheek)

```text
Repo: bibliotheek (nieuwe chat / move-to-root).
Ná tooling met nieuwe from-ir: verwijder S8→.mvsa.svg-bypass in
bieb-score/schermpartituur; steekproef alleluia/9a-toon-8/groningen;
JS-hide/S8-check opschonen. Geen tooling-emit in deze run.
```

### Run 4 — docs/norm afronden (licht, beide of alleen links)

```text
Werk schermpartituur + tooling plan-status bij: S8-schermgap gesloten;
verwijs naar osmd-s8-recite. Geen nieuwe features.
```

**Goedkoper formuleren:** zeg expliciet *«alleen run N — …»*.

---

## 7. Docs (wat wanneer)

| Wanneer | Document                                                                                                                            | Actie                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Run 0   | `docs/plans/osmd-s8-recite.md`, `plans/README.md`, mkdocs-nav                                                                       | Plan + vindbaarheid              |
| Run 1   | Dit plan §2 Besluit                                                                                                                 | Empirische keuze vastleggen      |
| Run 2   | `docs/formats/score-ir.md`, checklist S8-zin over from-ir, `docs/reference/cli/mvsa.md` (from-ir), eventueel `partituur-ir.md` §4.4 | Emit-contract synchroon met code |
| Run 3   | bibliotheek `docs/specs/schermpartituur.md` §2/§5.1                                                                                 | Tijdelijke SVG-bypass eruit      |
| Run 4   | Cross-links kale-muziek / partituur-ir “productiescherm”                                                                            | Gap-status                       |

Terminologie: `zangstuk-id` → `variant-id` → `uitvoeringsvorm-id` →
`representatie-id`; geen ad-hoc “scherm-IR”.

---

## 8. Risico’s en open peilpunten

| Risico                                               | Mitigatie                                                                   |
| ---------------------------------------------------- | --------------------------------------------------------------------------- |
| OSMD eert geen enkele “onzichtbare kop + lyric”-truc | Dan pas C (sibling) of smalle JS als *laatste* noodoplossing — alleen na OK |
| Nav-/volta-regressie bij XML-wijziging               | Bestaande from-ir nav-tests + bibliotheek nav-check meenemen in run 2/3     |
| Verwarren MuseScore-MXL en from-ir                   | Docs: from-ir = scherm/OSMD; partituur-MXL/MSCZ = blad                      |
| Tempo/`<sound tempo>` recent                         | Niet terugdraaien; S8-emit orthogonaal houden                               |

**Open tot run 1:** exacte MusicXML-tags voor spacer (B vs andere OSMD-vriendelijke
vorm). **Open product:** of korte recite (`n < 6`) ongewijzigd blijft (ja,
tenzij peiling anders eist).

---

## 9. Succescheck (plan klaar genoeg)

- [x] Architectuur A/B/C + aanbeveling
- [x] Scope tooling vs bibliotheek
- [x] Tests per repo
- [x] Gefaseerde runs met kopieerbare opdrachtregels
- [x] Docs-matrix
- [ ] Run 1 peiling uitgevoerd (nog niet)
- [ ] Product-emit (run 2) — wacht op OK
