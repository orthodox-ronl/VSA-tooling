# `.mvsa` — meerstemmige tekstbron (draft)

Tekstbron met lyrics-regel(s) en stemregels (typisch L + SATB). Draft-spec:
[specification-mvsa](../specification-mvsa/README.md). Tutorial:
[mvsa schrijven 101](../guides/mvsa-schrijven-101.md).

## Wat hoort hier

| Onderwerp                           | Waar                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------ |
| Canonieke schrijfvorm, sync, recite | [Syntax](../specification-mvsa/syntax.md), [Semantiek](../specification-mvsa/semantics.md) |
| Validatieregels                     | [Validatie](../specification-mvsa/validation.md)                                           |
| Pitch-vormen / conversies           | [mvsa-conversies](../plans/mvsa-conversions.md)                                            |
| CLI                                 | [`mvsa`](../reference/cli/mvsa.md) (`≡ vsa mvsa`)                                          |
| Platte gezongen tekst               | [`vsa text`](../reference/cli/text.md)                                                     |

## Typische commando’s

```cmd
mvsa validate examples\mvsa
mvsa musicxml examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mxl
mvsa mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
mvsa pdf examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.pdf --keep-mscz generated\alleluia.mscz
mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
mvsa import generated\alleluia.mxl --pitch doremi -o generated\alleluia.import.mvsa
vsa text examples\mvsa\alleluia-toon-8.mvsa
```

Via repo-script: `scripts\mvsa.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
