# mvsa-experimenten

De map `examples/mvsa` is **geen** invoer voor `vsa validate` (eenstemmig).
Wel:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa validate examples\mvsa
vsa mvsa musicxml examples\mvsa\kleine-intocht-zondag-hemelum.mvsa --section schets-a-bladcijfer -o generated\intocht-a.mxl
```

De `.mvsa`-bestanden volgen de draft-spec
[`docs/specification-mvsa/`](../../docs/specification-mvsa/README.md).
Achtergrond:
[`docs/plans/mvsa-v0-syntax.md`](../../docs/plans/mvsa-v0-syntax.md).

Open de `.mvsa`-bestanden in VSCode met een **monospace**-lettertype.

Tijdelijke afgeleiden (later weer weg): naast elk bronbestand staan
`*.mvsa.mvsa` (normalize, default **preserve** = zelfde noteernamen),
`*.mvsa.mxl`, `*.mvsa.mscz`, `*.mvsa.pdf` (MuseScore-partituur voor
zangers) — **overschrijf de originelen niet**. Lokaal bouwen:
`make.cmd naam` of `make.cmd all` (PDF vereist MuseScore 4).
Leesbaarheid: [MSCZ-leesbaarheid](../../docs/formats/mscz-leesbaarheid.md).

| Bestand                              | Wat je ziet                                                                              |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| `alleluia-toon-1.mvsa`               | `@speelplan 1,2,1,2,1,3` → volta op partituur                                            |
| `alleluia-toon-2.mvsa` … `8.mvsa`    | Eén doorlopende cadens (geen speelplan)                                                  |
| `1a-vredeslitanie.mvsa` | Open herhaling met `\|:` … `: | ` (geen speelplan); blad én Coria via MusicXML-`<repeat>` |
| `3-eerste-kleine-litanie.mvsa`       | Korte litanie, antwoorden één keer uitgeschreven |
| `kleine-intocht-zondag-hemelum.mvsa` | Omzetting VSA-demo MusicXML; absolute `bb4`/`g3` |
| `trisagion-8a-slav-hemelum.mvsa`     | `@speelplan` → Segno / Fine / D.S. al Fine       |

**Speelplan vs `|:…:|`:** vaste klinkende volgorde → één `@speelplan` per
`.mvsa` met `@blok` (Coria schrijft uit; blad: volta / herhaling / D.S. of
expand). Open litanie-herhaling (N onbekend) → `|:…:|` zonder speelplan.
`@sectie` alleen in bestanden zonder speelplan (schetsen / `--section`).

Canonieke vorm (draft): woordstreepjes tussen lettergrepen van hetzelfde woord;
maatstrepen op alle LSATB-regels; bij **secties** eindstreep `||` op het
laatste systeem; tussen **speelblokken** is `||` geen eis. **Lege regel**
tussen vscode-systemen (geen `@---` nodig).
