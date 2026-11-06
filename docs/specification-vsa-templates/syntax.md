# Syntax

Canonieke bronvorm: **YAML**. Structurele toetsing:
[`schema/vsa-template.schema.json`](schema/vsa-template.schema.json).

Toonhoogte- en duurmodel sluiten aan op [VSA](@) 1.0 ([do-context](@),
[ELM](enkelvoudige-lengte-modifier@)). Zie
[Semantiek](../specification/semantics.md) §5.5–5.10.

## Topniveau

Elk [vsa-template](@) is **één** van drie vormen:

1. **cycle-form** — `cycle` + `final`;
2. **sequence-form** — `sequence`;
3. **alias-form** — `same_as`.

### Cycle-form

```yaml
spec_version: draft-v0
id: tropaar-toon-4
genre: tropaar
tone: 4
do: F4
mode: major
duration-model: default
pitches_status: provisional
source: "…"
also_used_as: [kondak]
cycle: ["1", "2"]
final: laatste
phrases:
  - id: "1"
    events: [ ... ]
  - id: "1a"
    events: [ ... ]
```

Toegestane `genre` / `also_used_as`: `tropaar`, `kondak`, `stichier`,
`vers`, `other`.

[Template-frasen](template-frase@) in `phrases` die **niet** in `cycle`/`final`
staan (zoals `"1a"`) horen bij de bibliotheek.

### Sequence-form / alias-form

Zelfde `do` / `mode` (verplicht). Alias heeft geen `phrases`.

## Template-event

```yaml
- role: recite
  duration: "~"
  optional: false
  anchor: l.st.
  pitches:
    S: mi
    A: do
    T: sol-1
    B: do-1
```

### Duration ([ELM](enkelvoudige-lengte-modifier@))

Standaardduur ↔ kwartnoot bij `duration-model: default`.

| ELM  | Semantiek (VSA)       | MusicXML (default) |
| ---- | --------------------- | ------------------ |
| `~`  | 1 × standaardduur     | quarter            |
| `-`  | 1 × standaardduur     | quarter            |
| `-.` | 1½ × standaardduur    | dotted quarter      |
| `~.` | 1½ × standaardduur    | dotted quarter      |
| `_`  | 2 × standaardduur     | half               |
| `_.` | 3 × standaardduur     | dotted half        |
| `__` | 4 × standaardduur     | whole              |
| `.`  | ½ × standaardduur     | eighth             |
| `..` | ¼ × standaardduur     | 16th               |

`role: recite` = [reciteertoon](@); typisch `duration: "~"` per syllabe.

### Pitches ([laddergraad](@))

```text
pitch := ['#' | 'b'] degree [ '+' n | '-' n ]
degree := 'do' | 're' | 'mi' | 'fa' | 'sol' | 'la' | 'ti'
```

Voorbeelden bij `do: F4`, `mode: major`: `do`→F4, `mi`→A4, `sol-1`→C4.

### Regels (syntactisch)

1. Frase-ids uniek; mogen `1a` / `2a` bevatten.
2. Cycle- / sequence- / alias-form zoals hierboven.
3. Elk [template-event](@): `role`, `duration` (ELM), `pitches` met S/A/T/B.
4. `do` matcht scientific pitch; `mode` ∈ {`major`, `minor`} (zelfde waarden
   als de VSA-parser).
5. `anchor` ∈ {`e.st.`, `l.st.`, `vl.st.`, `l.lgr.`} indien aanwezig
   ([frase-anker](@)). Spaties in invoer (`e. st.`) worden genormaliseerd naar
   de canonieke vorm zonder spatie.
6. In `events` mag een **`of`-groep** staan (minstens twee cadenspaden). Elk
   pad is een lijst gewone events. Formuleblad toont pad 0; de instance-mapper
   kiest het pad dat bij de VSA-hoogten past. Geen pad → hoogte-mismatch.
   Dit zijn **geen** [uitvoeringsvorm](@bron)-en.

```yaml
- of:
    - id: re-close
      events:
        - role: cadence
          duration: "_"
          pitches: { S: re, A: ti-1, T: sol-1, B: sol-2 }
        - role: cadence
          duration: "__"
          pitches: { S: mi, A: do, T: sol-1, B: do-1 }
    - id: fa-close
      events:
        - role: cadence
          duration: "_"
          pitches: { S: fa, A: re, T: la-1, B: re-1 }
        - role: cadence
          duration: "__"
          pitches: { S: mi, A: do, T: sol-1, B: do-1 }
```

## Wat syntax niet uitdrukt

- Syllabe-tekst / VSA-scopes (zie [mapping](mapping-vsa.md)).
- SVG-/MusicXML-layout.
- Ongelijke ritmes per stem.
