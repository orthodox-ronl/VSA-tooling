# Conversielessen VSA → MVSA (levend)

**Doel:** alles wat we bij toon 1/2/3/4/6/8 (en later 5/7, stichier,
vers, …) leerden, blijft vindbaar wanneer de officiële `vsa mvsa`-route
groeit. Normatieve regels blijven in
[vsa-mvsa-contract.md](vsa-mvsa-contract.md) (T1–T7). Hier alleen
**praktijklessen** en waar ze in code/YAML zitten.

Agent-regel: bij elke nieuwe template of toon deze checklist aflopen
(T7) en hier of in `library/<id>/notes/` bijwerken.

## Officiële route (één motor)

| Onderdeel | Plek                                                |
| --------- | --------------------------------------------------- |
| CLI       | `vsa mvsa [--template ID] [-o OUT] bestand.vsa`     |
| API       | `vsa.vsa_mvsa.convert_vsa_to_mvsa`                  |
| Mapper    | `vsa.template_instance.map_vsa_to_template` (T2–T4) |
| Emit      | `vsa.vsa_mvsa.emit_mapped_document` (T5–T6)         |
| Library   | `vsa.template_library` — ids, aliassen, `same_as`   |
| Formules  | `docs/specification-vsa-templates/library/<id>/`    |

Nieuwe formule = nieuwe map + `template.yaml` (genre × traditie × toon).
Geen toon-specifieke if-takken in de motor tenzij YAML tekortschiet (T7).

## Checklist bij elke nieuwe template / toon

1. **Id** — `{traditie}-{genre}-toon-{n}` of legacy zonder prefix; alias
   in `TEMPLATE_ALIASES` alleen als playbook die naam noemt.
2. **`same_as`** — tropaar = kondak-formule? Alias-YAML zonder phrases;
   CLI volgt `same_as` automatisch.
3. **`also_used_as`** — kondak op tropaar-formule (of omgekeerd) documenteren.
4. **`@oct`** — default emit: `S=0 A=0 T=-1 B=-1`. Alt op do=F4 = `f`
   (niet `f+` → F5 in Coria). Afwijking alleen met bewuste les + test.
5. **Tempo** — tropaar/kondak: emit zet altijd `@tempo 180` tenzij CLI
   `--tempo`; VSA-frontmatter-tempo telt niet. Niet in `template.yaml`.
6. **Emit-document (T6)** — geen `@speelplan`/`@blok`; gekuiste
   frontmatter; VSA-commentaar + banner; secties `cyclus-1` /
   `herhaling` / `laatste` (niet toon 3). Zie contract T6.
7. **B-pad / traditie** — verschil Hemelum↔Groningen (toon 4 frase 1)
   in YAML vastleggen (Hemelum `/2`→mi-1→re-1→la-2; Groningen `/`→re-1→la-2).
8. **VSA-invoer** — marker/`do` gelijk aan template; bekende valstrikken
   (toon 2: geen `{\Gij}` na mi-cadens) in README van die template.
9. **Corpus / afgeleiden** — na YAML-wijziging:
   `python scripts\sync_library_templates.py <id>` (schrijft `template.mxl`/
   `.mscz` naast de YAML), daarna `vsa mvsa` steekproef + optioneel `mvsa mxl`.
   Check: `python scripts\sync_library_templates.py --check <id>`.
10. **Notes** — korte les in `library/<id>/notes/` of een rij in de tabel
    hieronder.
11. **Tests** — frase-plan en/of emit-regressie in
    `tests/test_vsa_template_instance.py` / `test_vsa_mvsa_cli.py`.

## Lessen per toon / traditie (tot nu)

| Toon / id                                                | Les                                                                                                                                                                                                                                                                        | Waar vastgelegd                                                                           |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 4 Hemelum `tropaar-toon-4-hemelum`                       | Frase 1 B: `/2` al op mi-`@l.st.` → `mi-1`, dan `re-1` → `la-2`. Default `vsa mvsa`.                                                                                                                                                                                       | `template.yaml` + README                                                                  |
| 4 Groningen `tropaar-toon-4-groningen`                   | Frase 1 B: `@l.st.` `do-1`, fa `/` → `re-1` → `la-2`. Expliciet `--template`.                                                                                                                                                                                              | template + README                                                                         |
| 4 beide                                                  | Emit-oct: `A=0` synchroon met schrijfoctaaf (bug was F5).                                                                                                                                                                                                                  | `DEFAULT_VOICE_OCT`                                                                       |
| 4 / tropaar+kondak                                       | Tempo 180 in stuk, niet in formule.                                                                                                                                                                                                                                        | playbook + library README                                                                 |
| 1 `kondak-toon-1-groningen`                              | Mapping-plans (`standard` / `tropaar-extended-close`); melisma-emit Sofiа.                                                                                                                                                                                                 | template + tests                                                                          |
| 2 `kondak-toon-2-groningen` / `tropaar-toon-2-groningen` | `same_as`; VSA: na mi-cadens frase 2 niet `{\Gij}` (toon-1-reflex).                                                                                                                                                                                                        | tropaar-toon-2-groningen README                                                           |
| 3 `tropaar-toon-3-groningen`                             | Sequence `1,3,1,2,3,1,2a,4` (papier; géén herhalingsblok) eist 8 frasen — kortere corpus-teksten falen op mapping; geen ad-hoc kortere plannen zonder redactie. `do` F4. Zondag-kondak wél 8 na `*`-norm, dan pitch «Uit». Werkmap: bibliotheek `_werk/problemen-toon-3/`. | library + T6 + werkmap                                                                    |
| 5 `kondak-toon-5-groningen` / `tropaar-toon-5-groningen` | Groningen; `same_as`; cycle `1,2,3` + laatste; `@oct A=-1`.                                                                                                                                                                                                                | kondak-toon-5-groningen README                                                            |
| 6 `kondak-toon-6-groningen` / `tropaar-toon-6-groningen` | `same_as`; `@oct A=-1` in klaar-kondak.                                                                                                                                                                                                                                    | kondak-toon-6-groningen README                                                            |
| 7 `kondak-toon-7-groningen` / `tropaar-toon-7-groningen` | `same_as`; cycle `1,2` + laatste.                                                                                                                                                                                                                                          | library                                                                                   |
| 8 `kondak-toon-8-groningen` / `tropaar-toon-8-groningen` | Groningen; `same_as`; korte cycle; cadens re→do.                                                                                                                                                                                                                           | library + tests                                                                           |
| 8 `kondak-toon-8-hemelum` (+ tropaar)                    | Hemelum/Liturgikon; frase 1 `of:` (fa ná recite óf klim vóór); `laatste` → mi.                                                                                                                                                                                             | problemen-hoogte gestorvenen MVSA                                                         |
| 5 stichier/vers                                          | PDF-stichier blijft `stichier-toon-5-pdf` (niet Groningen kondak-5).                                                                                                                                                                                                       | library maps                                                                              |
| Capella/MSCZ→MVSA                                        | Losse straat (`mscz mvsa`); chord-explode M2 — niet verwarren met VSA→MVSA.                                                                                                                                                                                                | checklists M*                                                                             |
| Emit + align (T5)                                        | Geen ``)-(`` / wees-``-`` vóór ``(``: recite niet in hyphen-cont plakken; aligner skipt stray ``-`` (anders MVSA-SYNC).                                                                                                                                                    | `vsa_mvsa._join_l_atoms`, `mvsa_align._l_position_spans`, `tests/test_mvsa_align_sync.py` |
| Frasescheiders / print-wrap                              | Losse `*`/`/`/`**`/`//` buiten scope scheiden frasen; `{/…}` blijft EHM. Zonder `*`/`**`: niet-ingesprongen regel = frase; indent = wrap.                                                                                                                                  | `vsa_stanzas`, mapping-vsa §frasescheiders                                                |

## Wat de motor wél / niet doet

| Wel                                                         | Niet                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| Template kiezen via id/alias/`same_as`                      | Stille “dichtstbijzijnde” cadens                                   |
| Schets-banner + `# WAARSCHUWING:` + secties (T6)            | `@speelplan` / `@blok` in de schets                                |
| Gekuiste frontmatter (catalogusvelden)                      | `do`/`mode`/`tempo` in YAML-kop van de schets                      |
| Default oct + tempo 180 (frontmatter-tempo negeren)         | Tradition-specifieke B-uitzonderingen raden                        |
| Uitbreiden met nieuwe library-mappen                        | Per-toon fork van emit-code                                        |

## Zie ook

- Contract T1–T7: [vsa-mvsa-contract.md](vsa-mvsa-contract.md)
- Playbook (repo, niet op Pages):
  `examples/formule-tekst/PLAYBOOK.md`
  ([GitHub](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/formule-tekst/PLAYBOOK.md))
- Library: [library/README.md](library/README.md)
- CLI: [docs/reference/cli/vsa-mvsa.md](../reference/cli/vsa-mvsa.md)
