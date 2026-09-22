# Voorbeelden (draft)

Normatieve of semi-normatieve voorbeelden staan als experimentele bestanden
onder [`examples/mvsa/`](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/mvsa). Valideren:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa validate examples\mvsa
```

| Bestand                                                                                        | Wat het illustreert                                                           |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| [`alleluia-toon-8.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/alleluia-toon-8.mvsa) | Recite, laddergraden, toonnamen, `@oct`, EHM                                  |
| [`alleluia-toon-1.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/alleluia-toon-1.mvsa) | Vrije SATB, relatief                                                          |
| [`kleine-intocht-zondag-hemelum.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/kleine-intocht-zondag-hemelum.mvsa) | Omzetting uit MusicXML; absolute octaafcijfers                                |
| [`trisagion-8a-slav-hemelum.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/mvsa/trisagion-8a-slav-hemelum.mvsa) | ELM’s, melisma, recite; experimenteel blokhergebruik (nog **niet** normatief) |

Werkplan met woordenlijst en achtergrond:
[`docs/plans/mvsa-v0-syntax.md`](../plans/mvsa-v0-syntax.md).

Bij het bijwerken van voorbeelden: streef naar de canonieke vorm uit
[Syntax](syntax.md) (woordstreepjes, `|` / `||` op alle LSATB-regels). Oudere
schetsen in hetzelfde bestand mogen als commentaar blijven staan.
