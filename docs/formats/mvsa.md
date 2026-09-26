# `.mvsa` — meerstemmige tekstbron (draft)

Tekstbron met lyrics-regel(s) en stemregels (typisch L + SATB). Draft-spec:
[specification-mvsa](../specification-mvsa/README.md).

## Wat hoort hier

| Onderwerp | Waar |
| --------- | ---- |
| Canonieke schrijfvorm, sync, recite | [Syntax](../specification-mvsa/syntax.md), [Semantiek](../specification-mvsa/semantics.md) |
| Validatieregels | [Validatie](../specification-mvsa/validation.md) |
| Pitch-vormen / conversies | [mvsa-conversies](../plans/mvsa-conversions.md) |
| CLI | [`mvsa`](../reference/cli/mvsa.md) (`≡ vsa mvsa`) |

## Typische commando’s

```cmd
mvsa validate examples\mvsa
mvsa musicxml examples\mvsa\alleluia-toon-8.canonieke.mvsa -o generated\alleluia.mxl
mvsa mscz examples\mvsa\alleluia-toon-8.canonieke.mvsa -o generated\alleluia.mscz
mvsa normalize examples\mvsa\alleluia-toon-8.canonieke.mvsa --pitch abc -o generated\alleluia.abc.mvsa
mvsa import generated\alleluia.mxl --pitch doremi -o generated\alleluia.import.mvsa
```

Via repo-script: `scripts\mvsa.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
