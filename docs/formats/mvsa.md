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
| Import uit `.mxl` / `.mscz`         | [`mvsa import`](../reference/cli/mvsa.md#vsa-mvsa-import) (soft-wrap ~80; holds; recite)   |
| CLI                                 | [`mvsa`](../reference/cli/mvsa.md) (`≡ vsa mvsa`)                                          |
| Platte gezongen tekst               | [`vsa text`](../reference/cli/text.md)                                                     |

**Import (kort):** `.mxl` gaat rechtstreeks naar de SATB-parser (P1–P4);
`.mscz` eerst via MuseScore naar temp-`.mxl` en dezelfde SATB-explode als
[`mscz mxl`](../reference/cli/mscz.md). Met `--pitch vsa` plakt de import
check-only eindankers (a–g + cijfer) op systeemeinden; `doremi` / `a-g` doen
dat niet. Tutorial: [mvsa schrijven 101 — bladmuziek](../guides/mvsa-schrijven-101.md#7-taak-bladmuziek--mvsa).

## Typische commando’s

```cmd
mvsa validate examples\mvsa
mvsa musicxml examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mxl
mvsa mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
mvsa pdf examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.pdf --keep-mscz generated\alleluia.mscz
mvsa normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
mvsa import generated\alleluia.mxl --pitch doremi -o generated\alleluia.import.mvsa
mvsa import generated\alleluia.mxl --pitch vsa -o generated\alleluia.vsa.mvsa
mvsa validate generated\alleluia.vsa.mvsa
vsa text examples\mvsa\alleluia-toon-8.mvsa
```

Via repo-script: `scripts\mvsa.cmd …`

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
