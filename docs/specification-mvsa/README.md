# Specificatie mvsa (draft)

**Status:** draft v0 (werkontwerp overgenomen uit experimenten; nog geen
parser/CLI).

Deze map is de specificatie van **mvsa**: meerstemmige invoer als
tekstbestanden (typisch `.mvsa`) met lyrics-regels en stemregels, bedoeld voor
VSCode en latere tooling.

Lees eerst: [Doel en scope](overview.md).

## Relatie tot andere specs

| Map                                                                    | Rol                                                      |
| ---------------------------------------------------------------------- | -------------------------------------------------------- |
| [`docs/specification/`](../specification/)                             | Normatieve eenstemmige [VSA](@) 1.0                      |
| [`docs/specification-vsa-templates/`](../specification-vsa-templates/) | Draft melodietemplates (YAML)                            |
| **`docs/specification-mvsa/`** (deze)                                  | Draft mvsa-syntax en -semantiek                          |
| [`docs/plans/mvsa-v0-syntax.md`](../plans/mvsa-v0-syntax.md)           | Werkplan / geschiedenis; bij conflict wint deze draft    |

Bij tegenstrijdigheid met VSA 1.0 over **gedeelde** tekens (ELM’s, laddergraden)
wint de VSA-spec tot mvsa die keuzes expliciet overneemt of afwijkt.

## Documenten

| Document                         | Inhoud                                              |
| -------------------------------- | --------------------------------------------------- |
| [Doel en scope](overview.md)     | Idee, niet-doelen, termen, defaults                 |
| [Syntax](syntax.md)              | Bestandsvorm, markers, maten, secties, L en stemmen |
| [Semantiek](semantics.md)        | Sync, recite, hoogte, directives, pitfalls          |
| [Validatie](validation.md)       | Geldigheidsregels (draft)                           |
| [Voorbeelden](examples.md)       | Pointers naar `examples/mvsa/`                      |
| [Open punten](open-points.md)    | Bewust later                                        |
| [Versionering](versioning.md)    | Draft-versiebeleid                                  |

## Bewust buiten scope (nu)

- Werkende parser of `vsa`-subcommanden voor `.mvsa`;
- MusicXML-/MSCZ-export uit mvsa;
- Blokhergebruik (`@voices`, secties kopiëren);
- Overlays van A/T/B t.o.v. S;
- Pagina-layout (MuseScore-“systemen” op een blad).
