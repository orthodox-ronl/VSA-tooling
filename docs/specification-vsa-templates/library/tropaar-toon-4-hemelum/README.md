# Tropaar toon 4 (Hemelum)

**Traditie:** Hemelum (niet Groningen). **Ook voor kondak** toon 4
(`also_used_as: [kondak]`). Canonieke id: `tropaar-toon-4-hemelum`. Playbook-alias
voor CLI: `hemelum-tropaar-toon-4` → dit id (default bij `vsa mvsa`).

Groningen toon 4: aparte formule
[`tropaar-toon-4-groningen`](../tropaar-toon-4-groningen/) (expliciet
`--template tropaar-toon-4-groningen`).

**Frase 1 B-pad:** Hemelum zet `/2` → `mi-1` zodra de mi-cadens na de
recite begint, dan `\` → `re-1` (hold) → `la-2`. Groningen houdt B op
`do-1` tot de fa (`/` → `re-1`). Bron: klaar Nikolaas + gecorrigeerde
`kondak-zondag-toon-4-hemelum.mvsa`. Tempo (`@tempo 180`) hoort in het
stuk, niet in deze formule.

> **Herstart 2026-11:** formule+tekst-verkenning in de repo-map
> `examples/formule-tekst/tropaar-toon-4-hemelum/` (niet op de documentatiesite).
> Playbook: `examples/formule-tekst/PLAYBOOK.md`.
> Snapshot oude aanpak: `examples/formule-tekst/.archief/tropaar-toon-4-hemelum-oud/`.

| Veld              | Waarde                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Formule-bron      | [`template.yaml`](template.yaml) — **bewerk dit**                                            |
| Traditie / genres | Hemelum; tropaar + kondak                                                                    |
| `laatste` cadens  | `of:` `re-close` (pad 0, formuleblad) · `fa-close` (mi–fa–mi)                                |
| Formule-MSCZ/MXL  | [`template.mscz`](template.mscz) / [`template.mxl`](template.mxl) — afgeleid uit *deze* YAML |
| Formule-PDF       | `template.pdf` (lokaal via MuseScore; niet in git)                                           |
| Status pitches    | `provisional`                                                                                |
| Mapping           | S=VSA, A/T/B=template ([mapping-vsa.md](../../mapping-vsa.md))                               |

## Wat hoort in deze map

```text
tropaar-toon-4-hemelum/
  template.yaml          ← canonieke formule (bewerk hier)
  template.mscz          ← afgeleid uit template.yaml (Hemelum)
  template.mxl           ← afgeleid uit template.yaml (Hemelum)
  template.pdf           ← lokaal afgeleid (print; .gitignore)
  README.md
  notes/                 ← corpus-notities, mappinglessen
  examples/corpus/       ← .vsa + afgeleide .mscz/.mxl (+ lokale .pdf)
```

Na elke wijziging in `template.yaml` (zelfde voor Groningen):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\sync_library_templates.py tropaar-toon-4-hemelum
python scripts\sync_library_templates.py --check tropaar-toon-4-hemelum
```

**Niet** committen / niet bewaren: MuseScore-rommel (`.mscbackup/`,
`Thumbnails/`, losse `META-INF/`, `audiosettings.json`, `viewsettings.json`,
`score_style.mss`, …), dubbele `template-from-yaml.*`, of `*.pdf`.

## Corpus-pijplijn

Elke `examples/corpus/*.vsa` + `template.yaml` → `.mscz` (MuseScore) +
`.mxl` (Coria) + optioneel `.pdf` (print).

Titel in MSCZ/PDF = frontmatter-`title`; ontbreekt die → bestandsnaam zonder
extensie.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
call .venv\Scripts\activate
python scripts\render_tropaar_toon4_corpus.py
python scripts\render_tropaar_toon4_corpus.py --pdf
```

Alleen formuleblad:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\sync_library_templates.py tropaar-toon-4-hemelum
python scripts\render_tropaar_toon4_corpus.py --template --pdf
```

Alleen PDF’s opnieuw uit bestaande `.mscz`:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\render_tropaar_toon4_corpus.py --pdf-only
```

Default gebruikt bestaande `examples/corpus/*.vsa`. Alleen met
`--from-onderzoek` opnieuw extracten uit het onderzoeks-markdown (dat
bestand heeft niet alle 13 blokken, o.a. T4-07a).

## Voorbeelden

| Pad                                                                                | Inhoud                                      |
| ---------------------------------------------------------------------------------- | ------------------------------------------- |
| [`notes/corpus.md`](notes/corpus.md)                                               | overzicht 13 stukken + mapping              |
| [`examples/corpus/T4-06-profeet-elia.vsa`](examples/corpus/T4-06-profeet-elia.vsa) | canonieke Elia-bron                         |

## Notes

| Bestand                                          | Inhoud                          |
| ------------------------------------------------ | ------------------------------- |
| [`notes/corpus.md`](notes/corpus.md)             | Toon-4-teksten ↔ frase-cycle    |
| [`notes/elia-mapping.md`](notes/elia-mapping.md) | Slot-toets Elia regel 1         |

## Status

- Frase-ids, `||O||`-recite, haakjes-optional, `e.st.`/`l.st.` in YAML;
  renderer → MSCZ.
- Tenor openingsakkoord: `sol-1` = **C4** t.o.v. `do: F4` (niet C3).
- Lyrics: DejaVu Sans Condensed 12pt (`LYRIC_FONT_PT`).
- Verticale witruimte: stafafruimte 5 spatium; systeemmafruimte en
  titel→systeem mikken op **1,5×** daarvan op het scherm. Titelgat =
  VBox + `frameSystemDistance` (VBox 3.5 + frame 4.0). Systeemmafruimte
  gecorrigeerd (gemeten 7/6 → setting ×9/7). Geen page-fill, geen
  eerste-systeem-inspringing. MSCZ bevat `score_style.mss`.
