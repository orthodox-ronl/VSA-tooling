# `.vsa` — eenstemmige VSA-bron

Tekstbron voor **eenstemmige** [VSA](@)-notatie. Normatieve taal: de
[VSA-specificatie](../specification/README.md). Contracten:
[contract-index](contract-index.md).

## Wat hoort hier

| Onderwerp                               | Waar                                                                                                 |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Syntax, semantiek, validatie            | [Specificaties](../specification/README.md)                                                          |
| Valideren / MusicXML                    | [`vsa`](../reference/cli/index.md), [`vsa musicxml`](../reference/cli/musicxml.md)                   |
| Standaardproducten + meta               | [`vsa products`](../reference/cli/products.md) (Coria-`.mxl` met syllabify+finalize + `.svg` + meta) |
| Muziek-only SVG (scherm / koormap)      | [`vsa-svg`](vsa-svg.md) · [`vsa svg`](../reference/cli/svg.md)                                       |
| Zoektekst in canonieke bron             | [`zoektekst`](zoektekst.md) · CLI [`vsa zoektekst`](../reference/cli/zoektekst.md)                   |
| Platte gezongen tekst (extractie)       | [`vsa text`](../reference/cli/text.md)                                                               |
| MusicXML-profielen (Coria vs engraving) | [MusicXML-export](../guides/musicxml-export.md)                                                      |
| Meerstemmig (L + SATB)                  | **niet** `.vsa` — zie [`.mvsa`](mvsa.md)                                                             |

## Typische commando’s

```cmd
vsa validate examples\minimal\050_svg_demo.vsa
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa
vsa products examples\minimal\valid-demo.vsa
vsa musicxml examples\docs-walkthroughs\coria-oefenlink\oefenmelodie.vsa generated\mxl\oefenmelodie.mxl --syllabify
vsa text examples\minimal\001_plain_text.vsa
```

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md)
