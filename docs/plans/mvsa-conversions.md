# mvsa ↔ MusicXML/MSCZ — conversies en canonieke vormen

| Veld            | Waarde                                                                                         |
| --------------- | ---------------------------------------------------------------------------------------------- |
| **Status**      | werkplan                                                                                       |
| **Doel**        | Betrouwbare conversies tussen `.mvsa`, `.mxl`/`.musicxml` en `.mscz`, plus normalisatie (diagonaal) |
| **Draft-spec**  | [`docs/specification-mvsa/`](../specification-mvsa/README.md)                                  |
| **Gerelateerd** | [mvsa-v0-syntax](mvsa-v0-syntax.md), [MusicXML-export](../guides/musicxml-export.md), [vsa-templates](../specification-vsa-templates/README.md) |

Dit is het **werkplan** voor conversietooling. Normatieve mvsa-schrijfregels
blijven in `specification-mvsa/`. Dit document legt vast: welke conversies we
willen, welke CLI-vorm, canonieke defaults, en in welke volgorde we bouwen.

---

## 1. Conversiematrix

Rijen = **bron**, kolommen = **doel**. De **diagonaal** is normalisatie: een
bestand waarin iets is gewijzigd of gemengd geschreven weer naar een gekozen
canonieke vorm brengen (zelfde formaat).

| Bron ↓ \ Doel → | `.vsa` | `.mvsa` | `.mxl` / `.musicxml` | `.mscz` |
| --------------- | ------ | ------- | -------------------- | ------- |
| **`.vsa`** | **normalize** (canonieke VSA-schrijfvorm; bestaand pad waar relevant) | — (niet v0; eenstemmig ≠ mvsa) | `vsa musicxml` (bestaat) | via MXL of template-pad (bestaat deels voor corpus) |
| **`.mvsa`** | — | **`normalize`** (pitch-vorm + `@oct`/layout) | `mvsa musicxml` (bestaat deels) | **nieuw** (keten of native) |
| **`.mxl` / `.musicxml`** | — (later / out of scope tenzij nodig) | **`import`** → mvsa | **normalize** (ons playback-/engraving-profiel) | MuseScore CLI / workflow |
| **`.mscz`** | — | **`import`** → mvsa | export uit MuseScore / tooling | **normalize** (ons partituur-profiel; beperkt wat wij vastleggen) |

Legenda status in dit traject:

| Cel | Betekenis |
| --- | --------- |
| **bestaat** | Werkende CLI / script in deze repo |
| **nieuw** | Te bouwen in dit plan |
| **diagonaal** | Zelfde formaat → canonieke vorm |
| **—** | Bewust niet in v0 van dit plan |

**Diagonaal (expliciet):**

- **`.mvsa` → `.mvsa`:** hoogte-spelling (`doremi` / `abc` / `vsa`),
  octaafstijl (`@oct` vs. later marker), kolom- + maatstreep-uitlijning
  (kuiser / `align_mvsa_columns`).
- **`.vsa` → `.vsa`:** alleen waar tooling al een canonieke schrijfvorm afdwingt
  of gaat afdwingen; geen scope-creep hier.
- **`.mxl` → `.mxl` / `.mscz` → `.mscz`:** normaliseer naar *ons* profiel
  (Coria-playback vs. partituur), niet herdefiniëren van MusicXML/MuseScore.

---

## 2. Canonieke vormen (index)

Wat **wij** vastleggen vs. externe standaarden:

| Formaat | Wat canoniek is (van ons) | Waar vastgelegd |
| ------- | ------------------------- | --------------- |
| `.vsa` | Eenstemmige VSA 1.0-schrijfvorm | [`specification/`](../specification/README.md), bron-glossary |
| `.mvsa` | LSATB, sync, recite, kolommen, directives; pitch-varianten equivalent | [`specification-mvsa/`](../specification-mvsa/README.md) |
| `.mxl` / `.musicxml` | Exportprofielen `playback` (Coria) en `engraving`; geen volledige MusicXML-herdefinitie | [MusicXML-export](../guides/musicxml-export.md), [rendering](../specification/rendering.md#musicxml-export) |
| `.mscz` | Partituur-workflow (SATB, layout-conventies die MusicXML kwijtraakt); geen MuseScore-formaat-spec | [vsa-templates](../specification-vsa-templates/README.md), pitfalls |

### Pitch op stemregels (mvsa; keuze bij export/normalisatie)

| Id | Betekenis |
| -- | --------- |
| `doremi` | Laddergraden `do` `re` `mi` … (+ octaafsuffix / `#`/`b`) |
| `abc` | Toonnamen `a`–`g` / `bb` / `f#` (+ wetenschappelijk cijfer of suffix) |
| `vsa` | Relatief: EHM `/` `\` `-` `/3` … op stemregels |

L-regel (lyrics, ELM, recite, melisma) blijft semantisch gelijk; alleen
hoogte-spelling op S/A/T/B verandert.

### Octaafstijl (mvsa)

| Stijl | Betekenis | Rol in gegenereerde output |
| ----- | --------- | -------------------------- |
| `@oct` | Schrijfoctaaf per stem (`@oct T=-1 B=-1`) | **Canoniek** in tooling-output |
| Marker (voorstel `T-1:` / `S+1:`) | Zelfde *bedoeling* als schrijfoctaaf — **niet** `@start` | Optionele invoer; kuiser normaliseert naar `@oct` |

**Besluit (plan):** `T-1:` (als we die marker later toestaan) = equivalent aan
`@oct T=-1` (schrijfoctaaf), niet startanker. Huidige marker-grammatica
`[LSATB] digit* ":"` gebruikt cijfers voor **stemnummer** (`T1:`); signed
octaaf in de marker is een bewuste syntax-uitbreiding later, niet stilzwijgend
hergebruik van `digit*`.

### Bestandsnaamgeving (conventie, niet afgedwongen)

- Default CLI-output: eenvoudig (`-o out.mxl`, bron-stem → `.mxl`).
- Optioneel in `generated/`: bron-extensie meenemen voor herkomst, bv.
  `naam.mvsa.mxl`, `naam.mscz.mvsa`. Tools kijken naar de **laatste** extensie.

---

## 3. Doel-CLI (bron = command)

Elke conversie-entry leest één brontype:

| Command | Bron | Acties (richting) |
| ------- | ---- | ----------------- |
| `vsa` | `.vsa` | validate, musicxml, svg, …; later `normalize` waar zinvol |
| `mvsa` | `.mvsa` | validate, musicxml, mscz, **normalize**, … |
| `mxl` | `.mxl` / `.musicxml` | import → mvsa; normalize (profiel); → mscz |
| `mscz` | `.mscz` | import → mvsa; normalize (profiel); → mxl |

**Transitie:** bestaande `vsa mvsa …` en `vsa musicxml` blijven werken tot de
top-level commands stabiel zijn (alias of wrapper). Windows: voorkeur voor
duidelijke cmd-voorbeelden per broncommand in man-pagina’s.

Huidig (tot migratie):

```text
vsa mvsa validate PATH
vsa mvsa musicxml PATH [-o OUT] [--section ID]
```

Gepland (namen mogen licht afwijken; wel `--help` + man-pagina):

```text
mvsa validate PATH
mvsa musicxml PATH [-o OUT] [--section ID] [--profile playback|engraving]
mvsa mscz PATH [-o OUT] [--section ID]
mvsa normalize PATH [-o OUT] --pitch {doremi,abc,vsa} --octave-style {@oct,marker}
mxl import PATH [-o OUT] --pitch … --octave-style …
mscz import PATH [-o OUT] --pitch … --octave-style …
```

Tot top-level `mvsa` bestaat: zelfde subcommando’s onder `vsa mvsa …`.

---

## 4. Trade-offs (kort)

| Onderwerp | Keuze in dit plan |
| --------- | ----------------- |
| MSCZ uit mvsa | Eerst **keten** `mvsa → mxl → mscz` (MuseScore CLI), documenteren; native MSCX alleen als partituur-layout MusicXML overleeft niet |
| Octaaf in output | Altijd `@oct` in gegenereerde canonieke mvsa |
| Import | Lossy; succes = pitch/duur/lyrics-equivalentie, niet byte-identiek MSCZ |
| Scope | Geen `@voices` / blokhergebruik tenzij export het eist |

---

## 5. Slices (volgorde)

### Stap 1 — Matrix + index + doorverwijzingen ✅

**Criterium:** dit plan staat in MkDocs; `specification-mvsa` en `open-points`
verwijzen ernaar; diagonaal is expliciet in de matrix.

### Stap 2 — `normalize` (diagonaal `.mvsa` → `.mvsa`) ✅

```text
vsa mvsa normalize PATH [-o OUT] --pitch {doremi,abc,vsa} --octave-style @oct
```

- Herschrijf stemhoogten; behoud L-semantiek; kolom-/maatstreep-align (tenzij
  `--no-align`).
- Marker-octaaf-schrijven nog niet (`--octave-style marker` → foutmelding).
- EHM-cijfervormen `/3` / `\2` worden bij resolve ondersteund.

**Criterium (gehaald):** `alleluia-toon-8.canonieke.mvsa` sectie
`schets2-oct-doremi`: `normalize --pitch abc` → validate OK → MusicXML-pitches
identiek; ook `doremi → abc → doremi` en `--pitch vsa` pitch-equivalent
(`tests/test_mvsa_normalize.py`).

### Stap 3 — MSCZ-export uit mvsa

Keten documenteren + CLI `mvsa mscz` (of `vsa mvsa mscz`). Coria blijft via
`.mxl` playback-profiel.

**Criterium:** gegenereerde `.mscz` opent in MuseScore 4 en toont SATB + lyrics
bruikbaar voor de partituur-workflow (niet alleen “toevallig open”).

### Stap 4 — Import (score → mvsa)

`mxl import` / `mscz import` met `--pitch` en `--octave-style @oct`.

**Criterium:** roundtrip `mvsa → mxl → mvsa` (gekozen pitch) pitch/duur-equivalent
op een fixture uit `examples/mvsa/`; output onder `generated/`.

### Stap 5 — Bron-commands + man-pagina’s

Top-level `mvsa` / `mxl` / `mscz` (of `.cmd`-wrappers); `docs/reference/cli/`
bijwerken; oude paden als alias.

**Criterium:** `mvsa -h`, `mxl -h`, `mscz -h` tonen de matrix-acties; voorbeelden
in docs gebruiken Windows `cmd`-blokken.

---

## 6. Bewust later / buiten slice

- Blokhergebruik `@voices`, overlays A/T/B t.o.v. S
- Native MSCZ-schrijver voor willekeurige mvsa (tenzij stap 3 faalt zonder)
- Parallelle lyrics (`L1` als lyric number 2)
- Volledige MuseScore- of MusicXML-formaatdefinitie
- Verplichte dubbele extensies in alle outputs

---

## 7. Succescriteria (programma)

- Spec/plan: canonieke keuzes en CLI staan hier (niet alleen in chat).
- Roundtrips waar haalbaar; anders pitch/duur-equivalentie.
- `.mxl` blijft playback-vriendelijk (bestaande profielen / pitfalls).
- `.mscz` bruikbaar in partituur-workflow.
- `examples/mvsa/` blijft `vsa mvsa validate`-groen; nieuwe fixtures in
  `generated/`.
- Geen scope-creep op blokhergebruik.
