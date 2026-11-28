# `@include-vsa` referentie

Status: geïmplementeerd voor `id=`. `zoek=`, `lokaal=` en `bron:` zijn verwijderd (zie [Verwijderd](#verwijderd)).

## Syntax

```vsa
refrein: @include-vsa id=troparion-geboorte-moeder-gods/obikhod/groningen
```

## Parameters

| Parameter | Bron                                                                  | Opmerking                          |
| --------- | --------------------------------------------------------------------- | ---------------------------------- |
| `id=`     | Pad onder `content-source/catalogus/` (zangstuk/variant/uitvoeringsvorm) | Moet precies één `.vsa` opleveren |

Alleen de substring `@include-vsa ...` wordt vervangen; tekst ervoor blijft staan.

## Resolve-contract

| Uitkomst                         | Gedrag bij `@include-vsa` / `vsa validate` |
| -------------------------------- | ------------------------------------------ |
| Geen `.vsa` onder de map van id  | Fout                                       |
| Meer dan één `.vsa`              | Fout (`id` is niet uniek)                  |

## Expand

De doel-`.vsa` wordt gelezen, frontmatter wordt gestript en de body wordt in-memory ingevoegd.

Het brondocument wordt niet gewijzigd.

## Verwijderd

`@include-vsa zoek="…"`, `@include-vsa lokaal=…` en in markdown `:::include bron:…`
worden niet meer ondersteund en geven een foutmelding. Ook de opdracht
`vsa resolve-catalogus` en de optie `--bron-root` bestaan niet meer.
Verwijs in plaats daarvan met `id=` of met een bestandspad.

## Implementatiestatus

| Onderdeel                                             | Status             |
| ----------------------------------------------------- | ------------------ |
| `expand_include_vsa`                                  | Geïmplementeerd    |
| `@include-vsa id=`                                    | Geïmplementeerd    |
| `@include-vsa lokaal=`, `bron:`, `zoek=`              | Verwijderd         |
| Integratie validate / svg / musicxml / build-markdown | Geïmplementeerd    |
