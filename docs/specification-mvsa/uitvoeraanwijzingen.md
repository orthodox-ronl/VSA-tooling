# Uitvoeraanwijzingen op de lyrics-regel

**Status:** **fase 1–5 actief** in code en export: cesuur `[//]`; dynamiek
`ppp`–`fff`; `[adem]` / `[ferm]`; `[cresc]`/`[/cresc]` en `[dim]`/`[/dim]`;
`[rit]` / `[atempo]`; plus `@tempo` (optioneel tempo-woord). Fase 6
(import-roundtrip) staat nog open — zie §7.

**Doel:** een **generiek** mechanisme voor uitvoeraanwijzingen op de
mvsa-lyrics-regel (`L:` / `L1:` / …), met gesloten `[token]`-syntax —
zonder de L↔SATB-sync te breken.

Gerelateerd:

- Lyrics-regels: [syntax.md § Lyrics](syntax.md#6-lyrics-regel-l)
- Dubbele maatstreep / sectie-einde: [syntax.md § Einde](syntax.md#einde)
- Cues: [`@tekst` in keywords.md](keywords.md#tekst)
- Open backlog: [open-points.md](open-points.md)
- VSA control-tokens (andere laag):
  [control-token](../terminologie/control-token.md)
- Coria-cesuur-timing: `src/vsa/musicxml_coria_timing.py`

**Termen:** *uitvoeraanwijzing*, *cesuur* en *beurtgrens* zijn hier
**mvsa-drafttermen**. Ze horen nog niet in de org-glossary
(`bron/docs/specs/terminologie.md`) tot ze normatief worden vastgelegd.

---

## 1. Generiek model

### 1.1 Wat is een uitvoeraanwijzing?

Een **uitvoeraanwijzing** is een markering in de **representatie** (`.mvsa`)
die zegt hoe er op een plek gespeeld of onderbroken wordt — los van de
lettergreeptekst zelf.

| Laag                      | Rol                                                                              |
| ------------------------- | -------------------------------------------------------------------------------- |
| Abstracte betekenis       | Bijv. `caesura`, `dyn_mf`, `breath`, `cresc`, …                                  |
| Schrijfwijze op `L:`      | Gesloten `[token]` dat **vóór** of **na** een L-positie plakt (zie §1.2)         |
| Export (glyph / MusicXML) | Per kind vastgelegd; MuseScore-partituur vs Coria-playback kunnen verschillen    |
| Catalogus-metadata        | **Niet** hier — hoort niet in `zangstuk.yaml` / variant-metadata                 |

De markering is **geen** lettergreep en neemt **geen** lengte-positie in.
Stemregels wijzigen niet.

### 1.2 Plaatsing en aanhechting

| Regel                                    | Ontwerp                                                                                         |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Alleen op lyrics-regels                  | Ja (`L:`, `L1:`, `lyrics:`, …)                                                                  |
| Nooit op stemregels                      | Ongeldig                                                                                        |
| Nooit midden in een lettergreep          | Ongeldig (`hei[p]lig`)                                                                          |
| Geen lengte-positie                      | Sync telt marks niet (zelfde klasse als leestekens)                                             |
| Gesloten registry                        | Onbekende `[…]` op L → validate-fout; vrije tekst = `@tekst`, niet `[…]`                        |
| Binnen recite `( … )` vóór `)`           | Ongeldig — marks horen ná het L-stuk (na `)` en optionele ELM)                                  |

Twee aanhechtingswijzen (vanaf dag 1 in het model):

| Attach    | Betekenis                           | Typische tokens                            |
| --------- | ----------------------------------- | ------------------------------------------ |
| `before`  | Plakt aan de **volgende** L-positie | dynamiek, start cresc/dim, `[rit]`, …      |
| `after`   | Plakt aan de **vorige** L-positie   | `[//]`, `[adem]`, `[ferm]`, stop cresc/dim |

Volgorde in de bron rond één lettergreep:

```text
[marks_before]*  lettergreep  ELM/melisma  leesteken  [marks_after]*  spatie of maatstreep
```

Spatie na `]` vóór een lettergreep mag (`[mf] Heer`); die spatie hoort niet bij
het token. Normalize mag die spatie behouden of tot één spatie terugbrengen —
niet het token van de lettergreep losknippen.

### 1.3 IR (voorstel)

Uitbreiding op `LPosition` (conceptueel):

```text
LPosition
  …bestaand (recite, syllables, elms, links, …)…
  marks_before: list[Mark]
  marks_after:  list[Mark]

Mark
  kind: str                    # registry-id
  raw: str                     # token zonder haken, bv. "//", "mf"
  span_role: none | start | stop
```

**Exportankers:**

- `attach=after` → laatste klinkende noot van die positie (melisma: laatste
  slot; recite-playback: laatste lettergreep-noot)
- `attach=before` → eerste klinkende noot van die positie
- Trajecten: `start` / `stop` op die ankers

Geëxporteerde lyric-`<text>` bevat **geen** `[token]`-tekst.

### 1.4 Coria vs partituur (algemeen)

- **Partituur (MSCZ / print-MXL):** altijd de juiste MusicXML-vorm voor
  MuseScore (articulatie, dynamiek, wedge, woorden).
- **Coria-playback:** `sanitize_coria_importer` **stript `<notations>`** van
  noten. Articulaties (cesuur, adem, fermata) verdwijnen daar tenzij een
  **timing-transform** ze eerder omzet (zoals bij cesuur → kwart-rust).
  Directions (`<dynamics>`, `<wedge>`, `<words>`, `<sound tempo>`) blijven
  eerder behouden; volume-/tempo-effect in Coria is niet altijd gegarandeerd
  (zie kolom Coria in §3).

---

## 2. Beurtgrens (dubbele maatstreep) — buiten deze registry

De **dubbele maatstreep** (twee verticale strepen; met herhaling: dubbele punt
plus die strepen) blijft de structurele **beurtgrens**: einde van een serie
koormaten, waarna priester of diaken weer het woord krijgt. Dat is **geen**
L-`[…]`-token en wordt **niet** vervangen door `[//]`.

| Laag             | Wat de dubbele maatstreep is                                                                                                      | Wat het níet is                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Bron-syntax      | Maatstreep op alle LSATB-regels; expliciet sectie-einde ([syntax § Einde](syntax.md#einde))                                       | Geen lettergreep-markering; geen `[//]`       |
| Semantiek        | Beurtgrens: koor (tijdelijk) klaar; ruimte voor cue / andere stem in de liturgie                                                  | Geen “adem even midden in één zin”            |
| Partituur (MSCZ) | Dubbele maatstreep (MusicXML `light-light`); herhalingsvorm → repeat-end waar van toepassing                                      | Geen cesuur-glyph op de laatste noot          |
| Coria / oefenen  | Bestaande **pauzemaat** (hele-nootrust, lyric `[PAUZE]`) ná die grens — oefenhulp (checklist M12/M15)                             | Geen cesuur-kwart-rust; geen L-aanwijzing     |

Typische combinatie (blijft geldig):

```text
L: … laatste koorfrase ||
S: …                 ||

@tekst "P: …"
L: … koorantwoord |
S: …              |
```

Playback: dubbele streep → pauzemaat → cue → verder. Mid-flow `@tekst` heeft
dezelfde pauzelogica (M15).

| Situatie                                                                  | Gebruik                                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Koor stopt; priester/diaken spreekt; daarna weer koor                     | Dubbele maatstreep (meestal plus `@tekst`) — beurtgrens                                |
| Binnen doorlopend koorzingen een korte onderbreking op één lettergreep    | `[//]` op de L-regel — uitvoeraanwijzing (cesuur)                                      |
| Alleen bladtekst zonder maatstructuur te wijzigen                         | Alleen `@tekst` (vervang de dubbele maatstreep niet als je wél een beurtgrens bedoelt) |

Eventuele latere verfijning van de oefenpauze (lengte, wel/geen lyric
`[PAUZE]`, zichtbaarheid in partituur) is een **apart** open punt — niet
gekoppeld aan cesuur-implementatie.

---

## 3. Canonieke tokenlijst (roadmap)

**Legende Coria**

| Label                 | Betekenis                                                                 |
| --------------------- | ------------------------------------------------------------------------- |
| ja (transform)        | Vóór sanitize omzetten naar speelbaar effect                              |
| richting behouden     | Als `<direction>`; volume/tempo niet gegarandeerd                         |
| nee                   | `<notations>` verdwijnt in Coria-sanitize; geen beloofde speelduur        |

**Registry-activering:** alles hieronder staat in de docs; in code worden
tokens pas geaccepteerd vanaf hun **fase** (onbekend tot die tijd).

### 3.1 Puntmarkeringen — `attach=after`

| Token                  | kind       | Betekenis                                                 | MusicXML (partituur)                                        | MuseScore                 | Coria-playback                                                                      | Fase |
| ---------------------- | ---------- | --------------------------------------------------------- | ----------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------- | ---- |
| `[//]` of `[//`+ELM`]` | `caesura`  | Liturgische cesuur; optionele **pauze-duur** in ELM-stijl | `<caesura/>` of `<caesura elm="…"/>` op laatste noot        | Standaard caesura (glyph) | **ja (transform):** rust alle parts, duur uit ELM (default `~` = kwart), geen lyric | 1    |
| `[adem]`               | `breath`   | Ademteken (korter dan cesuur)                             | `<articulations><breath-mark/></articulations>`             | Breath mark (komma)       | **nee** in v1; latere korte-rust-transform optioneel                                | 3    |
| `[ferm]`               | `fermata`  | Fermate op die positie                                    | `<fermata type="upright"/>` in `<notations>`                | Fermata boven noot        | **nee** in v1; MuseScore-audio mag wel verlengen                                    | 3    |

### 3.2 Dynamiek — `attach=before`

| Token    | kind       | MusicXML                                              | MuseScore     | Coria                 | Fase |
| -------- | ---------- | ----------------------------------------------------- | ------------- | --------------------- | ---- |
| `[ppp]`  | `dyn_ppp`  | `<direction>…<dynamics><ppp/></dynamics>…`            | Dynamiek ppp  | richting behouden     | 2    |
| `[pp]`   | `dyn_pp`   | `<pp/>`                                               | pp            | idem                  | 2    |
| `[p]`    | `dyn_p`    | `<p/>`                                                | p             | idem                  | 2    |
| `[mp]`   | `dyn_mp`   | `<mp/>`                                               | mp            | idem                  | 2    |
| `[mf]`   | `dyn_mf`   | `<mf/>`                                               | mf            | idem                  | 2    |
| `[f]`    | `dyn_f`    | `<f/>`                                                | f             | idem                  | 2    |
| `[ff]`   | `dyn_ff`   | `<ff/>`                                               | ff            | idem                  | 2    |
| `[fff]`  | `dyn_fff`  | `<fff/>`                                              | fff           | idem                  | 2    |

Geen `fp` / `sfz` / … tot er echte behoefte is (nieuwe rij, geen modelswijziging).

### 3.3 Trajecten (hairpins)

| Tokens                     | kind     | MusicXML                                      | MuseScore           | Coria                              | Fase |
| -------------------------- | -------- | --------------------------------------------- | ------------------- | ---------------------------------- | ---- |
| `[cresc]` … `[/cresc]`     | `cresc`  | `<wedge type="crescendo">` … `stop`           | Crescendo-hairpin   | richting behouden; geen envelope   | 4    |
| `[dim]` … `[/dim]`         | `dim`    | `<wedge type="diminuendo">` … `stop`          | Diminuendo-hairpin  | idem                               | 4    |

Regels: start heeft later een matching stop in dezelfde L-stroom; nesten
verboden; wees-start/stop → fout. Alias `[decresc]` = `[dim]` (normalize →
`[dim]`). Start = `before`, stop = `after`.

### 3.4 Tempo

| Vorm                       | Plaats                         | Betekenis                                      | MusicXML / MuseScore                                      | Coria                                              | Fase |
| -------------------------- | ------------------------------ | ---------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------- | ---- |
| `@tempo 72`                | sticky directive boven systeem | Metronoomkwart = 72 (canonieke eenheid: kwart) | `<metronome>` / `<sound tempo="72"/>`                     | **ja** als `<sound tempo>` in playback landt       | 5    |
| `@tempo 72 "Andante"`      | idem                           | tempo + optioneel woord                        | metronome + words                                         | getal wel; woord visueel                           | 5    |
| `[rit]`                    | L, `before`                    | ritardando vanaf die positie                   | `<words>rit.</words>`                                     | woorden behouden; geleidelijke vertraging niet v1  | 5    |
| `[atempo]`                 | L, `before`                    | a tempo                                        | `<words>a tempo</words>`                                  | idem                                               | 5    |

`@tempo` staat in [keywords.md](keywords.md). CLI `--tempo` op `audio`
blijft een render-override en is iets anders.

### 3.5 Bewust níet in deze registry

| Idee                                        | Waarom niet                                                      |
| ------------------------------------------- | ---------------------------------------------------------------- |
| Dubbele maatstreep als `[…]`-token          | Blijft maatstreep / beurtgrens (§2); Coria-`[PAUZE]` hoort daar  |
| `[*]` / `[/]`                               | VSA control-tokens (andere laag)                                 |
| Los Unicode-cesuurteken als primaire syntax | Vervangen door `[//]` (bewuste type-drempel)                     |
| Vier MuseScore-cesuur-glyphs als tokens     | Eén `caesura`; glyph-parameter alleen later als nodig            |
| Vrije `[tekst]`                             | Gebruik `@tekst`                                                 |
| Sectie-tempo alleen op L                    | Sectie-tempo = `@tempo`                                          |

---

## 4. Afgrenzing (samenvatting)

| Concept                         | Relatie                                                                      |
| ------------------------------- | ---------------------------------------------------------------------------- |
| Enkele maatstreep               | Frasegrens op alle LSATB-regels; deel van maatstructuur                      |
| Dubbele maatstreep              | Beurt-/sectiegrens + Coria-`[PAUZE]` — **geen** cesuur (§2)                  |
| `@tekst`                        | Bladcue / rubriek; geen dynamiek/cesuur                                      |
| Leestekens (`,` `.` …)          | Orthografie op L; geen L-stuk; geen uitvoeraanwijzing                        |
| VSA `*` / `[*]` / `[/]`         | Andere notatielaag (eenstemmig); niet hergebruiken als mvsa-cesuur           |
| ELM / `&` melisma               | Bepalen duur en slots; `after`-marks komen erna en delen de lengte-positie   |

---

## 5. Voorbeelden

### Cesuur `[//]` (fase 1)

```text
L: Eén is hei_-lig[//] | Eén is Heer,_[//] | Je-zus Chris_-tus_&_&_,[//] |
S: do   re mi_-sol     | do   re mi__      | do re  mi__    sol&la&si     |

L: (Eén is heilig),[//] |
S: do                   |
```

**Pauze-duur (Coria / audio):** na `//` mag een gewone ELM staan. Die stuurt
alleen de **ingevoegde rust** bij playback; op het blad blijft één
cesuurteken. Zonder ELM geldt default `~` (kwart), hetzelfde als VSA.

| Token               | Coria-rust                         |
| ------------------- | ---------------------------------- |
| `[//]`              | kwart (`~`)                        |
| `[//.]`             | achtste                            |
| `[//..]`            | zestiende                          |
| `[//_]`             | half                               |
| `[//_.]`            | gepunteerde half                   |
| `[//__]`            | heel                               |
| `[//-.]` / `[//~.]` | gepunteerde kwart                  |

`[//~]` en `[//-]` zijn geldig (ook kwart); `normalize` herschrijft ze naar
`[//]`. Ongeldige tekens na `//` (bijv. `[//@]`) → validate-fout.

```text
L: stil_[//_] dan_ verder_ |
S: do    -     re   mi_    |
```

Ongeldig:

```text
L: [//] Eén is heilig |     # after zonder vorige L-stuk
S: [//] do re mi |          # niet op stemregel
L: (Eén is[//] heilig) |    # niet binnen recite-haakjes
L: a_[//@] |                # geen geldige ELM-duur
```

### Dynamiek (fase 2)

```text
L: [mf]Heer_ is groot_ |
S: do    re mi_  fa_   |
```

### Crescendo / diminuendo (fase 4)

```text
L: [cresc]Heer_ is groot_[/cresc] |
S: do       re mi_  fa_           |

L: [dim]zacht_ en stil_[/dim] |
S: do    re_   mi_            |
```

Alias: schrijf `[decresc]…[/decresc]` mag; `normalize` herschrijft naar `[dim]…[/dim]`.

### Tempo (fase 5)

```text
@tempo 72 "Andante"
L: [rit]Heer_ is groot_ [atempo]Amen_ |
S: do       re mi_  fa_            sol_ |
```

`@tempo` zet de afspeelsnelheid (`sound tempo`); het optionele woord en
`[rit]` / `[atempo]` zijn zichtbare aanwijzingen. Geleidelijke vertraging
in Coria is geen v1-eis.

### Beurtgrens (bestaand — geen L-token)

```text
L: ont-ferm U o-ver ons ||
S: …                    ||

@tekst "P: …"
L: A_ -men_ |
S: …        |
```

---

## 6. Validate / normalize / kuiser / import (per actieve fase)

| Pad             | Gedrag wanneer het token actief is                                                         |
| --------------- | ------------------------------------------------------------------------------------------ |
| **validate**    | Onbekend `[…]` → fout; verkeerde attach/wees-span → fout; `[` op stemregel → fout          |
| **normalize**   | Canonieke tokenvorm; alias `[decresc]` → `[dim]`; marks blijven geplakt                    |
| **kuiser**      | Raakt marks niet aan (geen strip, geen verplaatsing)                                       |
| **import**      | Roundtrip naar canonieke `[token]` op de juiste L-positie (fase 6 voor alle actieve marks) |
| **L↔SATB-sync** | Marks tellen niet mee                                                                      |

---

## 7. Implementatiefasen

| Fase  | Inhoud                                                                                                                                              | Docs sync                                          |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **0** | Ontwerp (docs) — **klaar**                                                                                                                          | deze pagina + pointers                             |
| **1** | Kern + `[//]` — **klaar** (registry, parser `marks_*`, validate, kuiser-skip, export `<caesura/>`, Coria-rust; ELM-duur op `[//`+ELM`]`)            | validation / formats / guides                      |
| **2** | Dynamiek `ppp`–`fff` — **klaar** (vóór lettergreep; MusicXML `<dynamics>`; partituur sopraan; playback alle parts)                                  | registry-status; voorbeelden                       |
| **3** | `[adem]` + `[ferm]` — **klaar** (partituur `<breath-mark/>` / `<fermata/>`; Coria stript notations)                                                 | idem                                               |
| **4** | `[cresc]`/`[/cresc]` + `[dim]`/`[/dim]` — **klaar** (span-IR; `<wedge>`; partituur sopraan; playback alle parts; alias `[decresc]`→`[dim]`)         | idem                                               |
| **5** | `@tempo` (+ optioneel woord) + `[rit]`/`[atempo]` — **klaar** (`sound tempo`; L-woorden zichtbaar; geen geleidelijke rit-envelope)                  | keywords.md                                        |
| **6** | Import-roundtrip actieve marks; liturgische voorbeelden; glossary-PR op `bron` indien normatief                                                     | checklist/voorbeelden                              |

---

## 8. Bewust open (niet blokkerend)

- Soft/optional-varianten (vergelijk VSA `[*?]`).
- Cesuur midden in een melisma (niet op het laatste slot) — fase 1: alleen einde van de lengte-positie.
- Meerdere marks op één positie (bijv. `[mf]` + later `[//]` op dezelfde zin) — toestaan wanneer attach niet botst; details bij implementatie.
- Adem → korte Coria-rust-transform.
- Verfijning oefenpauze na dubbele maatstreep (apart van dit mechanisme).
- Org-glossary-entries.
