# Contract: VSA + template → MVSA (T-reeks)

**Status:** normatief voor tooling en agent-werk (draft v0).  
**Canonieke hub** voor `vsa mvsa` / template-instance / emit.  
Uitwerking van hypotheses: [mapping-vsa.md](mapping-vsa.md).  
In de index: [contract-index](../formats/contract-index.md).

Bij **elk** werk aan mapper, emit, `vsa mvsa`, of corpus-regeneratie:
lees de relevante **T-id** hier; wijzig normatieve tekst **alleen** hier
(elders linken). Noem het T-id in PR/tests/uitleg.

## Architectuur (T0)

| Laag                           | Rol                                                                        |
| ------------------------------ | -------------------------------------------------------------------------- |
| **Template-id**                | Bijv. `kondak-toon-1` (map `library/<id>/`); CLI-alias later (`kondak-t1`) |
| **Template** (`template.yaml`) | Formule: frasen, rollen, ankers, `do`/`mode`, speelplan                    |
| **Motor**                      | Gedeelde mapper + emit voor alle template-ids                              |
| **Instance**                   | Afgeleide MVSA (schets tot goedgekeurd in corpus)                          |

Eén motor, veel templates. Toon-specifieke code alleen als het eventmodel
tekortschiet — eerst YAML proberen (T7).

## Checklist T1–T7

| Id  | Regel                                | Kort                                                                                                                                                                                                                                                          |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T1  | Template-id                          | Elke afgeleide MVSA noemt template-pad of canonieke id in commentaar/`@`-meta. Geen stille default zonder vermelding.                                                                                                                                         |
| T2  | Melodiestem uit VSA                  | **Default:** VSA-melodie matcht template-`pitches.S` en vult de MVSA-**S**-regel. **Override:** `--melody A` (enz.) → match op `pitches.A` (of T/B); VSA-pitch vult die MVSA-stem; overige stemmen uit template op hetzelfde event.                           |
| T3  | Overige stemmen                      | Niet-melodiestemmen: laddergraden uit template-`pitches.*` op het **zelfde** gekoppelde event (synchroon met melodiekeuzes H4–H8).                                                                                                                            |
| T4  | ELM / EHM                            | **ELM:** VSA wint (duur). **EHM:** exacte match op template-`pitches.<melodiestem>` t.o.v. template-`do`/`mode` (H5/H9). Mismatch → harde fout, geen stil hold.                                                                                               |
| T5  | Recite & ELM in emit                 | MVSA-recite `(…)` = standaardkwart per lettergreep; **geen** ELM binnen haakjes. Same-pitch-collapse alleen voor default-kwarten. Halve noten (`_`) blijven eigen L-posities. Melisma: zie ook K2/K3 / mapping H8.                                            |
| T6  | Schets-documentvorm & waarschuwingen | Afgeleide MVSA: gekuiste frontmatter; VSA-commentaar; bron/template/notatie; schets-banner + `# WAARSCHUWING:`; `@title`/`@do`/`@mode`/`@tempo`/`@oct`; systemen **zonder** `@speelplan`/`@blok`; secties `cyclus-1` / `herhaling` / `laatste` (niet toon 3). |
| T7  | Corpus & verbetercyclus              | Per template-id: corpus `.vsa` + goedgekeurde `.mvsa`. Eerst template-YAML bijstellen; motor alleen bij structurele gaten. Na wijziging: steekproef/regressie op corpus. Lessen in `library/<id>/notes/`.                                                     |

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
vsa mvsa pad/naar.vsa --template kondak-toon-1
vsa mvsa pad/naar.vsa --template kondak-toon-1 --melody A
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

1. **Frontmatter** — alleen catalogusvelden (`titel`, `partituur`, `toon`,
   `taal`, `bron`, `soort`, `gelegenheid`, `zoektekst`). Geen `do` /
   `mode` / `tempo` / `template` in YAML (playback staat in `@`-regels).
2. **Oorspronkelijke VSA** als commentaarblok (ELM-foutzoeken).
3. **Meta-commentaar** — bronpad, template-id (T1), notatie (ag-vsa).
4. **Waarschuwingen** — algemene schets-banner plus eventuele specifieke
   `# WAARSCHUWING:`-regels (o.a. melisma met herhaalde niet-default ELM:
   controleer bron `{/&/x_}` vs `{/&/x_&_}`).
5. **`@`-kop** — `@title`, `@do`, `@mode`, `@tempo` (default 180 voor
   tropaar/kondak; VSA-frontmatter-tempo wordt genegeerd), `@oct` uit
   template-`voice_oct`.
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
