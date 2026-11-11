# Open punten — vsa-templates

Checklist voor verdere chats. Afgevinkt = gedaan in deze branch/sessies.
Onder **Werklijst** staan alleen nog echte vervolgstappen.

Valkuilen bij MSCZ/MXL: [rendering-pitfalls.md](rendering-pitfalls.md).
Mappingcontract: [mapping-vsa.md](mapping-vsa.md).

---

## Gedaan (niet opnieuw oppakken)

- [x] Lokale curated texts: [vsa-template](@), [template-frase](@),
      [template-event](@), [frase-id](@), [frase-anker](@), [formulelabel](@),
      [reciteertoon](@), [laddergraad](@), [do-context](@).
- [x] Frase-toewijzing: `text_mapping` + `mapping_plans` +
      [`template_mapping.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/template_mapping.py).
- [x] Mapping-architectuur **VSA→template-instance** (S uit VSA, A/T/B uit
      template) — zie [mapping-vsa.md](mapping-vsa.md);
      implementatie [`template_instance.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/template_instance.py)
      (geen “pad B”-jargon meer).
- [x] Hoogte-mismatch → harde `TemplateInstanceError` (H9); geen stil hold.
- [x] Tropaar-toon-4 corpus-pipeline: `.vsa` / `.mscz` / `.mxl` + lokale PDF;
      CLI `scripts/render_tropaar_toon4_corpus.py`.
- [x] Recite-print (MSCZ): ≥3 ongemarkeerd recite → `||O||`; eerste
      lettergreep **gecentreerd** op de nootkop; rest op spacer-noten naar
      rechts; laatste als kwart; **geen** melisma-extender onder recite;
      VSA-scopes eigen noten; Coria-MXL zonder collapse.
- [x] Instance-layout: één maat per strofe; MS4-maatstrepen via voice-
      `<BarLine visible=0>`; geen dots op `||O||`; lyric-dichtheid via
      `lyricsMinDistance` / `minNoteDistance` / maat-eind-spacer.
- [x] Valkuilen-doc + links in README / AGENTS / MkDocs:
      [rendering-pitfalls.md](rendering-pitfalls.md).
- [x] PDF-export uit git geweerd (afgeleide); lokaal via `--pdf-only`.
- [x] Spot-check PDF’s tropaar-toon-4-hemelum corpus: recite/scopes/layout kloppen
      (menselijke audit).
- [x] **Instance-foutmeldingen zoals `vsa validate`:** compacte + uitgebreide
      vorm; **bestand:regel:kolom**; foutcode; `Hint:` (H7/H9 e.d.).
- [x] **Mapping H4–H7** in de instance-mapper (optional; VSA-duur H5;
      hold/zelfde-S H6; H7 andere toon alleen via optional / zelfde-S-run
      incl. na recite). Details: [mapping-vsa.md](mapping-vsa.md).
- [x] **H1 `open` vs eerste recite:** YAML houdt twee events (formuleblad);
      instance slaat `open` over als VSA meteen reciteert — geen dubbele noot.
- [x] **`mode` / `do`:** template én VSA-parser alleen `major`/`minor`;
      mismatch → `VSA-TEMPLATE-MODE-MISMATCH` / `VSA-TEMPLATE-DO-MISMATCH`.
- [x] **Sequence / text_mapping-lengte:** vaste `sequence` zonder `laatste`
      eist exacte lengte. Speelplan eindigend op `laatste` (toon 3): prefix +
      altijd `laatste`; overflow → `VSA-TEMPLATE-TEXT-MAPPING`. Cycle+final
      variabel. Stichier-toon-5-pdf `laatste` heeft het anker.
- [x] **`l.lgr.` (H8):** mapper koppelt geankerd event + rest van de frase aan
      de laatste VSA-syllabe; stichier-toon-5-pdf `laatste` heeft het anker.
- [x] **Anker-normalisatie:** `e. st.` → `e.st.` (zelfde voor `l.st.`,
      `vl.st.`, `l.lgr.`).
- [x] **Parallelle cadenspaden (`of`):** YAML + mapper; VSA kiest impliciet;
      geen pad → mismatch. **Geen** [uitvoeringsvorm](@bron) (dat is
      zangstuk-niveau). Formuleblad toont pad 0. Tropaar-toon-4 `laatste`
      blijft voorlopig alleen mi–re–mi (fa-tak kan later bij).
- [x] **Tenor-octaaf tropaar-toon-4-hemelum:** `sol-1` t.o.v. `do: F4` = **C4**
      (niet C3). Vastgelegd in YAML + test.
- [x] CLI `vsa template validate`.
- [x] Formule-MusicXML: `scripts/render_vsa_template_musicxml.py`
      (`--all` of `template.yaml` → `.musicxml`/`.mscz`).
- [x] Formuleblad vs instance: wat in git / hoe regenereren — zie
      [rendering-pitfalls.md](rendering-pitfalls.md#formuleblad-vs-instance-wat-in-git)
      en [library/README.md](library/README.md).
- [x] **Inline VSA in proza:** `T.N` is geen zingbare syllabe; corpus zonder
      `T.N` in de VSA-regel. Markdown-inline renderer is geen
      instance-pipeline (zie mapping-vsa).
- [x] **Geen org glossary-PR** tot termen repo-overschrijdend moeten
      (template-termen blijven lokaal).
- [x] **Stemmen met onderling verschillende ritmes:** niet doen tot de
      noodzaak blijkt (homofone eventkeuzes blijven).

---

## Werklijst (vervolg)

### Templates / pitches

- [ ] Overige templates (niet tropaar-toon-4-hemelum): graden/`do`/`mode`
      `provisional` tot PDF-/partituur-audit.
- [ ] Tropaar-toon-4 `laatste`: fa-cadenspad als tweede `of`-tak encoderen
      zodra SATB van dat pad tegen het bronblad is gezet.

### Tooling / export

- [ ] Andere genres/tonen: eigen corpus + render zodra pitches geverifieerd
      zijn (mapper/renderer zijn al generiek).
- [ ] Markdown-inline VSA-fragment (hoogtemarkering / `Amen` in proza) als
      aparte presentatielaag — tablet/pc/telefoon én print — wanneer die UX
      nodig is.
