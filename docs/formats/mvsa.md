# `.mvsa` — meerstemmige tekstbron (draft)

Tekstbron met lyrics-regel(s) en stemregels (typisch L + SATB). Draft-spec:
[specification-mvsa](../specification-mvsa/README.md). Tutorial:
[mvsa schrijven 101](../guides/mvsa-schrijven-101.md). Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                      |
| -------- | ------------------------------------------- |
| Extensie | `.mvsa`                                     |
| Rol      | Canonieke **notatiebron** (geen meta-key)   |
| Sibling  | Bestandsnaam = bronnaam (bijv. `lied.mvsa`) |
| Wanneer  | Meerstemmige catalogus- of schetsbron       |

## Canoniciteit

Canoniek = [syntax](../specification-mvsa/syntax.md) /
[semantiek](../specification-mvsa/semantics.md) /
[validatie](../specification-mvsa/validation.md) +
[syllabificatie](syllabificatie.md) op L-lyrics. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp                  | Regel                                                                                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontmatter / `@`-keywords | [Keywords](../specification-mvsa/keywords.md); brug naar NL-termen: [metadata-brug](../guides/metadata-brug.md)                                               |
| Encoding                   | UTF-8                                                                                                                                                         |
| Zoektekst YAML             | [zoektekst](zoektekst.md)                                                                                                                                     |
| Normalisatie               | Spelling/pitch + kolommen (ook `&` in melisma): [`mvsa normalize`](../reference/cli/mvsa.md#mvsa-normalize) + [mvsa-conversies](../plans/mvsa-conversions.md) |

## Syllabificatie

Soft `-` in L-tekst (recite tussen haakjes én cadens-brug `)-…`). Hub:
[syllabificatie](syllabificatie.md). Schrijfhulp:
[`mvsa syllabify`](../reference/cli/mvsa.md#mvsa-syllabify).

## Melisma en binding

| Id            | Regel                                                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K2 / L3 / S13 | Hyphen ≠ melisma; export volgt M5a/S13                                                                                                                                    |
| `&`-kolommen  | Canonieke layout: `&` op L en S/A/T/B in dezelfde kolom; spaties rond `&` semantisch neutraal ([syntax](../specification-mvsa/syntax.md#canonieke-kolomuitlijning-lsatb)) |
| Recite        | Print-collapse alleen op partituur-producten (S8); niet in authoring-tekst “wegschrijven”                                                                                 |

## Transliteratie

n.v.t. in `.mvsa` als tweede L-laag. Translit = apart product
([translit-svg](translit-svg.md)).

## Stemmen en partijen

Typisch L + S/A/T/B. Melodiestem-default bij VSA→MVSA: **S** (T2). Extractie
naar `.vsa`: [mvsa-vsa-contract](mvsa-vsa-contract.md) (E\*; default S).

## Leesbaarheid

n.v.t. op de tekstbron. Producten: [`.mscz`](mscz.md), [mvsa-svg](mvsa-svg.md),
[score-ir](score-ir.md).

## Herkomst

n.v.t. voor het brontype. Afgeleiden: `{naam}.mvsa.products-meta.json` —
[products-meta](products-meta.md).

## Conversies

| Doel                                                     | CLI                                                               |
| -------------------------------------------------------- | ----------------------------------------------------------------- |
| Products                                                 | [`mvsa`](../reference/cli/mvsa.md) products / losse keys          |
| `.mxl` / `.mscz` / SVG / PDF / audio / lyrics / score-ir | `mvsa mxl` / `mscz` / `svg` / `pdf` / `mp3` / `text` / `score-ir` |
| → `.vsa`                                                 | `mvsa vsa` / products key `vsa` (E\*)                             |
| Score → `.mvsa`                                          | `mxl mvsa` / `mscz mvsa` — **werkbank** (zie hieronder)           |

## Validatie

[`mvsa validate`](../reference/cli/mvsa.md) + syllabify-checks op L.

| Code                        | Regel                                                                                                                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MVSA-RECITE-INTERIOR-ELM`  | Geen duur-/melisma-ELM (`_`, `~`, `.`, `&`, …) op lettergrepen **binnen** `(…)`; duur alleen ná `)` of als aparte L-positie erbuiten. Hub: [syntax — reciteertoon](../specification-mvsa/syntax.md#reciteertoon). |

---

## Score naar mvsa (type-specifiek)

!!! warning "Alleen voor de werkbank-fase"
    `mxl mvsa` / `mscz mvsa` zijn bedoeld als **bewerk-/startvorm** — van
    MuseScore/MusicXML naar bewerkbare `.mvsa`, daarna handmatig afmaken.
    Niet als kant-en-klare catalogusbron. Elk bestand krijgt na
    `# Imported: …` een ASCII-waarschuwingsbanner met checklist.

| Bron                          | Commando    | Default-uitvoer (zonder `-o`) |
| ----------------------------- | ----------- | ----------------------------- |
| `.mxl` / `.musicxml` / `.xml` | `mxl mvsa`  | `<bronnaam>.mvsa`             |
| `.mscz`                       | `mscz mvsa` | `<bronnaam>.mvsa`             |

Default: canonieke schrijfvorm, `--pitch ag-vsa`, `--octave-style @oct`
(relatieve a–g zoals `Bb` / `c+`, geen `Bb4`), `--section schets`.
Met `--octave-style none` krijg je wetenschappelijke absolute hoogtes
(`Bb4`); dat mag niet samen met `--pitch doremi`. Zie
[mvsa-conversions](../plans/mvsa-conversions.md).
Man-pagina’s: [`mxl mvsa`](../reference/cli/mxl.md) ·
[`mscz mvsa`](../reference/cli/mscz.md). Controle:
[`mscz compare`](../reference/cli/mscz.md#mscz-compare).

## Canonieke maatnummers (type-specifiek)

Elke **koormaat** heeft in alle vormen waar een maatnummer zichtbaar is
(MuseScore/`.mscz`, MusicXML `@number`, import-commentaar `#maat N`,
partituur-PDF) **hetzelfde nummer**.

| Regel        | Toelichting                                                                  |
| ------------ | ---------------------------------------------------------------------------- |
| Bron         | Maatnummer = MuseScore-partituur / MusicXML `measure@number` van de koormaat |
| `#maat N`    | `N` = canonieke nummer van de eerste koormaat in het LSATB-systeem           |
| Pauzematen   | Coria `[PAUZE]` → afgeleid `Np`; verschuift volgende koormaten **niet**      |
| Score → mvsa | Geen `[PAUZE]`-maten in authoring-schets                                     |
| Soft-wrap    | Mag afwijken van MuseScore-systeemovergangen; nummer per maat is gedeeld     |

## Typische commando’s

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\mvsa.cmd validate examples\mvsa
scripts\mvsa.cmd mxl examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mxl
scripts\mvsa.cmd mscz examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mscz
scripts\mvsa.cmd pdf examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.pdf --keep-mscz generated\alleluia.mscz
scripts\mvsa.cmd svg examples\mvsa\alleluia-toon-8.mvsa -o generated\alleluia.mvsa.svg
scripts\mvsa.cmd normalize examples\mvsa\alleluia-toon-8.mvsa --pitch a-g -o generated\alleluia.ag.mvsa
```

## Zie ook

- [Formaten & CLI — overzicht](index.md)
- [`.mscz`](mscz.md) · [`.mxl`](mxl.md) · [`.vsa`](vsa.md)
