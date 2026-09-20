# mvsa-experimenten

De map `examples/mvsa` is **geen** invoer voor `vsa validate`. De `.mvsa`-bestanden
oefenen de schrijfsyntax uit
[`docs/plans/mvsa-v0-syntax.md`](../../docs/plans/mvsa-v0-syntax.md)
(L-regel + stemregels). Open de `.mvsa`-bestanden in VSCode met een
**monospace**-lettertype.

| Bestand                              | Wat je ziet                                                                                           |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `alleluia-toon-8.mvsa`               | Reciteertoon (`~`) + cadens; do-re-mi / a–g / `@oct` / EHM.                                           |
| `alleluia-toon-1.mvsa`               | Vrije SATB, relatief.                                                                                 |
| `kleine-intocht-zondag-hemelum.mvsa` | Omzetting VSA-demo MusicXML; absolute `bb4`/`g3`, `@oct`, mix.                                        |
| `trisagion-8a-slav-hemelum.mvsa`     | Blokhergebruik: `L`/`L'`, `@voices =:…`, `@:final = :nl1[3-4] + :slav1` (plan §11).                   |

De tenor van Alleluia toon 8 is gelijkgetrokken (D/C-lijn). De bas gebruikt
`so-2`/`c-2` naast `do-`/`f-`: het octaafsuffix telt vanaf het do-octaaf, niet
vanaf C. Zie het commentaar bovenaan `alleluia-toon-8.mvsa` en plan §2.2.1.
