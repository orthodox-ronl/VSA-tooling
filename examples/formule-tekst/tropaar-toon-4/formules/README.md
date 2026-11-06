# Formule — tropaar toon 4 (Hemelum)

Mensformule (leesvoorbeeld, pad 0 = `laatste` mi–re–mi):
[`tropaar-toon-4.formule.mvsa`](tropaar-toon-4.formule.mvsa).

**Mapper-canonieke bron:**
[`docs/.../library/tropaar-toon-4/template.yaml`](../../../docs/specification-vsa-templates/library/tropaar-toon-4/template.yaml)
(inclusief `of:` fa-close). Verworpen YAML-kandidaat (andere experiment):
[`.archief/…/formule-kandidaat-yaml-verworpen.yaml`](../../.archief/tropaar-toon-4-oud/formule-kandidaat-yaml-verworpen.yaml).

## Hergebruik bestaande syntax

| Onderwerp        | Gebruik                                    | Vermijd                          |
| ---------------- | ------------------------------------------ | -------------------------------- |
| Starttoon        | `a` `f` `c` `f#` …                         | plak-`a-` i.p.v. `a -`           |
| Relatief         | `-` `/` `\` `#\` `b\`                      | `\#`                             |
| Zelfde toon 1×   | `-`                                        | `~` op de stem voor die rol      |
| Kruis op a–g     | `f#` `bb`                                  | `fis` in deze voorbeelden        |
| Optioneel        | `a?` `f#?`                                 | `[open]`                         |
| Ankers + duur    | `@l.st._` `/_` (ELM op stem; formule)      | letterlijke PDF-1-n-1            |
| Recite           | één slot; export doet 1-n-1                | open+box als losse bronnoten     |
| Plan             | `@speelplan \|: f1, f2 :\| laatste`        | YAML-cycle                       |

Zie ook [`../../README.md`](../../README.md) (ftxt-tekens) en
[`../../vsa-bestanden/`](../../vsa-bestanden/) (Fase A-corpus).
