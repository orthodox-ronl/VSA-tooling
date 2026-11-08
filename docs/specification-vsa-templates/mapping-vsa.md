# Mapping VSA ↔ vsa-template (experimenteel)

Status: **hypotheses + architectuurkeuze VSA→template-instance**; geen normatieve VSA 1.0-wijziging.

**Normatieve checklist (T1–T7):** [vsa-mvsa-contract.md](vsa-mvsa-contract.md)
(ook in [contract-index](../formats/contract-index.md)). Dit document houdt
de H1–H9-details; de T-reeks is leidend voor CLI/emit/corpus.

Implementatie: [`src/vsa/template_mapping.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/template_mapping.py)
(frase-toewijzing) en
[`src/vsa/template_instance.py`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/src/vsa/template_instance.py)
(event-niveau; melodiestem default S — **T2**).

## Doel

Beschrijven hoe een [VSA](@)-tekstblok (één melodielijn) op
[template-events](template-event@) van een [vsa-template](@) landt, zodat
de overige stemmen uit de template meegenomen kunnen worden naar een
afgeleide (bijv. MVSA / MusicXML) — zonder lyrics in de template-syntax.

## Architectuur: VSA→template-instance (besloten)

Default (**T2**): VSA = formule-melodie op **S**. Override: VSA matcht
`pitches.A` (of T/B) als die de melodielijn is.

| Stem                        | Toonhoogte / contour                      | Ritme / optional / split-merge                 |
| --------------------------- | ----------------------------------------- | ---------------------------------------------- |
| **Melodiestem** (default S) | uit [VSA](@) + [do-context](@)            | uit VSA (scopes, ELMs, syllaben)               |
| **Overige**                 | uit template-[laddergraden](laddergraad@) | **zelfde** eventkeuzes als voor de melodiestem |

### ELM vs EHM (bindend)

| Modifier                                              | Rol in de instance                                                                                                                                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ELM** (`_`, `__`, `~`, `-.`, `~.`, …)               | **VSA bepaalt de werkelijke duur.** Template-`duration` is alleen een formule-indicatie op het blad; in de uitgewerkte partituur wint de VSA-ELM. A/T/B krijgen **dezelfde** duur als S op dat event (H5). |
| **EHM** (`/`, `\`, `~`, …) / resulterende laddergraad | **Moet precies matchen** op template-`pitches.S` (zelfde klinkende toon t.o.v. `do`/`mode`). Geen “ongeveer”; mismatch → harde fout (H9), geen stil hold.                                                  |

Kort: duur mag afwijken van de formule; **toonhoogte niet**.

## Tekstregels → template-frasen

Elke **tekstfrase** (zie frasescheiders hieronder) wordt in volgorde toegewezen
aan [template-frase](template-frase@)-ids.

### Frasescheiders en print-wraps

Zangers zien in een doorlopende tekst waar formulefrasen beginnen/eindigen.
De mapper volgt dezelfde grenzen.

| Markering                 | Rol voor zangers / blad               | Rol voor `vsa mvsa`                                                                                 |
| ------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `*`                       | Frasescheiding                        | Sluit de huidige tekstfrase                                                                         |
| `**`                      | Sterke scheiding vóór **laatste**     | Zelfde split als `*` (vaak genormaliseerd tot één `*` in afgeleide tekst)                           |
| `/`                       | Frasescheiding of maatstreep (blad)   | Trailing `/` op een regel telt als scheiding voor ensure/telling; losse `/` middenin blijft EHM     |
| `//`                      | Sterke scheiding / dubbele maatstreep | Trailing `//` idem; **leidende** `//` op de laatste frase is blad-/EHM-conventie (géén extra split) |
| *(geen markering)*        | —                                     | Elke **niet-ingesprongen** regel = één frase                                                        |
| Ingesprongen vervolgregel | Te lange frase op papier              | Hoort bij de **vorige** frase (geen nieuwe grens)                                                   |

Markeringen zijn **niet verplicht**. Voor betrouwbare mapping: zet `*` (of
`**` vóór laatste) aan het eind van elke tekstfrase, of vertrouw op één
frase per niet-ingesprongen regel.

**Print-wrap:** staat het vervolg van dezelfde frase op de volgende regel,
spring die regel in (spaties/tabs vooraan). Zonder scheiders zou een harde
regeleinde anders ten onrechte als nieuwe frase tellen — dat geeft vaak
`VSA-TEMPLATE-TEXT-MAPPING` of `VSA-TEMPLATE-REQUIRED-SLOT-UNUSED` op een
«te korte» frase.

### Legacy (nog ondersteund)

| Vorm            | YAML                         | Betekenis                                      |
| --------------- | ---------------------------- | ---------------------------------------------- |
| cycle-form      | `cycle` + `final`            | cyclisch herhalen tot één regel resteert       |
| sequence-form   | `sequence`                   | vaste volgorde, geen herhaling                 |

`cycle: ["1", "2"]` + `final: laatste` compileert naar:

```yaml
text_mapping:
  - repeat: ["1", "2"]
    until: final
  - phrase: laatste
```

### `text_mapping` (algemeen)

Lijst van **stappen** (in volgorde):

| Stap        | YAML-vorm                                      | Effect                                    |
| ----------- | ---------------------------------------------- | ----------------------------------------- |
| enkel       | `phrase: "1"`                                  | één tekstregel → frase `1`                |
| reeks       | `sequence: ["1", "3", "2a"]`                   | vaste reeks, één regel per id             |
| herhaling   | `repeat: ["2", "3"]` + `until`                 | cyclisch toewijzen tot stopconditie       |

#### `until: final`

Herhaal het patroon **cyclisch** over zoveel regels als nodig, zodat de
**tail** (alle stappen ná deze `repeat`) precies overblijft. Typisch eindigt
de tail op `phrase: laatste`.

**Geen eis** dat het aantal regels vóór `laatste` een veelvoud van `k` is.
Bij `k = 2` en `n = 7` regels: `1, 2, 1, 2, 1, 2, laatste`.

#### `until: { remaining: N }`

Stop met herhalen wanneer nog **N** regels over zijn; die vallen op de tail
(meestal `sequence: [...]`). Voorbeeld tropaar toon 1 (variant met slot
`1, 1a, 1a, 2`):

```yaml
- repeat: ["1", "2"]
  until:
    remaining: 4
- sequence: ["1", "1a", "1a", "2"]
```

### Voorbeelden (bladnotatie → `text_mapping`)

| Blad / gewoonte                         | `text_mapping`                                                        |
| --------------------------------------- | --------------------------------------------------------------------- |
| `\|\|: 1, 2 :\|\| laatste`              | `repeat [1,2] until final` + `phrase laatste`                         |
| `1 \|\|: 2, 3 :\|\| laatste`            | `phrase 1` + `repeat [2,3] until final` + `phrase laatste`            |
| `1, 3, 1, 2, 3, 1, 2a, 4`               | `sequence: [1, 3, 1, 2, 3, 1, 2a, 4]`                                 |
| `1, 2, 3, \|\|: 4, 5, 3a :\|\| laatste` | `sequence [1,2,3]` + `repeat [4,5,3a] until final` + `phrase laatste` |

## `mapping_plans` (meerdere plannen)

Als één template op het blad **meerdere cycle-notaties** heeft (bijv. tropaar
toon 1), of de toewijzing **afhangt van het aantal tekstregels**:

```yaml
mapping_plans:
  - id: standard
    label: "||: 1, 2 :|| laatste"
    when:
      default: true
    steps:
      - repeat: ["1", "2"]
        until: final
      - phrase: laatste
  - id: extended-close
    label: "||: 1, 2 :|| 1, 1a, 1a, 2"
    when:
      stanza_count: 5
    steps:
      - repeat: ["1", "2"]
        until:
          remaining: 4
      - sequence: ["1", "1a", "1a", "2"]
```

Selectie: `select_mapping_plan(doc, stanza_count)` — eerste plan waarvan
`when` matcht; anders plan met `when.default: true`.

| `when`-sleutel       | Match                                     |
| -------------------- | ----------------------------------------- |
| `default: true`      | fallback                                  |
| `stanza_count`       | exact aantal regels                       |
| `stanza_count_mod`   | `{ mod: 3, remainder: 0 }` → `n % 3 == 0` |
| `stanza_count_min`   | minimaal n regels                         |
| `stanza_count_max`   | maximaal n regels                         |

Voorbeeld **3n regels** met prefix + cycle + afwijkende slot:

```yaml
- id: triple
  when:
    stanza_count_mod:
      mod: 3
      remainder: 0
  steps:
    - phrase: "1"
    - repeat: ["2", "3", "1"]
      until: final
    - phrase: "2a"
    - phrase: laatste
```

## Frase-ankers (inclusief melisma)

| Anchor (YAML) | Bladlabel | Bedoeling                                           |
| ------------- | --------- | --------------------------------------------------- |
| `e.st.`       | `e. st.`  | eerste streek / inzet                               |
| `l.st.`       | `l. st.`  | laatste streek op cadensnoot                        |
| `vl.st.`      | `vl. st.` | voorlaatste streek                                  |
| `l.lgr.`      | `l. lgr.` | start van het **slotmelisma** (laatste lettergreep) |

`l.lgr.` wijst naar een noot **waar nog noten achteraan komen**. Vanaf dat
event tot het einde van de [template-frase](template-frase@) horen **alle**
noten bij de **laatste lettergreep** van de tekst — één syllabe over meerdere
template-events (melisma). In VSA hoort dat te blijken als één [zangelement](@)
met meerdere [muzikale posities](@) (`&` in de modifiers).

## Hypotheses (event-niveau)

| #   | Hypothese                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | Ongemarkeerde VSA-syllaben vóór cadens-scopes vallen op recite. `open` (zelfde graad, eigen event op het formuleblad) wordt in de instance **overgeslagen** als de VSA meteen reciteert — geen dubbele noot. YAML blijft twee events. **Uitzondering open-aanloop:** ongemarkeerde noten op een open-toon die gevolgd worden door *scoped* latere opens (bijv. `o Ge{/bie}{/der}`) horen bij die opens, niet bij recite. **Scoped op recite-toon** mag de recite starten of meedoen (`{\\zijt} Gij…`); ná minstens één ongemarkeerde recite-syllabe gaat een nieuwe scope naar de cadens (H2), ook op dezelfde toon. |
| H2  | Cadens-scopes corresponderen met `cadence`-events, vaak bij `l.st.` of erna.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| H3  | `{/…}` aan het begin van een regel kan `e.st.` van frase `2` (of vergelijkbaar) zijn. Een scoped VSA-noot op een event met `e.st.` / `l.st.` / `vl.st.` krijgt bij voorkeur de anker-weergave (nadruk/klemtoon).                                                                                                                                                                                                                                                                                                                                                                                                     |
| H4  | `optional: true` events: mee als VSA-S dat slot gebruikt, anders weg — voor **alle** stemmen.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| H5  | **ELM:** VSA bepaalt de werkelijke nootlengte; template-`duration` is alleen formuleblad. Die VSA-duur geldt parallel voor A/T/B.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| H6  | Blijft VSA-S op dezelfde graad voor extra syllaben, dan **houden** A/T/B hetzelfde slot-akkoord.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| H7  | **Verplichte** template-slots moet VSA aandoen (eigen syllabe, hold H6, of melisma H8). Ongebruikt verplicht slot aan het eind → **fout**. Een **andere** toon in de cadens overslaan mag alleen via `optional: true` (H4). Rest van een ondergevulde **zelfde-S-run** mag stil weg.                                                                                                                                                                                                                                                                                                                                 |
| H8  | `l.lgr.`: start van een slotmelisma — geankerd event **plus alle volgende** events in de frase op de laatste VSA-syllabe.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| H9  | **EHM/hoogte:** VSA-melodie moet **exact** op een resterend template-slot van de **melodiestem** landen (`pitches.S` default; T2: ook A/T/B). Mismatch → `TemplateInstanceError`; geen stil hold, geen “ongeveer”.                                                                                                                                                                                                                                                                                                                                                                                                   |

### H4 vs H7 (optional vs verplicht)

| Soort template-slot                                                        | VSA doet het slot niet aan                         | Gedrag                                                                                                                                                                                        |
| -------------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `optional: true` (haakjes op het blad)                                     | —                                                  | stil weglaten voor alle stemmen (**H4**)                                                                                                                                                      |
| verplicht (geen `optional`)                                                | —                                                  | **`TemplateInstanceError`** — VSA moet het slot meenemen of de template/VSA corrigeren                                                                                                        |
| verplicht, maar VSA “springt” naar **andere** toon                         | tussenslot(s) met **andere** S-graad               | **fout** tenzij die tussenslots `optional: true` zijn                                                                                                                                         |
| rest van een **zelfde-S-run** na de laatste gebruikte syllabe op die graad | VSA gaat door naar een latere andere toon          | **kwart** (`~`/leeg): mag stil weg. **Half/heel** (`_`/`__`): mapper vult als leeg melisma op de vorige lettergreep (`le_&_na_`), tenzij het volgende slot al `@l.st.`/`@vl.st.`/`@e.st.` is. |
| optional tussenslots bij sprong naar latere toon                           | VSA-pitch matcht een later slot                    | optional tussenslots weglaten (**H4**); daarna koppelen                                                                                                                                       |

**H6-aanscherping:** blijven er VSA-syllaben op dezelfde graad én is het **volgende**
template-slot ook die graad, dan vult de volgende syllabe dat slot (bijv. `l.st.`),
in plaats van alles op het eerste slot te houden.

### H5 (duur — ELM uit VSA)

De template geeft **ongeveer** aan hoe lang formuleslots zijn. In de instance
bepalen de **VSA-ELMs** de lengte.

| Situatie                                                         | Gedrag                                                                  |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------- |
| VSA-scope met `_` / `__` / `~` / …                               | die MusicXML-duur op het mapped event (alle stemmen)                    |
| Template-event had andere `duration` (bijv. `~` vs VSA `_`)      | template genegeerd in de **instance**; wel zichtbaar op het formuleblad |
| Twee syllaben op dezelfde graad (split)                          | twee events; elk met eigen VSA-duur; A/T/B-akkoord herhaald (H6)        |
| Eén VSA-duur i.p.v. langere formule-indicatie (merge)            | één event met VSA-duur; geen aparte A/T/B-ritmes                        |
| Recite (ongemarkeerd) in instance vóór print-collapse            | kwart per syllabe; MSCZ-collapse naar `\|\|O\|\|` is een print-stap     |

## Hoogte (EHM — exact)

Vergelijking: absolute toonhoogte van de VSA-noot (uit EHM + do-context) ↔
laddergraad `pitches.S` van template-events (zelfde `do`/`mode`). **Geen
tolerantie:** verkeerde graad is fout, ook als de ELM “ongeveer” past.
| Situatie                                                                                      | Gedrag                                                          |
| --------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| VSA-pitch = huidig slot                                                                       | koppelen                                                        |
| VSA-pitch = later slot; overgeslagen tussenslots alleen `optional` of rest van dezelfde S-run | tussenslots weg; daarna koppelen                                |
| VSA-pitch = later slot; ≥1 overgeslagen tussenslot is verplicht **én** andere S-graad         | **`TemplateInstanceError`** (verplicht slot overgeslagen)       |
| VSA-pitch = zelfde slot opnieuw                                                               | hold (H6); bij volgend zelfde-S-slot: dat slot vullen           |
| VSA-pitch past nergens meer in de resterende tail                                             | **`TemplateInstanceError`** (hoogte-mismatch)                   |
| Extra noot ná de tail, andere hoogte                                                          | **`TemplateInstanceError`**                                     |
| Extra noot ná de tail,zelfde hoogte als slot                                                  | hold (H6)                                                       |
| Einde VSA terwijl er nog **verplichte** template-slots resten                                 | **`TemplateInstanceError`** (verplicht slot niet aangedaan)     |
| Einde VSA; resten alleen `optional: true`                                                     | optional resten weglaten (H4)                                   |

Zo wordt bijv. `{-&/Schep_&_}{\per_}` (mi–fa–mi) op template-`laatste`
(mi–re–mi) afgewezen i.p.v. A/T/B stil op mi te laten hangen.

### Foutmeldingen (instance-mapping)

Mappingfouten (H7/H9 e.d.) moeten **bruikbaar** zijn, in dezelfde geest als
`vsa validate`:

| Laag           | Inhoud                                                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Compact**    | korte regel: bestand, regel/kolom (of frase-id + syllabe), foutcode                                                                      |
| **Uitgebreid** | wat er mis is (VSA-pitch vs verwachte template-S-slots); **hint** hoe te herstellen (VSA aanpassen, optional zetten, of ander cadenspad) |

Minimaal in elke melding: bronpad, **regel/kolom** in de VSA-bron (via
`VsaNote.line`/`column`), frase-id, betrokken lyric/syllabe, verwachte vs
gevonden laddergraden. Compact: `bestand:regel:kolom: CODE`.

## Parallelle cadenspaden (`of`)

Eén [template-frase](template-frase@) mag 2+ slot-/cadensreeksen hebben, in
YAML als `of:` met minstens twee `events:`-lijsten. De VSA kiest **impliciet**
welk pad klinkt: de mapper probeert de paden in volgorde en neemt het eerste
waarvan de hoogten (EHM) kloppen. Geen pad → `TemplateInstanceError`
(`VSA-TEMPLATE-CADENCE-PATH` / hoogte-mismatch).

Dit zijn **formule-alternatieven in één template**, geen aparte
[uitvoeringsvorm](@bron)-en (die horen bij zangstuk → variant →
uitvoeringsvorm). Tropaar-toon-4 `laatste` (Hemelum) heeft twee takken:
`re-close` (mi–re–mi, formuleblad pad 0) en `fa-close` (mi–fa–mi).

Formuleblad (`template.mscz`): toont **pad 0** (eerste tak).

## `mode` / `do` (template vs VSA)

Template-`mode` is `major` of `minor` — dezelfde waarden als de VSA-parser.
Bij `map_vsa_to_template` moeten VSA-frontmatter `mode` en `do` (indien
aanwezig) **exact** gelijk zijn aan de template; anders
`VSA-TEMPLATE-MODE-MISMATCH` / `VSA-TEMPLATE-DO-MISMATCH`. Geen stille
afwijking.

## Sequence-form / `text_mapping`-lengte

`sequence: ["1", "2", "3"]` eist precies drie VSA-regels. Cycle+final is
variabel (herhaling tot de slotfrase past). Past het aantal regels niet bij
het plan → `VSA-TEMPLATE-TEXT-MAPPING` (zelfde geest als `vsa validate`).

## Tenor-octaaf (tropaar toon 4)

Openingsakkoord tenor `sol-1` t.o.v. `do: F4` = **C4** (niet C3). Bass
`do-1` = F3. Dat is de gekozen spelling in `template.yaml`;
`pitches_status` blijft `provisional` tot een volledige PDF-audit van andere
tonen.

## Inline VSA in proza

Toon-aanduiding (`T.4`, `T.N`) hoort **niet** in de zingbare VSA-regel (geen
lyric-syllabe). Klein fragment in markdown/proza (alleen hoogtemarkering,
eventueel `Amen`) is een aparte presentatielaag — niet de
instance-lyric-pipeline. Corpus-`.vsa` heeft geen `T.N` vóór EHM’s.

## Corpus en detail

Library-werkmappen: [`library/`](library/README.md).

Corpus Toon 4:
[`library/tropaar-toon-4/notes/corpus.md`](library/tropaar-toon-4/notes/corpus.md).

Elia regel 1 (instance + MusicXML):
[`library/tropaar-toon-4/notes/elia-mapping.md`](library/tropaar-toon-4/notes/elia-mapping.md).

## Wat deze laag niet doet

- Geen nieuwe VSA-syntax voor SATB (SATB blijft in de template).
- Geen automatische keuze tussen plannen op inhoud van de tekst (alleen
  `stanza_count` / expliciet `plan_id`); inhoudelijke keuze blijft redactie.
