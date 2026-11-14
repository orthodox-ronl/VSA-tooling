# `.vsa` — eenstemmige VSA-bron

Tekstbron voor **eenstemmige** [VSA](@)-notatie. Normatieve taal: de
[VSA-specificatie](../specification/README.md). Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                      |
| -------- | ------------------------------------------- |
| Extensie | `.vsa`                                      |
| Rol      | Canonieke **notatiebron** (geen meta-key)   |
| Sibling  | Bestandsnaam = bronnaam (bijv. `lied.vsa`)  |
| Wanneer  | Eenstemmige catalogus- of corpusbron        |

## Canoniciteit

Canoniek = voldoet aan [VSA-specificatie](../specification/README.md) +
[syllabificatie](syllabificatie.md) (dictionary / soft `-`) +
bibliotheek-frontmatter waar die consumer geldt. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp      | Regel                                                                                                                                                 |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontmatter    | Consumer: [bibliotheek `vsa-frontmatter`](https://github.com/orthodox-ronl/bibliotheek/blob/main/docs/specs/vsa-frontmatter.md) (`soort`/`toon` e.d.) |
| Encoding       | UTF-8                                                                                                                                                 |
| Zoektekst YAML | Optioneel in bron — [zoektekst](zoektekst.md)                                                                                                         |
| Meerstemmig    | **Niet** in `.vsa` — zie [`.mvsa`](mvsa.md)                                                                                                           |

## Syllabificatie

Soft `-` **vereist** in platte recite-woorden met meerdere lettergrepen;
hard `=` = orthografisch koppelteken. Scope `{…}` = al grens (geen soft `-`
naast `{`/`}`). Hub: [syllabificatie](syllabificatie.md). Schrijfhulp:
[`vsa syllabify`](../reference/cli/syllabify.md). Validate:
`VSA-SYLLABLE-DICT-*`, `VSA-SYLLABIFY-MISSING-HYPHENS`.

## Melisma en binding

| Id      | Regel                                                    |
| --      | -----                                                    |
| K2 / L3 | Lettergreep = tekstpositie met ≥1 noot; hyphen ≠ melisma |
| Export  | Same-pitch melisma → M5a/S13 in MXL/MSCZ-producten       |

## Transliteratie

Bron blijft liturgische spelling. Tweede laag = apart product
([translit-svg](translit-svg.md)), niet in `.vsa` zelf.

## Stemmen en partijen

n.v.t. — eenstemmig. Melodie naar SATB via template: T1–T7
([vsa-mvsa-contract](../specification-vsa-templates/vsa-mvsa-contract.md)).

## Leesbaarheid

n.v.t. op de tekstbron zelf. Scherm: [vsa-svg](vsa-svg.md). Partituur:
product [`.mscz`](mscz.md).

## Herkomst

n.v.t. voor het brontype zelf. Afgeleiden: `{naam}.vsa.products-meta.json`
— [products-meta](products-meta.md).

## Conversies

| Doel                                      | CLI                                                               | Opmerking                                         |
| ----------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------- |
| Products-set                              | [`vsa products`](../reference/cli/products.md)                    | Geen partituur-PDF in products                    |
| `.mxl`                                    | [`vsa mxl`](../reference/cli/musicxml.md)                         | Zing-deling in bron; `--syllabify` = uitzondering |
| `.mscz` / SVG / audio / lyrics / score-ir | via products of losse straat-subs                                 | C3/C4                                             |
| → `.mvsa`                                 | [`vsa mvsa`](../specification-vsa-templates/vsa-mvsa-contract.md) | T1–T7                                             |

Geen `vsa normalize`.

## Validatie

[`vsa validate`](../reference/cli/validate.md) — syntax, semantiek,
syllabificatie/dictionary.

## Typische commando’s

```cmd
vsa validate examples\minimal\050_svg_demo.vsa
vsa svg examples\docs-walkthroughs\svg-phrase-kort.vsa
vsa products examples\minimal\valid-demo.vsa
vsa pdf examples\minimal\valid-demo.vsa -o generated\demo.pdf
vsa mxl examples\docs-walkthroughs\coria-oefenlink\oefenmelodie.vsa -o generated\mxl\oefenmelodie.mxl --syllabify
vsa text examples\minimal\001_plain_text.vsa
```

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md) · [`.mvsa`](mvsa.md)
