# Metadata-brug: `.vsa` ↔ `.mvsa`

**Voor wie:** wie metadata zet in eenstemmige [VSA](@) (`.vsa` / Hugo-blok) of
in meerstemmige mvsa (`.mvsa`) en wil weten welke namen horen bij welk
exportveld.

De **canonieke termen zijn Nederlands** (zoals in mvsa-`@`-keywords). De
schrijfwijze verschilt per formaat; de betekenis en MusicXML-bestemming moeten
hetzelfde blijven.

## Schrijfwijze (niet unificeren)

| Formaat   | Hoe metadata schrijven                                                        |
| --------- | ----------------------------------------------------------------------------- |
| `.mvsa`   | Keyword-regel: `@title "…"`, `@do F4`, `@tempo 72`                            |
| `.vsa`    | YAML-frontmatter (`muziek:` / `identificatie:`) of blokparameters (`do="F4"`) |

Geen verplichting om YAML in `.mvsa` of `@`-regels in `.vsa` te gebruiken.
Alleen de **begrippen** en exportgedrag gelijk houden.

## Gedeelde velden (Nederlands → schrijfwijzen)

| Term (NL)      | `.mvsa`                 | `.vsa` (YAML / blok)                         | MusicXML / MuseScore                                      |
| -------------- | ----------------------- | -------------------------------------------- | --------------------------------------------------------- |
| titel          | `@title "…"`            | `identificatie.title` / `title="…"`          | `<work-title>` / titel                                    |
| ondertitel     | `@ondertitel "…"`       | `identificatie.subtitle` / `subtitle="…"`    | `<movement-title>` / subtitle                             |
| componist      | `@composer "…"`         | `identificatie.composer` / `composer="…"`    | `<creator type="composer">`                               |
| tekstdichter   | `@tekstdichter "…"`     | `identificatie.lyricist`                     | `<creator type="lyricist">`                               |
| arrangeur      | `@arrangeur "…"`        | *(geen standaardveld)*                       | `<creator type="arranger">`                               |
| vertaler       | `@vertaler "…"`         | *(geen standaardveld)*                       | `<creator type="translator">`                             |
| bron           | `@bron "…"`             | *(geen standaardveld; optioneel vrij)*       | `<source>` / misc `bron` (Coria); MSCZ-colofon            |
| copyright      | `@copyright "…"`        | `identificatie.rights`                       | `<rights>` / copyright                                    |
| tempo          | `@tempo 72`             | `muziek.tempo` / `tempo="72"`                | `sound tempo` (metronoom onzichtbaar op blad/PDF)         |
| toon           | `@toon "8"`             | `identificatie.tone` / `tone="…"`            | `miscellaneous-field name="tone"`                         |
| do (grondtoon) | `@do F4`                | `muziek.do` / `do="F4"`                      | key / pitch-context                                       |
| modus          | `@mode major`           | `muziek.mode` / `mode="major"`               | key mode                                                  |

**Tempo-default:** in beide formaten **130** BPM als je geen tempo opgeeft
(export zet dan toch `sound tempo` 130 in mvsa-MusicXML; de metronoom blijft
onzichtbaar op blad, `.mscz` en PDF).

**Toon:** kerktoon / oktoechos-nummer. Keyword en term: **toon**; in MusicXML
blijft de veldnaam `tone` (compatibel met bestaande VSA-export).

## Alleen in één formaat

Niet forceren naar het andere formaat:

| Alleen `.mvsa`                                      | Alleen `.vsa`                                      |
| --------------------------------------------------- | -------------------------------------------------- |
| `@oct`, `@start`, `@sectie`, `@blok`, `@speelplan`  | `validate-ending`, `duration-model`, `meter`       |
| `@tekst`, `@mscz-newline`, `@---`                   | `reciting-mode`, `musicxml-profile`                |
| `@taal` (hulptekst / Coria-labels)                  | `part-name`, `midi-*`, `typografie.*`              |
| `@genre`, `@opmerkingen` (gereserveerd)             | `@include-vsa`                                     |

## Bestaande `.mvsa` bijwerken

Script in VSA-tooling (eerst dry-run, dan `--apply`):

```cmd
cd /d C:\Git\orthodox-ronl\bibliotheek
C:\Git\orthodox-ronl\VSA-tooling\scripts\migrate-metadata.cmd content-source

cd /d C:\Git\orthodox-ronl\VSA-tooling
scripts\migrate-metadata.cmd examples\mvsa --apply
```

Zet `@toon "N"` als die volgt uit titel of pad. Optioneel `--tempo` voor
expliciet `@tempo 130`. Zie `scripts/README.md`.

## Zie ook

- [Keywords (mvsa)](../specification-mvsa/keywords.md)
- [VSA-syntax — blokmetadata en YAML](../specification/syntax.md)
- [Metadatareferentie (VSA)](../reference/metadata.md)
- [mvsa schrijven 101](mvsa-schrijven-101.md)
