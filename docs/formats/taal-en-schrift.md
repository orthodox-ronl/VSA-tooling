# Taal en schrift

**Taal** is wat er gezongen wordt. **Schrift** is met welke letters de tekst
geschreven is. Het zijn twee verschillende eigenschappen, en een naam of code
zegt altijd maar één van de twee. Deze pagina is de norm voor VSA-tooling en
voor de repo `bibliotheek`. Start: [contract-index](contract-index.md).

## Begrippen

| Begrip         | Betekenis                                             | Codes                    |
| -------------- | ----------------------------------------------------- | ------------------------ |
| Taal           | Wat gezongen wordt: Nederlands, Kerkslavisch, …       | `nl`, `ksl`, `ro`, `el`  |
| Schrift        | De letters: Latijns schrift of Cyrillisch schrift     | `latn`, `cyrl`           |
| Brontekst      | De tekst zoals die in `.vsa` of `.mvsa` staat         | n.v.t.                   |
| Transliteratie | Dezelfde tekst in het andere schrift; taal blijft     | zie [Namen](#namen)      |

Kerkslavisch is een eigen kerktaal en niet hetzelfde als Russisch. Schrijf
daarom «Kerkslavisch».

## Regels voor de brontekst

1. Nederlands staat in de bron altijd in Latijns schrift. Kerkslavisch staat
   in de bron altijd in Cyrillisch schrift.
2. Zonder aanduiding geldt daarom: Latijns schrift is Nederlands, Cyrillisch
   schrift is Kerkslavisch. Zo werken ook stukken in beide talen.
3. `Kyrie eleison` geldt als Nederlands.
4. Een andere taal markeer je met `@taal` en de taalcode, bijvoorbeeld
   `@taal ro`. Zo'n passage krijgt geen transliteratie en geen
   woordenlijst-controle (zie [syllabificatie](syllabificatie.md)).
5. De frontmatter noemt de taal van het stuk: `taal: nl`, `taal: ksl` of
   `taal: [nl, ksl]`.

## Transliteratie

| Brontekst                      | Taal         | Transliteratie in  | Voorbeeld                              |
| ------------------------------ | ------------ | ------------------ | -------------------------------------- |
| Nederlands (Latijns schrift)   | Nederlands   | Cyrillisch schrift | `Heer` → `Хиир`, `Ky-ri-e` → `Ки-ри-е` |
| Kerkslavisch (Cyrillisch)      | Kerkslavisch | Latijns schrift    | `Господи` → `Gospodi`                  |

Een transliteratie verandert de taal niet. `Хиир` is Nederlands in Cyrillisch
schrift, geen Kerkslavisch. Welke transliteraties een bron nodig heeft, volgt
alleen uit de gezongen tekst; zie [translit-svg](translit-svg.md). De gekozen
schrijfwijzen staan in
[transliteraties-keuzes](../plans/transliteraties-keuzes.md).

Gebruik het woord «transliteratie» (kort: «translit»), niet «hulptekst».

## Namen

Een deel van de bestaande namen gebruikt een taalcode waar een schrift bedoeld
is. De namen in de kolom «Nu» werken totdat ze vervangen zijn. Voer geen
nieuwe namen van die soort in.

| Waar                              | Nu                  | Wordt                | Betekent                             |
| --------------------------------- | ------------------- | -------------------- | ------------------------------------ |
| `--translit-modus`                | `nls`               | `latn`               | transliteratie in Latijns schrift    |
| `--translit-modus`                | `ksl`               | `cyrl`               | transliteratie in Cyrillisch schrift |
| Productbestand                    | `.translit-nls.svg` | `.translit-latn.svg` | transliteratie in Latijns schrift    |
| Productbestand                    | `.translit-ksl.svg` | `.translit-cyrl.svg` | transliteratie in Cyrillisch schrift |
| Knop op de bibliotheek-site       | `Ксл→Nls`           | `Ксл→Latn`           | Kerkslavisch meelezen                |
| Knop op de bibliotheek-site       | `Nls→Ксл`           | `Nls→Кирл`           | Nederlands meelezen                  |

De code `ksl` blijft de taalcode voor Kerkslavisch, ook in mapnamen zoals
`hemelum-ksl`.

## Nog niet afgedwongen

De volgende regels gelden als afspraak, maar het programma controleert ze nog
niet:

- een bron zonder `taal` is een fout; conversies en `fix` vullen de taal zo veel
  mogelijk zelf in;
- een aanduiding die het schrift tegenspreekt (bijvoorbeeld `@taal nl` boven
  Cyrillische tekst) is een fout;
- in `.vsa` houdt de transliteratie nog geen rekening met `@taal`; alleen in
  `.mvsa` krijgt een passage in een andere taal al geen transliteratie;
- `--lyrics-lang` en de keuze van de woordenlijst volgen eerst de aangegeven
  taal en pas daarna het schrift.

## Schrijven in docs, code en berichten

- «Nederlands» en «Kerkslavisch» betekenen altijd de taal.
- Voor letters schrijf je «Latijns schrift» en «Cyrillisch schrift», nooit
  alleen «Cyrillisch» of «Latijn» als daarmee een taal bedoeld kan worden.
- Een variabele of optie voor een schrift heet naar het schrift (`latn`,
  `cyrl`), een variabele voor een taal naar de taal (`nl`, `ksl`).
