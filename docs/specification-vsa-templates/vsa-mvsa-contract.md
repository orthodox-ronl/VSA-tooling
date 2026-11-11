# Contract: VSA + template → MVSA (T-reeks)

**Status:** normatief voor tooling en agent-werk (draft v0).  
**Canonieke hub** voor `vsa mvsa` / template-instance / emit.  
Uitwerking van hypotheses: [mapping-vsa.md](mapping-vsa.md).  
In de index: [contract-index](../formats/contract-index.md).

Bij **elk** werk aan mapper, emit, `vsa mvsa`, of corpus-regeneratie:
lees de relevante **T-id** hier; wijzig normatieve tekst **alleen** hier
(elders linken). Noem het T-id in PR/tests/uitleg.

## Architectuur (T0)

| Laag                           | Rol                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| **Template-id**                | Bijv. `kondak-toon-1-groningen` (map `library/<id>/`); CLI-alias later (`kondak-t1`) |
| **Template** (`template.yaml`) | Formule: frasen, rollen, ankers, `do`/`mode`, speelplan                              |
| **Motor**                      | Gedeelde mapper + emit voor alle template-ids                                        |
| **Instance**                   | Afgeleide MVSA (schets tot goedgekeurd in corpus)                                    |

Eén motor, veel templates. Toon-specifieke code alleen als het eventmodel
tekortschiet — eerst YAML proberen (T7).

## Checklist T1–T7

| Id  | Regel                                | Kort                                                                                                                                                                                                                                                                                                                              |
| --- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T1  | Template-id                          | Keuze: zie **T1 — templatekeuze** hieronder (`soort`+`toon`, of `formule`+`toon` als de melodieformule ≠ liturgische soort). Elke afgeleide MVSA noemt de **feitelijk gebruikte** formule-id in frontmatter (`template:`) én in meta-commentaar. Was de CLI-/selectie-id een alias (of `same_as`), dan ook `template_opgegeven:`. Geen stille default. |
| T2  | Melodiestem uit VSA                  | **Default:** VSA-melodie matcht template-`pitches.S` en vult de MVSA-**S**-regel. **Override:** `--melody A` (enz.) → match op `pitches.A` (of T/B); VSA-pitch vult die MVSA-stem; overige stemmen uit template op hetzelfde event.                                                                                               |
| T3  | Overige stemmen                      | Niet-melodiestemmen: laddergraden uit template-`pitches.*` op het **zelfde** gekoppelde event (synchroon met melodiekeuzes H4–H8).                                                                                                                                                                                                |
| T4  | ELM / EHM                            | **ELM:** VSA wint (duur). **EHM:** exacte match op template-`pitches.<melodiestem>` t.o.v. template-`do`/`mode` (H5/H9). Mismatch → harde fout, geen stil hold. Bij fout: andere formules voor dezelfde `soort`+`toon` stil proberen; als die passen → suggestie + plakbaar `vsa mvsa … --template …` (geen automatische switch). |
| T5  | Recite & ELM in emit                 | MVSA-recite `(…)` = standaardkwart per lettergreep; **geen** ELM binnen haakjes. Same-pitch-collapse alleen voor default-kwarten. Halve noten (`_`) blijven eigen L-posities. Melisma: zie ook K2/K3 / mapping H8.                                                                                                                |
| T6  | Schets-documentvorm & waarschuwingen | Afgeleide MVSA: gekuiste frontmatter; VSA-commentaar; bron/template/notatie; schets-banner + `# WAARSCHUWING:`; `@title`/`@do`/`@mode`/`@tempo`/`@oct`; systemen **zonder** `@speelplan`/`@blok`; secties `cyclus-1` / `herhaling` / `laatste` (niet toon 3).                                                                     |
| T7  | Corpus & verbetercyclus              | Per template-id: corpus `.vsa` + goedgekeurde `.mvsa`. Eerst template-YAML bijstellen; motor alleen bij structurele gaten. Na wijziging: steekproef/regressie op corpus. Lessen in `library/<id>/notes/`.                                                                                                                         |

## T1 — templatekeuze (detail)

`vsa mvsa` zoekt formules in de library op **melodieformule + `toon`**:

- Standaard: liturgische **`soort` + `toon`** uit de `.vsa`-frontmatter
  (verplicht op catalogus-VSA’s).
- Uitzondering: staat **`formule:`** in de VSA, dan zoekt T1 op die
  formule-soort (of volledige template-id/alias) + `toon`. Liturgische
  `soort` blijft ongewijzigd (bijv. `soort: kondak` + `formule: stichier`
  + `toon: 6` → `stichier-toon-6-…`).

| Situatie                                                              | Gedrag                                                                             |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| CLI `--template ID`                                                   | Die id/alias wint altijd.                                                          |
| `formule:` = bestaande library-id/alias                               | Die gebruiken (geen kandidatenlijst).                                              |
| `formule:` = genre (`stichier`, …) of anders `soort` + `toon`         | Kandidaten `{formule\|soort}-toon-{n}-…`.                                          |
| Geen enkele passende formule                                          | **Harde fout** — geen stille Hemelum-/Groningen-default.                           |
| Precies één formule                                                   | Die gebruiken.                                                                     |
| Meerdere formules (bijv. `…-groningen` én `…-hemelum`)                | Disambigueren (zie hieronder); lukt dat niet → **harde fout** met kandidatenlijst. |

**Disambiguatie bij meerdere kandidaten**

1. **Bestaande uitvoer-`.mvsa`** (hergeneratie naar hetzelfde pad; default
   sibling is `<stam>.vsa.mvsa`): gebruik `template_opgegeven` als die
   staat, anders `template` — dat is de id waarmee de conversie eerder
   werd aangeroepen (mogelijk een alias). Die hint moet bij de kandidaten
   voor deze formule/soort/`toon` horen.
2. Anders: **bron** uit catalogus-leaf / bestandsnaam / `bron.uitgangspunt`
   (Liturgikon ≡ Hemelum), als dat precies één kandidaat overlaat.
3. Anders: geef `--template` (of regenereer een bestaande `.mvsa`).

Implementatie: `vsa.template_library.select_template_id` /
`list_templates_for_soort_toon`.

## T4 — suggestie bij mappingfout

Als `map_vsa_to_template` faalt (bijv. hoogte-mismatch) blijft dat een
**harde fout** (geen stille andere formule). De CLI mag daarna andere
library-ids voor dezelfde `soort`+`toon` **alleen in het geheugen**
proberen. Formules met dezelfde `formula_id` (via `same_as`) tellen niet
als alternatief. Past er minstens één: meld die id’s en een kopieerbaar
`vsa mvsa … --template …`-commando in de hint. Geen interactieve vraag.

Implementatie: `vsa.vsa_mvsa.find_fitting_alternate_templates` /
`format_alternate_template_hint`.

## T2 — melodiestem (detail)

VSA is één melodielijn. Die lijn is **vaak** de sopraan van de formule, maar
soms de alt (of een andere stem) in de koorzetting.

| Parameter      | Default | Betekenis                                                                                               |
| -------------- | ------- | ------------------------------------------------------------------------------------------------------- |
| `melody_voice` | `S`     | Template-sleutel in `pitches` waarmee VSA-hoogten worden vergeleken; MVSA-regel die de VSA-pitch krijgt |

Toegestaan: `S`, `A`, `T`, `B` (stem moet in elk gebruikt event `pitches`
voorkomen). Ontbrekende sleutel → mappingfout met duidelijke hint.

CLI (geïmplementeerd; schets-output):

```text
vsa mvsa pad/naar.vsa --template kondak-toon-1-groningen
vsa mvsa pad/naar.vsa --template kondak-toon-1-groningen --melody A
vsa mvsa --list-templates
```

Implementatie: `vsa.vsa_mvsa` + `vsa.template_library`. Praktijklessen:
[conversion-lessons.md](conversion-lessons.md).

## T5 — recite (detail)

| Situatie                                                       | Emit                                                                         |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Template-`role: recite` (kwarten)                              | `(…)` + één hoogte-slot                                                      |
| Opeenvolgende lettergrepen, zelfde VSA-toon, **default-kwart** | mag tot recite worden samengevoegd (ook over cadens→recite, bijv. `heb-ben`) |
| Zelfde toon maar `_` / `_.` / …                                | **geen** recite-collapse; ELM op eigen L-positie                             |
| Melisma (`&` in VSA)                                           | één L-positie met `&` in ELM/hoogte; geen stil droppen van lege noten        |

## T6 — schets-documentvorm & waarschuwingen

De emit van `vsa mvsa` schrijft een **schets** die dezelfde opbouw volgt
als de gekuiste bestanden in `bibliotheek/.../_klaar_voor_acceptatie`
(minus handmatige polish). Volgorde:

1. **Frontmatter** — nuttige catalogusvelden uit de VSA, in vaste volgorde:
   `titel`, `taal`, `soort`, `toon` (die twee direct onder elkaar), daarna
   **`template`** (feitelijk gebruikte formule-id na alias/`same_as`, T1) en
   zo nodig **`template_opgegeven`**, dan `partituur`, `bron`,
   `gelegenheid` / `gelegenheden`, `zoektekst`, eventueel `gebruikt-in` /
   `corpus_id`. Geen `do` / `mode` / `tempo` in YAML.
2. **Oorspronkelijke VSA** als commentaarblok (ELM-foutzoeken).
3. **Meta-commentaar** — bronpad, template-pad/id (T1), notatie (ag-vsa).
4. **Waarschuwingen** — algemene schets-banner; specifieke
   `# WAARSCHUWING:`-regels alleen als er later weer emit-detecties zijn
   (herhaalde melisma-ELM zoals `_&_` is géén hint meer: stem-sync).
5. **`@`-kop** — `@title`; daarna playback **`@do`**, **`@mode`**,
   **`@tempo`** (default 180 voor tropaar/kondak; VSA-frontmatter-tempo
   wordt genegeerd) **direct boven** `@oct` (uit template-`voice_oct`).
6. **Geen** `@speelplan` en **geen** `@blok`.
7. **Secties** — `@sectie cyclus-1` (eerste cycle-lengte uit
   template-`cycle`), `@sectie herhaling` (midden), `@sectie laatste`
   (frase-id `final`, meestal `laatste`). **Uitzondering:** toon 3 —
   geen drie sectiekoppen (zoals in de acceptatie-MVSA’s).

Implementatie: `vsa.vsa_mvsa.emit_mapped_document` /
`clean_emit_frontmatter` / `section_id_for_phrase_index`.

## T7 — verbetercyclus

```text
VSA → vsa mvsa --template <id> [--melody …]
    → controle (MuseScore / validate / oor)
    → feedback → YAML (of zelden motor) + notes/
    → corpus bijwerken → regressie
```

Goedgekeurde corpus-MVSA is referentie voor dat stuk; opnieuw genereren na
template-bump is bewust (diff / checklist).

## Relatie met andere contracten

| Onderwerp                          | Hub                                                                        |
| ---------------------------------- | -------------------------------------------------------------------------- |
| Event-hypotheses H1–H9, `of`-paden | [mapping-vsa.md](mapping-vsa.md)                                           |
| Melisma / lyrics in export         | [canonical-checklists](../formats/canonical-checklists.md) K2/K3, M5a, S13 |
| MVSA-syntax (recite, ELM, `\.`)    | [specification-mvsa](../specification-mvsa/README.md)                      |
| Library-mappen                     | [library/README.md](library/README.md)                                     |

## Wijzigingsbeleid

1. Norm alleen in **dit** bestand (T-ids) of in mapping-vsa voor H-details.
2. Implementatie (mapper/emit/CLI) noemt T-id in tests en PR.
3. Agent: zie `.cursor/rules/contracten-eerst.mdc` — ook dit pad.
