# Voorbeelden

## Library (geldige formules)

Canonieke werkmappen: [`library/`](library/README.md).
Per formule: `template.yaml`, plus afgeleide `template.mscz` (MuseScore) en
`template.mxl` (MusicXML) waar de pijplijn dat al doet; optioneel
`examples/corpus/` en `notes/`.

| Map                                                                      | Vorm     | Doel                                           |
| ------------------------------------------------------------------------ | -------- | ---------------------------------------------- |
| [`kondak-toon-1-groningen`](library/kondak-toon-1-groningen/README.md)   | cycle    | Groningen F4; also tropaar                     |
| [`kondak-toon-2-groningen`](library/kondak-toon-2-groningen/README.md)   | cycle    | Groningen F4; also tropaar                     |
| [`kondak-toon-6-groningen`](library/kondak-toon-6-groningen/README.md)   | cycle    | Groningen F4; also tropaar                     |
| [`kondak-toon-8-groningen`](library/kondak-toon-8-groningen/README.md)   | cycle    | Groningen F4; also tropaar; `\|: 1 :\|`        |
| [`kondak-toon-8-hemelum`](library/kondak-toon-8-hemelum/README.md)       | cycle    | Hemelum/Liturgikon F4; `laatste` → mi          |
| [`tropaar-toon-8-hemelum`](library/tropaar-toon-8-hemelum/README.md)     | alias    | `same_as: kondak-toon-8-hemelum`               |
| [`tropaar-toon-1-groningen`](library/tropaar-toon-1-groningen/README.md) | cycle    | `1,2` + `laatste`; bibliotheek `1a`            |
| [`tropaar-toon-2-groningen`](library/tropaar-toon-2-groningen/README.md) | alias    | `same_as: kondak-toon-2-groningen`             |
| [`tropaar-toon-6-groningen`](library/tropaar-toon-6-groningen/README.md) | alias    | `same_as: kondak-toon-6-groningen`             |
| [`tropaar-toon-8-groningen`](library/tropaar-toon-8-groningen/README.md) | alias    | `same_as: kondak-toon-8-groningen` (Groningen) |
| [`tropaar-toon-3-groningen`](library/tropaar-toon-3-groningen/README.md) | sequence | vaste volgorde + `2a` + ELM `.`                |
| [`tropaar-toon-4-hemelum`](library/tropaar-toon-4-hemelum/README.md)     | cycle    | Hemelum; Elia-mapping + corpus                 |
| [`tropaar-toon-4-groningen`](library/tropaar-toon-4-groningen/README.md) | cycle    | Groningen tropaar/kondak toon 4                |
| [`stichier-toon-5-pdf`](library/stichier-toon-5-pdf/README.md)           | cycle    | PDF-stichier `1,2,3` + `laatste`               |
| [`tropaar-toon-5-groningen`](library/tropaar-toon-5-groningen/README.md) | alias    | `same_as: kondak-toon-5-groningen` (Groningen) |
| [`kondak-toon-5-groningen`](library/kondak-toon-5-groningen/README.md)   | cycle    | Groningen; also tropaar                        |
| [`vers-toon-1-groningen`](library/vers-toon-1-groningen/README.md)       | cycle    | vers toon 1; `vl.st.`                          |
| [`vers-toon-5-groningen`](library/vers-toon-5-groningen/README.md)       | cycle    | vers toon 5; ELM `_.`                          |

Alle formules: [vsa-templates](vsa-template@) met `pitches_status: provisional`
tot PDF-audit. MusicXML regenereren:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\render_vsa_template_musicxml.py --all
```

## Ongeldig (`examples/invalid/`)

| Bestand                                                                         | Code                          |
| ------------------------------------------------------------------------------- | ----------------------------- |
| [`cycle-unknown-phrase.yaml`](examples/invalid/cycle-unknown-phrase.yaml)       | `TEMPLATE-CYCLE-REF`          |
| [`final-in-cycle.yaml`](examples/invalid/final-in-cycle.yaml)                   | `TEMPLATE-FINAL-NOT-IN-CYCLE` |
| [`missing-voice-pitch.yaml`](examples/invalid/missing-voice-pitch.yaml)         | `TEMPLATE-PITCHES`            |
| [`sequence-unknown-phrase.yaml`](examples/invalid/sequence-unknown-phrase.yaml) | `TEMPLATE-SEQUENCE-REF`       |
| [`same-as-missing-target.yaml`](examples/invalid/same-as-missing-target.yaml)   | `TEMPLATE-SAME-AS-REF`        |
| [`bad-duration-elm.yaml`](examples/invalid/bad-duration-elm.yaml)               | `TEMPLATE-DURATION`           |

## Checklist “mag in library/”

- [ ] Schema + documentregels groen
- [ ] `template.mxl` gegenereerd (SA/TB, `senza-misura`)
- [ ] `source` of README verklaart herkomst
- [ ] Onzekere pitches: `pitches_status: provisional`
