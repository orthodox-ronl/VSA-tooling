# Issues met MVSA experimenten

Status: **opgelost** (toolchain + checklists). Lokale regeneratie blijft
handmatig in `examples/mvsa/` (afgeleiden staan in `.gitignore`).

| #   | Issue                                                                             | Oplossing                                                                                                                                                                                        |
| -   | -----                                                                             | ---------                                                                                                                                                                                        |
| 1   | MSCZ: recite-lyrics moeten in PDF zichtbaar én netjes verdeeld; speelduur = Coria | Model A: 1–(n−2)–1 met `\|\|O\|\|` + **spacers** (`notehead none`, geen `print-object=no` op hele noot); duur per slot = rand — zie [mscz-leesbaarheid](../../docs/formats/mscz-leesbaarheid.md) |
| 2   | Sectie-einde moet dubbele maatstreep (`\|\|`) | `\|\|` / `: |     | ` → MusicXML `light-light` |
| 3   | MSCZ-afspraken (A4, systeemafstand, typografie, G/F, melisma, …) terug | VSA-demo contract → [canonical-checklists](../../docs/formats/canonical-checklists.md) + `mscz_partituur` Style |
| 4   | MXL zonder print-recite; Coria-afspraken terug                         | Playback = 1 noot/lettergreep (M10); M12–M14 in checklists                                                      |
| 5   | PDF en overige types                                                   | Checklist PDF P1–P5; copyright-footer blijft P4 “later”                                                         |
| 6   | Geen gegenereerde bestanden in `examples/mvsa/` committen              | `.gitignore`: `*.mvsa.*`, `*.mxl`, `*.mscz`, … + `*.autosave`                                                   |

Handmatig nalopen na export:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa mscz examples\mvsa\kleine-intocht-zondag-hemelum.mvsa -o examples\mvsa\kleine-intocht-zondag-hemelum.mvsa.mscz
mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa -o examples\mvsa\kleine-intocht-zondag-hemelum.mvsa.mxl
```

## Nieuwe issues:

1. Een maatstreep geeft het einde van een sectie aan 
   - bij een end-of-file (of een ander syntactisch einde, bijvoorbeeld als de mvsa in een of ander notatie-blok (komt te) zit(ten));
   - bij het starten van een nieuwe sectie (`@sectie`).
2. `vsa mvsa validate` moet geen bestanden noemen die OK zijn. Als alles OK is is een 'OK' voldoende, net als bij 'vsa validate'.
3. 