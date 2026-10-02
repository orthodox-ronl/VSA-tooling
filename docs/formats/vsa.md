# `.vsa` — eenstemmige VSA-bron

Tekstbron voor **eenstemmige** [VSA](@)-notatie. Normatieve taal: de
[VSA-specificatie](../specification/README.md).

## Wat hoort hier

| Onderwerp                               | Waar                                                                               |
| --------------------------------------- | ---------------------------------------------------------------------------------- |
| Syntax, semantiek, validatie            | [Specificaties](../specification/README.md)                                        |
| Valideren / SVG / MusicXML              | [`vsa`](../reference/cli/index.md), [`vsa musicxml`](../reference/cli/musicxml.md) |
| Platte gezongen tekst                   | [`vsa text`](../reference/cli/text.md)                                             |
| MusicXML-profielen (Coria vs engraving) | [MusicXML-export](../guides/musicxml-export.md)                                    |
| Meerstemmig (L + SATB)                  | **niet** `.vsa` — zie [`.mvsa`](mvsa.md)                                           |

## Typische commando’s

```cmd
vsa validate examples\minimal\050_svg_demo.vsa
vsa musicxml examples\docs-walkthroughs\coria-oefenlink\oefenmelodie.vsa generated\mxl\oefenmelodie.mxl
vsa text examples\minimal\001_plain_text.vsa
```

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md)
