# mvsa-experimenten

De map `examples/mvsa` is **geen** invoer voor `vsa validate` zolang er geen
mvsa-parser is. De `.mvsa`-bestanden volgen de draft-spec
[`docs/specification-mvsa/`](../../docs/specification-mvsa/README.md).
Achtergrond en eerdere schetsen:
[`docs/plans/mvsa-v0-syntax.md`](../../docs/plans/mvsa-v0-syntax.md).

Open de `.mvsa`-bestanden in VSCode met een **monospace**-lettertype.

| Bestand                              | Wat je ziet                                                                                         |
| ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `alleluia-toon-8.mvsa`               | Reciteertoon (`~`) + cadens; do-re-mi / a–g / `@oct` / EHM; canonieke `@sectie` + `\|\|`.           |
| `alleluia-toon-1.mvsa`               | Vrije SATB, relatief.                                                                               |
| `kleine-intocht-zondag-hemelum.mvsa` | Omzetting VSA-demo MusicXML; absolute `bb4`/`g3`, `@oct`, mix.                                      |
| `trisagion-8a-slav-hemelum.mvsa`     | Canonieke secties + **experimenteel** blokhergebruik (`@voices`, `L'` — nog niet normatief).        |

Canonieke vorm (draft): woordstreepjes tussen lettergrepen van hetzelfde woord;
maatstrepen op alle LSATB-regels; sectie-einde `||` op alle LSATB-regels.
