# Specificatie mvsa (draft)

**Status:** draft v0 (`validate` + MusicXML + MSCZ + import + `normalize` +
`kuiser` + `pdf` + `audio`).

Deze map is de specificatie van **mvsa**: meerstemmige invoer als
tekstbestanden (typisch `.mvsa`) met lyrics-regels en stemregels, bedoeld voor
VSCode en tooling.

Lees eerst: [Doel en scope](overview.md). Voor een taakgerichte introductie
(zonder de hele grammatica): [mvsa schrijven 101](../guides/mvsa-schrijven-101.md).

## Relatie tot andere specs

| Map                                                                             | Rol                                                         |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [`docs/specification/`](../specification/README.md)                             | Normatieve eenstemmige [VSA](@) 1.0                         |
| [`docs/specification-vsa-templates/`](../specification-vsa-templates/README.md) | Draft melodietemplates (YAML)                               |
| **`docs/specification-mvsa/`** (deze)                                           | Draft mvsa-syntax en -semantiek                             |
| [`docs/plans/mvsa-v0-syntax.md`](../plans/mvsa-v0-syntax.md)                    | Werkplan / geschiedenis; bij conflict wint deze draft       |
| [`docs/plans/mvsa-conversions.md`](../plans/mvsa-conversions.md)                | Conversiematrix (incl. normalisatie-diagonaal), CLI, slices |

Bij tegenstrijdigheid met VSA 1.0 over **gedeelde** tekens (ELM’s, laddergraden)
wint de VSA-spec tot mvsa die keuzes expliciet overneemt of afwijkt.

## Documenten

| Document                         | Inhoud                                              |
| -------------------------------- | --------------------------------------------------- |
| [Doel en scope](overview.md)     | Idee, niet-doelen, termen, defaults                 |
| [Syntax](syntax.md)              | Bestandsvorm, markers, maten, secties, L en stemmen |
| [Semantiek](semantics.md)        | Sync, recite, hoogte, directives, pitfalls          |
| [Keywords (`@…`)](keywords.md)   | Gedefinieerde `@`-regels: wat, wanneer, wel/niet    |
| [Speelplan](speelplan.md)        | `@blok` / `@speelplan`: bladvorm vs klinkende vorm  |
| [Validatie](validation.md)       | Geldigheidsregels (draft)                           |
| [Voorbeelden](examples.md)       | Pointers naar `examples/mvsa/`                      |
| [Open punten](open-points.md)    | Centrale backlog (nu + later)                       |
| [Versionering](versioning.md)    | Draft-versiebeleid                                  |

## Bewust buiten scope (nu)

- Blokhergebruik (`@voices`, secties kopiëren);
- Overlays van A/T/B t.o.v. S;
- Pagina-layout (MuseScore-“systemen” op een blad);
- Checklist-items voor lyric 2 / Coria-hulptekst-parts in
  [canonical-checklists](../formats/canonical-checklists.md) (export werkt al;
  normatieve M-items volgen later);
- Los MIDI-bestand (preview = [audio](../formats/audio.md)).

Wel beschikbaar: `vsa mvsa validate`, `musicxml`, `mscz`, `pdf`, `audio`,
`import`, `normalize`, `kuiser`; hulptekst via `--hulptekst` /
`--hulptekst-as-parts` (zie [kerkslavisch-transliteratie](../plans/kerkslavisch-transliteratie.md)).
Navigatiehub: [Formaten & CLI](../formats/index.md).
