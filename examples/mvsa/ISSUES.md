# Issues met MVSA-experimenten (archief)

Opgeloste experiment-issues en handmatige checks. **Open restpunten** staan
in de centrale backlog:
[`docs/specification-mvsa/open-points.md`](../../docs/specification-mvsa/open-points.md).

Lokale regeneratie: `examples\mvsa\make.cmd` (afgeleiden in `.gitignore`).

| #   | Issue                                                                             | Oplossing                                                                                                                                                                                        |
| --- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | MSCZ: recite-lyrics moeten in PDF zichtbaar én netjes verdeeld; speelduur = Coria | Model A: 1–(n−2)–1 met `\|\|O\|\|` + **spacers** (`notehead none`, geen `print-object=no` op hele noot); duur per slot = rand — zie [mscz-leesbaarheid](../../docs/formats/mscz-leesbaarheid.md) |
| 2   | Sectie-einde moet dubbele maatstreep (`\|\|`)                                     | `\|\|` en herhalingseinden → MusicXML `light-light`                                                                                                                                              |
| 3   | MSCZ-afspraken (A4, systeemafstand, typografie, G/F, melisma, …) terug            | VSA-demo contract → [canonical-checklists](../../docs/formats/canonical-checklists.md) + `mscz_partituur` Style                                                                                  |
| 4   | MXL zonder print-recite; Coria-afspraken terug                                    | Playback = 1 noot/lettergreep (M10); M12–M14 in checklists                                                                                                                                       |
| 5   | PDF en overige types                                                              | Checklist PDF P1–P5; copyright-footer blijft P4 “later”                                                                                                                                          |
| 6   | Geen gegenereerde bestanden in `examples/mvsa/` committen                         | `.gitignore`: `*.mvsa.*`, `*.mxl`, `*.mscz`, … + `*.autosave`                                                                                                                                    |

Handmatig nalopen na export (of via `make.cmd`):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\mvsa
make.cmd kleine-intocht-zondag-hemelum
```
