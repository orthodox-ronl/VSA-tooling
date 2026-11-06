# Archief — eerdere aanpak (VSA + template)

Deze map bewaart **snapshots** van het eerdere onderzoekstraject:

- melodieformule in YAML (`vsa-template`);
- tekst **én** sopraancontour in `.vsa`;
- mapping “S uit VSA, A/T/B uit template”.

Dat pad leverde waardevolle ervaringen op (ankers, optionele noten, recite,
cycle/`laatste`, MuseScore-valkuilen). Het is **niet** meer het uitgangspunt
van de herstart in `examples/formule-tekst/`.

## Wat hier ligt

| Pad                                       | Inhoud                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| `tropaar-toon-4-oud/`                     | Snapshot tropaar toon 4 (template, twee corpus-`.vsa`, mappingnotities) |
| `…/template.yaml`                         | Oude canonieke formule-YAML                                             |
| `…/corpus/T4-11-…vsa`                     | Nicolaas (VSA = tekst + S-melodie)                                      |
| `…/corpus/T4-06-…vsa`                     | Elia (baseline walkthrough optionals/ankers)                            |
| `…/notes/elia-mapping.md`                 | Event-niveau analyse Elia                                               |
| `…/notes/corpus.md`                       | Corpusoverzicht + cycle-regels                                          |
| `…/mapping-vsa.md`                        | Experimenteel mappingcontract (H1–H9)                                   |
| `…/formule-kandidaat-yaml-verworpen.yaml` | YAML-formulekandidaat — bewust verworpen (onleesbaar om te editen)      |

## Wat bewust níet hierheen is verhuisd

De draft-spec en library onder
`docs/specification-vsa-templates/` blijven staan: schema-tests, MkDocs-nav en
render-scripts hangen daar nog aan. Behandel die tree als **bevroren
referentie** tot we hem bewust opruimen of vervangen.

Afgeleide `.mscz` / `.mxl` uit het oude corpus zijn **niet** gekopieerd (groot,
genereerbaar); die staan nog in de library-map indien nodig.

## Leeswijzer t.o.v. de herstart

| Oud                                      | Nieuw (deze herstart)                                      |
| ---------------------------------------- | ---------------------------------------------------------- |
| `.vsa` = tekst + S-hoogte                | `.ftxt` = tekst + klemtoon (geen melodie)                  |
| Template vult A/T/B rond VSA-S           | Formule = hele muziek; tekst landt op slots via klemtonen  |
| Instance via `template_instance.py`      | Instanties hier: mensleesbare voorbeelden, nog geen tool   |
