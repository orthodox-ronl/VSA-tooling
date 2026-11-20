# `@include-vsa` referentie

Status: geïmplementeerd voor `id=` en `lokaal=`. `zoek=` is verwijderd (zie [Verwijderd: `zoek=`](#verwijderd-zoek)).

## Syntax

```vsa
refrein: @include-vsa id=troparion-geboorte-moeder-gods/troparion-geboorte-moeder-gods/liturgikon
refrein: @include-vsa lokaal=cherubijnenhymne/kastorski/groningen/groningen-vsa
```

## Parameters

| Parameter | Bron                                  | Opmerking                    |
| --------- | ------------------------------------- | ---------------------------- |
| `id=`     | Catalogus; beide herkomsten           | Lokaal wint bij conflict     |
| `lokaal=` | Catalogus; parochie `lokaal/`         | Lokale bron                  |

De twee parameters zijn wederzijds exclusief.

Alleen de substring `@include-vsa ...` wordt vervangen; tekst ervoor blijft staan.

## Resolve-contract

| Uitkomst catalogus                 | Gedrag bij `@include-vsa` / `vsa validate` |
| ---------------------------------- | ------------------------------------------ |
| Geen match                         | Fout                                       |
| Meerdere matches                   | Fout (`AmbiguousError`)                    |

## Expand

De doel-`.vsa` wordt gelezen, frontmatter wordt gestript en de body wordt in-memory ingevoegd.

Het brondocument wordt niet gewijzigd.

## Verwijderd: `zoek=`

`@include-vsa zoek="…"` en `:::include … zoek="…"` worden niet meer ondersteund
en geven een foutmelding. Ook de opdracht `vsa resolve-catalogus` bestaat niet meer.
Verwijs in plaats daarvan met `id=` of `lokaal=`, of met een bestandspad.

## Implementatiestatus

| Onderdeel                                             | Status             |
| ----------------------------------------------------- | ------------------ |
| `expand_include_vsa`                                  | Geïmplementeerd    |
| `@include-vsa id=`                                    | Geïmplementeerd    |
| `@include-vsa lokaal=`                                | Geïmplementeerd    |
| `@include-vsa zoek=`                                  | Verwijderd         |
| Integratie validate / svg / musicxml / build-markdown | Geïmplementeerd    |
