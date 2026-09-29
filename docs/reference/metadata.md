# Metadatareferentie

## Markdown-blokmetadata

Metadata kan direct onder de openingsregel van een VSA-codeblok staan.

```markdown
::: vsa-notatie
do="F4"
mode="major"
tempo="132"
[:] Tekst {met_} notatie
:::
```

| Parameter           | Betekenis                                      |
| ------------------- | ---------------------------------------------- |
| `do`                | Grondtoon, bijvoorbeeld `F4`                   |
| `mode`              | Modus, bijvoorbeeld `major` of `minor`         |
| `tempo`             | Tempo in BPM                                   |
| `validate-ending`   | Eindmarkering valideren                        |
| `duration-model`    | Model voor duurinterpretatie                   |

Vrije parameters mogen voorkomen en kunnen door [renderers](@) of exporteurs worden gebruikt.

## `.vsa`-frontmatter

Zelfstandige `.vsa`-bestanden kunnen YAML-frontmatter bevatten.

```yaml
---
muziek:
  do: F4
  mode: major
  tempo: 132
identificatie:
  title: Tropaar van de zondag, toon 1
  composer: Traditioneel
  language: nl
---
[:] Tekst {met_} notatie
```

## Secties

| Sectie           | Doel                                      |
| ---------------- | ----------------------------------------- |
| `muziek`         | Muzikale interpretatie                    |
| `identificatie`  | Titel, componist, taal en brongegevens    |
| `typografie`     | Lettertype- en rendererinstellingen       |
| `liturgie`       | Toekomstige liturgische [metadata](@)     |
| `publicatie`     | Toekomstige publicatiemetadata            |

## Velden in `muziek`

| Veld                 | Betekenis                                             |
| -------------------- | ----------------------------------------------------- |
| `do`                 | Grondtoon, bijvoorbeeld `F4`                          |
| `mode`               | Modus: `major` of `minor`                             |
| `tempo`              | Tempo in BPM                                          |
| `meter`              | Maatsoort, bijvoorbeeld `4/4`                         |
| `reciting-mode`      | Ongescopte tekst in MusicXML                          |
| `musicxml-profile`   | Exportprofiel: `playback` of `engraving`              |
| `part-name`          | Partijnaam in MusicXML                                |
| `midi-sound`         | General MIDI-instrument (canonieke default: piano)    |
| `midi-channel`       | MIDI-kanaal 1–16                                      |
| `midi-program`       | MIDI-programmanummer (canonieke default: `1` = piano) |
| `midi-volume`        | MIDI-volume 0–100                                     |
| `midi-pan`           | MIDI-panning −100…100                                 |

## Velden in `identificatie`

| Veld        | Betekenis                       |
| ----------- | ------------------------------- |
| `title`     | Titel van het [zangstuk](@bron) |
| `subtitle`  | Ondertitel                      |
| `composer`  | Componist of bron               |
| `language`  | Taalcode                        |
