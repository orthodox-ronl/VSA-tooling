# mvsa ↔ MusicXML/MSCZ — conversies en canonieke vormen

| Veld            | Waarde                                                                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | werkplan                                                                                                                                        |
| **Doel**        | Betrouwbare conversies tussen `.mvsa`, `.mxl`/`.musicxml` en `.mscz`, plus normalisatie (diagonaal)                                             |
| **Draft-spec**  | [`docs/specification-mvsa/`](../specification-mvsa/README.md)                                                                                   |
| **Gerelateerd** | [mvsa-v0-syntax](mvsa-v0-syntax.md), [MusicXML-export](../guides/musicxml-export.md), [vsa-templates](../specification-vsa-templates/README.md) |

Dit is het **werkplan** voor conversietooling. Normatieve mvsa-schrijfregels
blijven in `specification-mvsa/`. Dit document legt vast: welke conversies we
willen, welke CLI-vorm, canonieke defaults, en in welke volgorde we bouwen.

---

## 1. Conversiematrix

Rijen = **bron**, kolommen = **doel**. De **diagonaal** is normalisatie: een
bestand waarin iets is gewijzigd of gemengd geschreven weer naar een gekozen
canonieke vorm brengen (zelfde formaat).

| Bron ↓ \ Doel →          | `.vsa`                        | `.mvsa`                | `.mxl` / `.musicxml`                                                                             | `.mscz`                                                                                                 | `.mp3` / audio         | `.midi` / `.mid`   |
| ------------------------ | ----------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------ |
| **`.vsa`**               | **normalize** (waar relevant) | — (niet v0)            | `vsa musicxml`                                                                                   | via MXL / templates                                                                                     | `vsa audio`            | — (niet gepland)   |
| **`.mvsa`**              | —                             | **`normalize`**        | `mvsa musicxml`                                                                                  | **`mscz`** via mxl→MuseScore                                                                            | `mvsa audio`           | — (niet gepland)   |
| **`.mxl` / `.musicxml`** | —                             | **`import`**           | **normalize** → [checklist MXL](../formats/canonical-checklists.md#checklist-mxl-coria-playback) | MuseScore / `mxl mscz`                                                                                  | `vsa audio`            | — (niet gepland)   |
| **`.mscz`**              | —                             | **`import`** (via mxl) | `mscz mxl`                                                                                       | **normalize** → [checklist MSCZ](../formats/canonical-checklists.md#checklist-mscz-partituur-musescore) | `vsa audio` (fallback) | — (niet gepland)   |
| **`.midi` / `.mid`**     | —                             | —                      | —                                                                                                | —                                                                                                       | —                      | — (niet gepland)   |

**Audio (``.mp3``):** preview-luisteren via MuseScore — zie
[formats/audio.md](../formats/audio.md). **``.midi``:** **niet gepland**
(preview = audio) — zie [formats/midi.md](../formats/midi.md).

Hub: [Formaten & CLI](../formats/index.md).

Legenda status in dit traject:

| Cel           | Betekenis                          |
| ------------- | ---------------------------------- |
| **bestaat**   | Werkende CLI / script in deze repo |
| **nieuw**     | Te bouwen in dit plan              |
| **diagonaal** | Zelfde formaat → canonieke vorm    |
| **—**         | Bewust niet in v0 van dit plan     |

**Diagonaal (expliciet):**

- **`.mvsa` → `.mvsa`:** default **behoud noteernamen** (`preserve`); optioneel
  herschrijven naar `doremi` / `a-g` (alias `abc`) / `vsa`; octaafstijl (`@oct` vs. later
  marker); kolom- + maatstreep-uitlijning (kuiser / `align_mvsa_columns`).
- **`.vsa` → `.vsa`:** alleen waar tooling al een canonieke schrijfvorm afdwingt
  of gaat afdwingen; geen scope-creep hier.
- **`.mxl` → `.mxl` / `.mscz` → `.mscz`:** normaliseer naar de
  [canonieke checklists](../formats/canonical-checklists.md) (Coria vs
  partituur), niet herdefiniëren van MusicXML/MuseScore.
- **Audio (``.mp3``):** preview-luisteren; zie [formats/audio.md](../formats/audio.md).
- **`.midi`:** niet gepland (preview = audio).

---

## 2. Canonieke vormen (index)

Wat **wij** vastleggen vs. externe standaarden:

| Formaat              | Wat canoniek is (van ons)                                             | Waar vastgelegd                                                                                                                              |
| -------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `.vsa`               | Eenstemmige VSA 1.0-schrijfvorm                                       | [`specification/`](../specification/README.md), bron-glossary                                                                                |
| `.mvsa`              | LSATB, sync, recite, kolommen, directives; pitch-varianten equivalent | [`specification-mvsa/`](../specification-mvsa/README.md)                                                                                     |
| `.mxl` / `.musicxml` | Checklist Coria/`playback`: vier parts S/A/T/B                        | [canonieke checklists](../formats/canonical-checklists.md), [rendering](../specification/rendering.md#musicxml-export)                       |
| `.mscz`              | Checklist partituur: twee balken SA/TB, geen stem-labels              | [canonieke checklists](../formats/canonical-checklists.md), [vsa-templates / pitfalls](../specification-vsa-templates/rendering-pitfalls.md) |
| `.mp3` / audio       | Preview-luisteren; MuseScore-defaults                                 | [formats/audio.md](../formats/audio.md)                                                                                                      |
| `.midi` / `.mid`     | Niet gepland (preview = audio)                                        | [formats/midi.md](../formats/midi.md)                                                                                                        |

### Pitch op stemregels (mvsa; keuze bij export/normalisatie)

| Id         | Betekenis                                                                     |
| ---------- | ----------------------------------------------------------------------------- |
| `preserve` | **Default** bij `.mvsa` → `.mvsa`: laat bronspelling staan                    |
| `doremi`   | Laddergraden `do` `re` `mi` … (+ octaafsuffix / `#`/`b`); import-default      |
| `a-g`      | Toonnamen `a`–`g` / `bb` / `f#` (+ wetenschappelijk cijfer); CLI-alias: `abc` |
| `vsa`      | Relatief: EHM `/` `\` `-` `/3` … op stemregels                                |

L-regel (lyrics, ELM, recite, melisma) blijft semantisch gelijk. Alleen bij
expliciete herschrijf-`pitch` verandert de hoogte-spelling op S/A/T/B.

### Octaafstijl (mvsa)

| Stijl                             | Betekenis                                                | Rol in gegenereerde output                        |
| --------------------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| `@oct`                            | Schrijfoctaaf per stem (`@oct T=-1 B=-1`)                | **Canoniek** in tooling-output                    |
| Marker (voorstel `T-1:` / `S+1:`) | Zelfde *bedoeling* als schrijfoctaaf — **niet** `@start` | Optionele invoer; kuiser normaliseert naar `@oct` |

**Besluit (plan):** `T-1:` (als we die marker later toestaan) = equivalent aan
`@oct T=-1` (schrijfoctaaf), niet startanker. Huidige marker-grammatica
`[LSATB] digit* ":"` gebruikt cijfers voor **stemnummer** (`T1:`); signed
octaaf in de marker is een bewuste syntax-uitbreiding later, niet stilzwijgend
hergebruik van `digit*`.

### Bestandsnaamgeving (conventie, niet afgedwongen)

- Default CLI-output: eenvoudig (`-o out.mxl`, bron-stem → `.mxl`).
- Optioneel in `generated/`: bron-extensie meenemen voor herkomst, bv.
  `naam.mvsa.mxl`, `naam.mscz.mvsa`, `naam.vsa.mp3`.
- Tools kijken naar de **laatste** extensie.
- Normatieve korte tekst + checklist-context:
  [canonieke checklists — naamgeving](../formats/canonical-checklists.md#bestandsnaamgeving-conventie).

---

## 3. Doel-CLI (bron = command)

Elke conversie-entry leest één brontype:

| Command             | Bron                 | Acties (richting)                                         |
| ------------------- | -------------------- | --------------------------------------------------------- |
| `vsa`               | `.vsa`               | validate, musicxml, svg, …; later `normalize` waar zinvol |
| `mvsa` / `vsa mvsa` | `.mvsa`              | validate, musicxml, mscz, pdf, audio, import, normalize   |
| `mxl`               | `.mxl` / `.musicxml` | import → mvsa; mscz (MuseScore)                           |
| `mscz`              | `.mscz`              | import → mvsa; mxl (MuseScore)                            |
| `vsa audio`         | `.mxl` / `.vsa` / …  | preview ``.mp3`` via MuseScore                            |

**Transitie:** `vsa mvsa …` blijft de volledige alias van top-level `mvsa`.
Windows: `scripts\mvsa.cmd`, `scripts\mxl.cmd`, `scripts\mscz.cmd`.

---

## 4. Trade-offs (kort)

| Onderwerp        | Keuze in dit plan                                                                                                                |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| MSCZ uit mvsa    | **Keten** `mvsa → partituur-mxl (SA/TB) → mscz` + strip labels — checklist-conform                                               |
| MXL ↔ MSCZ CLI   | `mxl mscz` → partituur; `mscz mxl` → vier Coria-parts                                                                            |
| Octaaf in output | Altijd `@oct` in gegenereerde canonieke mvsa                                                                                     |
| Import           | Lossy; succes = pitch/duur/lyrics-equivalentie, niet byte-identiek MSCZ                                                          |
| Scope            | Geen `@voices` / blokhergebruik tenzij export het eist                                                                           |

---

## 5. Slices (volgorde)

### Stap 1 — Matrix + index + doorverwijzingen ✅

**Criterium:** dit plan staat in MkDocs; `specification-mvsa` en `open-points`
verwijzen ernaar; diagonaal is expliciet in de matrix.

### Stap 2 — `normalize` (diagonaal `.mvsa` → `.mvsa`) ✅

```text
vsa mvsa normalize PATH [-o OUT] [--pitch {preserve,doremi,abc,vsa}] --octave-style @oct
```

- **Default `--pitch preserve`:** noteernamen op S/A/T/B blijven zoals in de
  `.mvsa`-bron; alleen canonieke kolomuitlijning. Expliciet `doremi` / `a-g` /
  `vsa` herschrijft hoogten.
- Import uit `.mxl`/`.mscz` gebruikt **`doremi`** als default (geen bronnotatie
  om te bewaren).
- Marker-octaaf-schrijven nog niet (`--octave-style marker` → foutmelding).
- EHM-cijfervormen `/3` / `\2` worden bij resolve ondersteund.

**Criterium (gehaald):** `preserve` houdt bladcijfer/do-re-mi/mix intact;
`schets2-oct-doremi`: `normalize --pitch a-g` → validate OK → MusicXML-pitches
identiek; ook `doremi → abc → doremi` en `--pitch vsa` pitch-equivalent
(`tests/test_mvsa_normalize.py`).

### Stap 3 — MSCZ-export uit mvsa ✅

Keten: `.mvsa` → **partituur**-`.mxl` (SA/TB, lege part-namen) → MuseScore CLI
→ `.mscz` → stem-indicaties uit.

```text
vsa mvsa mscz PATH [-o OUT] [--section ID] [--musescore PATH] [--keep-mxl PATH]
```

- Module: `vsa.mvsa_mscz` + `vsa.mscz_partituur` + `vsa.musescore_cli`.
- Playback/Coria blijft `mvsa musicxml` (vier parts).

**Criterium (gehaald):** met MuseScore 4 lokaal: twee Parts, geen Soprano-labels
(`tests/test_mvsa_mscz.py`; skip als MuseScore ontbreekt).

### Stap 4 — Import (score → mvsa) ✅

```text
vsa mvsa import PATH [-o OUT] --pitch {doremi,abc,vsa} --octave-style @oct
```

- Bron: `.mxl` / `.musicxml` direct; `.mscz` via MuseScore → mxl.
- Top-level `mxl import` / `mscz import` volgt tot stap 5 (nu onder `vsa mvsa import`).

**Criterium (gehaald):** roundtrip `mvsa → mxl → mvsa` pitch-equivalent op
`alleluia-toon-8.canonieke.mvsa` sectie `schets2-oct-doremi` voor `--pitch
doremi` en `a-g` (`tests/test_mvsa_import.py`).

### Stap 5 — Bron-commands + man-pagina’s ✅

Top-level console-scripts + `scripts\*.cmd`:

| Command             | Bron               | Acties                                      |
| ------------------- | ------------------ | ------------------------------------------- |
| `mvsa` / `vsa mvsa` | `.mvsa`            | validate, musicxml, mscz, import, normalize |
| `mxl`               | `.mxl`/`.musicxml` | import → mvsa; mscz                         |
| `mscz`              | `.mscz`            | import → mvsa; mxl                          |

**Criterium (gehaald):** `mvsa -h`, `mxl -h`, `mscz -h` tonen matrix-acties;
man-pagina’s `docs/reference/cli/{mvsa,mxl,mscz}.md`; oude `vsa mvsa …` blijft
werken.

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
