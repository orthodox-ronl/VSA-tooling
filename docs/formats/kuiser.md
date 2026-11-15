# Kuiser (straat-actie)

**Status:** contract vastgelegd. **Geïmplementeerd in `mvsa kuiser`:**
Q1–Q8 (YAML-FM, `@`-blok, `#maat`, syllabify, dictionary, banners,
validate-gate, normaalvorm). **Q9** = bestaande `--check`.

Canonieke hub voor **opkuisen naar canonieke authoring-vorm** per
bestandstype. Geen product, geen products-meta. Straat-CLI:
`{straat} kuiser` — zelfde idee als `normalize`/`validate`.

Eigendom frontmatter-schema (YAML): bibliotheek
[`vsa-frontmatter.md`](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md).
Deze hub legt vast wat **tooling** bij kuiser mag/moet schrijven.

## Generiek

| Regel     | Inhoud                                                                                                  |
| --------- | ------------------------------------------------------------------------------------------------------- |
| CLI       | `{straat} kuiser PATH…` met alleen de bronextensie van die straat                                       |
| Geen spec | Exit ≠ 0 + duidelijke melding: voor dit type ontbreekt nog een kuiser-specificatie (link naar deze hub) |
| Na kuiser | Bestand voldoet aan het formatcontract van dat type (C2), voor zover de Q\*/V\*/…-reeks dat eist        |
| Dry-run   | `--check` / `--dry-run`: tonen zonder schrijven (waar geïmplementeerd)                                  |

| Straat / type           | Contract-reeks                 | Status                                    |
| ----------------------- | ------------------------------ | ----------------------------------------- |
| `.mvsa` (`mvsa kuiser`) | **Q1–Q9** (hieronder)          | Q1–Q8 actief; Q9 = `--check`              |
| `.vsa` (`vsa kuiser`)   | **V\*** (apart vast te leggen) | placeholder — CLI weigert tot V\* bestaat |
| `.mscz` (`mscz kuiser`) | —                              | geen spec → foutmelding                   |
| `.mxl` (`mxl kuiser`)   | —                              | geen spec → foutmelding                   |
| Partituur-PDF           | —                              | geen kuiser-straat; geen spec             |

`normalize` blijft **alleen** spelling/pitch/kolommen (`.mvsa`) of
layoutprofiel (`.mscz`/`.mxl`). Kuiser is breder: metadata, syllabificatie,
maatcommentaar, daarna normaalvorm.

---

## MVSA — checklist Q\*

Doel: catalogus-/werkbank-`.mvsa` naar **canonieke authoring-vorm**.
Volgorde van stappen is normatief (Q1 → … → Q9).

### Keuzes (besluit)

| Onderwerp                  | Keuze                                                                                                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tempo-fingerprint          | Ontbreekt of “tool-default” → kuiser zet **131**, of **181** bij `soort` ∈ {`tropaar`, `kondak`, `stichier`}. Zo herken je kuiser-tempo’s.                                     |
| Tool-default tempo         | Waarden die als “nog niet bewust gezet” tellen: ontbrekend; **130** (o.a. `mscz mvsa` / VSA-default zonder `@tempo`); eventueel oudere **180**. Bewust ander BPM blijft staan. |
| Tempo elders verzinnen     | Elke tool die een tempo moet verzinnen (import, kuiser, …) volgt **dezelfde** 131/181-regel.                                                                                   |
| Titel-suffix               | `(Toon N)` met hoofdletter T.                                                                                                                                                  |
| Conflict YAML ↔ `@`        | **`@`-blok wint**; YAML-frontmatter wordt daarnaar bijgewerkt.                                                                                                                 |
| Maatcommentaar             | Canoniek **`#maat N`** (geen spatie na `#`).                                                                                                                                   |
| Syllabificatie bij twijfel | Eerst **waarschuwen**; woorden (mét streepjes) aan de syllable-dictionary kunnen toevoegen; netjes **afbreken** zodat de redacteur meteen kan wijzigen.                        |
| Zoektekst                  | Interpunctie en hoofdletters volgen de L-lyrics; hele woorden (geen soft-hyphens); frasering ≈ MVSA-frases/maten.                                                              |
| Taal                       | Ontbrekende `taal` → `nl` (tenzij `@taal` / lyrics anders aangeven).                                                                                                           |

### Q1 — YAML-frontmatter (minimaal)

Schrijf of vul gedocumenteerde sleutels (catalogus: alleen gevulde sleutels;
zie bibliotheek-spec). Minimaal:

| Sleutel                 | Inhoud                                                                             |
| ----------------------- | ---------------------------------------------------------------------------------- |
| `titel`                 | Herkenbare titel; anders afgeleid van bestandsnaam + `(Toon N)` indien toon bekend |
| `taal`                  | Default `nl` indien ontbreekt                                                      |
| `soort`                 | Uit FM, anders pad/bestandsnaam                                                    |
| `toon`                  | 1–8 indien Oktoëchos / `toon-N` in pad                                             |
| `bron.uitgangspunt`     | Behouden indien aanwezig; niet verzinnen                                           |
| `bron.bewerking`        | Uitvoeringsvorm-label indien afleidbaar (pad)                                      |
| `zoektekst`             | Uit L-regels (zie keuze hierboven)                                                 |
| `do` / `mode` / `tempo` | Gelijk aan `@`-blok ná Q2 (plat, zolang tooling dat zo leest)                      |

Voorkeursvolgorde top-level: bibliotheek
[vsa-frontmatter — voorkeursvolgorde](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md).

### Q2 — `@`-blok

Zorg voor (document-start, vóór eerste LSATB-systeem):

| Directive    | Regel                                                                     |
| ------------ | ------------------------------------------------------------------------- |
| `@title "…"` | Verplicht na kuiser; wint van YAML `titel`                                |
| `@do`        | Behouden of uit context; sync naar FM `do`                                |
| `@mode`      | Behouden of default `major`; sync naar FM                                 |
| `@tempo`     | Volgens tempo-fingerprint (131/181); sync naar FM                         |
| `@oct`       | Alleen behouden/schrijven als die al zinvol aanwezig is of uit bron volgt |

Geen `@tempo` midden in een LSATB-systeem.

### Q3 — `#maat N` per systeem

| Regel    | Inhoud                                                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plaats   | Direct vóór elk LSATB-systeem (ná `@sectie` mag)                                                                                                              |
| Vorm     | `#maat N` — `N` = canonieke eerste koormaat van dat systeem ([mvsa — canonieke maatnummers](mvsa.md#canonieke-maatnummers-type-specifiek))                    |
| Opruimen | Verwijder andere regels die met `#maat` of `# maat` beginnen vóór dat systeem; tussen zo’n commentaar en het systeem geen `@…`-directives (die horen erboven) |

### Q4 — Lettergreepstreepjes plaatsen

Zet soft `-` op L volgens syllabificatie-hub
([syllabificatie.md](syllabificatie.md) / `mvsa syllabify`).

### Q5 — Dictionary-consistentie

Elke soft-deling moet kloppen met de syllable-dictionary van de repo.
Bij conflict of onbekend woord: **waarschuwing**; interactief of via vlag
woorden (mét streepjes) toevoegen; of **afbreken** zonder half geschreven
bestand (of met duidelijke non-write). Geen stille verkeerde deling.

### Q6 — Schets-/importbanners (catalogus)

Bij catalogus-opkuis: strip `# Imported:…` / schets-WAARSCHUWING-boxbanners
/ `# WAARSCHUWING:…` / emit-sectie «specifieke waarschuwingen».
Vlag **`--werkbank`**: behoud die banners (werkbank-schets).
`#maat N` en overige redactionele comments blijven staan.

### Q7 — Validatie na schrijven

Na kuiser (en na succesvolle schrijf): `mvsa validate` zonder **errors**
op het resultaat. Warnings (o.a. dictionary) mogen blijven. Optioneel:
bibliotheek `frontmatter-canoniek --check` buiten deze CLI.

### Q8 — Normaalvorm (bestaande kuiser + normalize)

Daarna de bestaande authoring-kuiser + align/normalize-pad:

- eenduidige ELM-`-` → `~`, lone `~` weg;
- maatstrepen syncen waar eenduidig;
- canonieke kolomuitlijning inkl. `&`-kolommen;
- optioneel `--pitch` / `--octave-style` zoals nu.

Zie [semantics — canonieke layout](../specification-mvsa/semantics.md#canonieke-layout-vs-tolerantie).

### Q9 — Dry-run / check

`--check` (of `--dry-run`): rapporteer voorgenomen wijzigingen; geen
schrijven; exit 1 als er iets zou wijzigen (huidig `mvsa kuiser --check`-gedrag
uitbreiden).

---

## VSA — V\* (placeholder)

Nog **niet** gespecificeerd. Volgende ronde: `vsa kuiser`-contract (V\*)
hier of in een sibling-sectie vastleggen. Tot die tijd weigert
`vsa kuiser` met verwijzing naar deze hub.

Verwachte richting (niet normatief tot V\* landt): frontmatter/`soort`/`toon`,
zoektekst, syllabificatie + dictionary, daarna canonieke VSA-vorm.

---

## MSCZ / MXL / PDF

Geen kuiser-checklist. `mscz kuiser` / `mxl kuiser` → foutmelding.
Partituur-PDF heeft geen `{straat} kuiser`-pad.

Layout/playback blijft bij `mscz normalize` / `mxl normalize`.

---

## Zie ook

- [contract-index](contract-index.md)
- [mvsa.md](mvsa.md) · [syllabificatie.md](syllabificatie.md) · [zoektekst.md](zoektekst.md)
- Man-pagina: [`mvsa kuiser`](../reference/cli/mvsa.md#mvsa-kuiser)
