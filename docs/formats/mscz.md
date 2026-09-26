# `.mscz` — MuseScore-partituur

Native MuseScore-bestand (zip met o.a. `.mscx`). In deze toolchain vooral
voor de **partituur-workflow**; Coria gebruikt `.mxl`.

## Wat hoort hier

| Onderwerp | Waar |
| --------- | ---- |
| Export vanuit `.mvsa` | [`mvsa mscz`](../reference/cli/mvsa.md#vsa-mvsa-mscz) (keten mxl → MuseScore) |
| Import → `.mvsa` | [`mscz import`](../reference/cli/mscz.md) |
| → `.mxl` | [`mscz mxl`](../reference/cli/mscz.md) |
| Template-/corpus-MSCZ | [VSA-templates](../specification-vsa-templates/README.md) |

Geen volledige MuseScore-formaat-spec — wel: wat **wij** genereren en
verwachten voor bruikbare SATB + lyrics.

## Typische commando’s

```cmd
mscz import generated\alleluia.mscz --pitch abc -o generated\from-mscz.mvsa
mscz mxl generated\alleluia.mscz -o generated\from-mscz.mxl
mvsa mscz examples\mvsa\alleluia-toon-8.canonieke.mvsa -o generated\alleluia.mscz
```

Via repo-script: `scripts\mscz.cmd …`

Vereist MuseScore 4 (of 3) lokaal, tenzij je alleen `.mxl` gebruikt.

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mvsa`](mvsa.md)
- [mvsa-conversies](../plans/mvsa-conversions.md)
