# `.mvsa` — meerstemmige tekstbron (draft)

Contracten / producten: [contract-index](contract-index.md).

Tekstbron met lyrics-regel(s) en stemregels (typisch L + SATB). Draft-spec:
[specification-mvsa](../specification-mvsa/README.md). Tutorial:
[mvsa schrijven 101](../guides/mvsa-schrijven-101.md).

## Wat hoort hier

| Onderwerp                           | Waar                                                                                                                  |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Canonieke schrijfvorm, sync, recite | [Syntax](../specification-mvsa/syntax.md), [Semantiek](../specification-mvsa/semantics.md)                            |
| `@`-keywords (titel, tempo, …)      | [Keywords](../specification-mvsa/keywords.md)                                                                         |
| Metadata ↔ `.vsa` (NL-termen)       | [Metadata-brug](../guides/metadata-brug.md)                                                                           |
| Zoektekst in canonieke bron         | [`zoektekst`](zoektekst.md) · CLI [`vsa zoektekst`](../reference/cli/zoektekst.md)                                    |
| Validatieregels                     | [Validatie](../specification-mvsa/validation.md)                                                                      |
| Pitch-vormen / conversies           | [mvsa-conversies](../plans/mvsa-conversions.md)                                                                       |
| Toonsoort / tonica verzetten        | [`mvsa transpose`](../reference/cli/mvsa.md#mvsa-transpose)                                                       |
| Score → `.mvsa` (werkbank)          | [`mxl mvsa`](../reference/cli/mxl.md) / [`mscz mvsa`](../reference/cli/mscz.md) — [Score naar mvsa](#score-naar-mvsa) |
| CLI (bron `.mvsa`)                  | [`mvsa`](../reference/cli/mvsa.md) ()                                                                     |
| Score-IR (scherm-JSON)              | [`score-ir`](score-ir.md) · [`mvsa score-ir`](../reference/cli/mvsa.md#mvsa-score-ir)                             |
| Muziek-only SVG (koormap)           | [`mvsa-svg`](mvsa-svg.md) · [`mvsa svg`](../reference/cli/mvsa.md#mvsa-svg)                                       |
| Platte gezongen tekst (extractie)   | [`vsa text`](../reference/cli/text.md)                                                                                |

## Score naar mvsa

!!! warning "Alleen voor de werkbank-fase"
    `mxl mvsa` / `mscz mvsa` zijn bedoeld als **bewerk-/startvorm** — van
    MuseScore/MusicXML naar bewerkbare `.mvsa`, daarna handmatig afmaken.
    Niet als kant-en-klare catalogusbron. Elk bestand krijgt na
    `# Imported: …` een ASCII-waarschuwingsbanner met checklist.

**CLI (conventie bron → doel):**

| Bron                          | Commando     | Default-uitvoer (zonder `-o`)              |
| ----------------------------- | ------------ | ------------------------------------------ |
| `.mxl` / `.musicxml` / `.xml` | `mxl mvsa`   | `<bronnaam>.mvsa` (bijv. `lied.mxl.mvsa`)  |
| `.mscz`                       | `mscz mvsa`  | `<bronnaam>.mvsa` (bijv. `lied.mscz.mvsa`) |

`.mxl` gaat rechtstreeks naar de SATB-parser (P1–P4); `.mscz` eerst via
MuseScore naar temp-`.mxl` en dezelfde SATB-explode als
[`mscz mxl`](../reference/cli/mscz.md). Default: **canonieke schrijfvorm**
(kuiser-normaalvorm), `--pitch ag-vsa`, `--section schets`. Soft-wrap,
`#maat N`, eindankers: zie hieronder en
[Canonieke maatnummers](#canonieke-maatnummers). Tutorial:
[mvsa schrijven 101 — bladmuziek](../guides/mvsa-schrijven-101.md#7-taak-bladmuziek--mvsa).

Man-pagina’s: [`mxl mvsa`](../reference/cli/mxl.md) ·
[`mscz mvsa`](../reference/cli/mscz.md).

Na import: controleer lyrics/melodie en wat niet meekwam met
[`mscz compare`](../reference/cli/mscz.md#mscz-compare)
(score ↔ `.mvsa`).

## Canonieke maatnummers

Elke **koormaat** heeft in alle vormen waar een maatnummer zichtbaar is
(MuseScore/`.mscz`, MusicXML `@number`, import-commentaar `#maat N`,
partituur-PDF) **hetzelfde nummer**.

| Regel             | Toelichting                                                                                                                                                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bron              | Het maatnummer is dat van de MuseScore-partituur / MusicXML `measure@number` van de koormaat.                                                                         |
| `#maat N`         | `N` = dat canonieke nummer van de eerste koormaat in het LSATB-systeem (niet de 1-based index in een genormaliseerde lijst met extra maten).                          |
| Pauzematen        | Coria-oefenmaten met lyric `[PAUZE]` (na dubbele streep) krijgen een afgeleid nummer `Np` (bijv. `6p`) en **verschuiven** de nummers van volgende koormaten **niet**. |
| Score → mvsa      | `mscz mvsa` / `mxl mvsa` voegen geen `[PAUZE]`-maten toe (die horen bij playback-`.mxl`, niet bij de authoring-schets).                                               |
| Systeemovergangen | Soft-wrap-grenzen in `.mvsa` mogen afwijken van MuseScore-systeemovergangen; alleen het **nummer per maat** is gedeeld, niet de regelsprong.                          |

## Typische commando’s

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd validate examples\mvsa
scripts\mvsa.cmd mxl examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mxl
scripts\mvsa.cmd mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
scripts\mvsa.cmd pdf examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.pdf --keep-mscz generated\alleluia.mscz
scripts\mvsa.cmd svg examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mvsa.svg
scripts\mvsa.cmd normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
scripts\mvsa.cmd transpose examples\bug-cases\alleluia-9b-toon-3-vokn.mvsa --to F4 -o generated\alleluia.in-F.mvsa
scripts\mxl.cmd mvsa generated\alleluia.mxl
scripts\mxl.cmd normalize generated\alleluia.mxl -o generated\alleluia.norm.mxl
scripts\mscz.cmd mvsa generated\alleluia.mscz -o generated\from-mscz.mvsa
scripts\mscz.cmd normalize generated\alleluia.mscz --layout partituur
scripts\mvsa.cmd validate generated\alleluia.mxl.mvsa
vsa text examples\mvsa\alleluia-toon-8.mvsa
```

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mxl`](mxl.md) · [`.mscz`](mscz.md) · [`.vsa`](vsa.md)
