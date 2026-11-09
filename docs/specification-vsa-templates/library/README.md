# Library: vsa-templates per genre × toon

Werkmap per formule. Gedeelde afspraken staan hier. **Nieuwe** formules:
map + id `{traditie}-{genre}-toon-{n}`. Legacy zonder traditie-prefix blijft
geldig.

## Mapstructuur

```text
library/
  README.md                      ← dit bestand (geldt voor alle formules)
  tropaar-toon-4/                ← legacy-id (Hemelum)
  groningen-tropaar-toon-4/      ← traditie in de id (voorkeur nieuw)
    template.yaml                ← canonieke formule
    template.mscz                ← formuleblad MuseScore (één bestand, geen .mscx)
    template.mxl                 ← formule MusicXML (delen)
    README.md                    ← kort: status, bron, pijplijn
    examples/corpus/             ← .vsa + afgeleide .mscz/.mxl
    notes/                       ← corpus, mappinglessen, besluiten
  …
```

### Traditie in het template-id

Nieuwe formules: id en mapnaam `{traditie}-{genre}-toon-{n}` (bijv.
`groningen-tropaar-toon-4`; later `hemelum-…` als die traditie een eigen YAML
krijgt). Zo is een tweede traditie een aparte map, geen stille overwrite.

Bestaande ids zonder prefix (`kondak-toon-1`, `tropaar-toon-4`, …) blijven;
de map-README noemt de traditie (meestal Groningen; `tropaar-toon-4` =
Hemelum). Playbook-aliassen wijzen naar het canonieke YAML-`id`.

Invalid schema-cases blijven in
`examples/invalid/` (geen formule-werkmap).

## Gedeelde afspraken

| Onderwerp          | Afspraak                                                                                                                                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Architectuur       | **VSA→template-instance** ([T1–T7](../vsa-mvsa-contract.md)): melodie uit VSA (default S), overige stemmen uit template                   |
| CLI                | `vsa mvsa --template <id>` — zie [vsa-mvsa.md](../../reference/cli/vsa-mvsa.md)                                                           |
| Lessen / checklist | [conversion-lessons.md](../conversion-lessons.md) (octaven, tempo, B-paden, same_as, nieuwe tonen)                                        |
| Contract           | [vsa-mvsa-contract.md](../vsa-mvsa-contract.md) · [mapping-vsa.md](../mapping-vsa.md) · [contract-index](../../formats/contract-index.md) |
| MusicXML-balken    | 2 partijen: P1 `S/A` (G), P2 `T/B` (F); per partij voice1=S of T, voice2=A of B; `backup`                                                 |
| Maatsoort          | bij voorkeur `senza-misura`; 4/4 tolereren in MuseScore-exports                                                                           |
| Optionele noten    | YAML `optional: true` ↔ MusicXML notehead parentheses                                                                                     |
| Pitches            | PDF/PNG = featurebron; menselijke MuseScore-edit → YAML                                                                                   |
| Renderer / sync    | Na YAML-wijziging: `python scripts\sync_library_templates.py [<id>…]` · check: `--check` · of `render_vsa_template_musicxml.py --all`     |
| Validatie          | `vsa template validate <pad>`                                                                                                             |

## Formuleblad vs instance

| Artefact                    | Rol                 | In git?       | Regenereren                                     |
| --------------------------- | ------------------- | ------------- | ----------------------------------------------- |
| `template.yaml`             | formule-bron        | ja            | handmatig                                       |
| `template.mscz`             | formule MuseScore   | ja (afgeleid) | `render_tropaar_toon4_corpus.py --template`     |
| `template.mxl`              | formule MusicXML    | ja (afgeleid) | idem / `render_vsa_template_musicxml.py --all`  |
| `template.pdf`              | formule print       | nee           | `--template --pdf`                              |
| corpus `.vsa`               | zangstuk-bron       | ja            | curated                                         |
| corpus `.mscz` / `.mxl`     | instance            | ja (afgeleid) | `render_tropaar_toon4_corpus.py`                |
| corpus `*.pdf`              | print               | nee           | `--pdf` / `--pdf-only`                          |

Formuleblad: ankers, frase-ids, cycle-frames, `||O||` zonder VSA-lyrics.
Instance: VSA-lyrics, recite-collapse, geen formulelabels; titel =
frontmatter-`title` (anders bestandsstem). Coria-MXL = instance zonder
collapse. Details: [rendering-pitfalls.md](../rendering-pitfalls.md).

**Geen** `template-from-yaml.mscx`/`.mscz` meer (één formule-MSCZ volstaat).
MuseScore-rommel (`.mscbackup/`, `Thumbnails/`, losse `META-INF/`, …) niet
committen.

## MuseScore-authoring (conventies)

Deze symbolen zijn **onze** semantiek; MuseScore zelf kent geen “recite”.

| In MuseScore                                                                        | Betekenis in template                                              |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Tekst `1`, `2`, `3`, … of `laatste` (cirkel, rechthoek, of zonder)                  | [frase-id](frase-id@) ([formulelabel](formulelabel@))              |
| Brevis-kop (` |     | O   |     | `), stemloos, halfnoot (2 tellen) | [reciteertoon](reciteertoon@) (`role: recite`) |
| Notehead met haakjes                                                       | `optional: true`                                            |
| Staff text `e. st.` / `l. st.` / `vl. st.` + pijl **eronder** naar de noot | [frase-anker](frase-anker@) ([formulelabel](formulelabel@)) |
| Staff text `\|\|: 1, 2 :\|\| laatste` of VBox onderaan                     | cycle-notatie (YAML `cycle`/`final`)                        |
| Duur quarter / half / whole                                                | ELM `~` / `_` / `__`                                        |

YAML-ankers zijn **zonder** spaties (`l.st.`); op het blad **mét** spaties
(`l. st.`). De pijl is hulpgrafiek, geen tweede [formulelabel](formulelabel@).

### Formuleblad (`.mscz`)

Het gegenereerde `template.mscz` dient voor twee dingen:

1. **Controle** — YAML en MuseScore in de pas houden terwijl de formule
   op orde komt.
2. **Koorprintje** — dezelfde partituur als printbare bron (PDF lokaal via
   `--template --pdf`).

Die tweede rol wint bij layoutkeuzes. Extra G-sleutels moeten weg. Extra
witruimte van verborgen rusten is ongewenst.

**Geen measure-padding.** De maatlengte is de som van de echte nootduren.

YAML → MuseScore + MXL (tropaar toon 4):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\render_tropaar_toon4_corpus.py --template
python scripts\render_tropaar_toon4_corpus.py --template --pdf
```

Overschrijf nooit de gebruikersoriginelen
(`Template - Tropaar (Toon 4).mscz` / `.musicxml` / `.mxl`).

### Sleutels

Geen `<Clef>` in maat 1 (dat tekende een tweede sleutel op het blad).
SA: G-sleutel via instrumentdefault. TB: bas-sleutel via
`<defaultConcertClef>F</defaultConcertClef>` en
`<defaultTransposingClef>F</defaultTransposingClef>` op de Part-Staff, plus
`<clef>F</clef>` in het instrument. MuseScore 4 leest de zichtbare sleutel
uit die staff-defaults; alleen Instrument-`<clef>` gaf nog een G-sleutel op
TB. Verborgen TimeSig 4/4 mag blijven. KeySig op beide balken is correct.

### Frames na de laatste maat

Vanuit lezersperspectief, na de laatste maat (cycle-form):

1. **lege horizontale frame** (`HBox`, spacer) — schuift de cycle-tekst
   ongeveer naar het midden (MuseScore centreert HBox-tekst niet betrouwbaar);
2. **horizontale frame met cycle-tekst** (`||: 1, 2 :|| laatste`).

Als de laatste [template-frase](template-frase@) **niet** alleen op een
systeem staat, of te breed is (meer dan
`CYCLE_HBOX_MAX_LAST_QUARTERS` kwartnoten), valt de renderer terug op één
**verticale frame** (`VBox`) onder de partituur.

### Formulelabels ([frase-id](frase-id@) en [frase-anker](frase-anker@))

Alles wat een **cijfer** is of precies **`laatste`**, telt als
[frase-id](frase-id@) — ongeacht enclosure (cirkel, vierkant, geen).
Rehearsal mark of staff text: beide oké. De vorm van het kader is geen extra
id.

Frase-ids en anker-afkortingen samen: [formulelabels](formulelabel@). In het
`.mscx` staan ze op **één vaste hoogte** (`y="-4.5"`, boven de noten,
autoplace uit, DejaVu Sans Condensed 12pt). Bij een frase-anker hoort extra
een pijl op **`y="-1.3"`** (onder het formulelabel); die pijl is geen tweede
label. In de bibliotheek wijst geen anker naar een recite-event (anker en
recite zijn altijd aparte events).

### Cycle-regel op het blad

Op de PDF staat vaak `||: 1, 2 :|| laatste`. Open **`template.mscz`**: daar
staat de regel in een **HBox** na de laatste maat (met lege spacer-HBox
ervoor), DejaVu Sans Condensed 14pt — of in een **VBox** als er te weinig
ruimte is. MusicXML/MXL kan MuseScore-Style/HBox/VBox **niet** round-trippen.
YAML-`cycle`/`final` blijft leidend.

### Laatste systeem niet uitrekken

In het **`.mscz`** staan de MuseScore-stijlen:
`enableVerticalSpread=0`, `maxPageFillSpread=0`, en lage gelijke
`minSystemDistance`/`maxSystemDistance` (anders vult MuseScore tot het
maximum, ook met vertical spread uit). `lastSystemFillLimit=1` op het formuleblad (100% —
laatste systeem rekt niet horizontaal). MusicXML kan die stijl niet dragen.

### Reciteertoon (||O||)

Op het blad is de [reciteertoon](reciteertoon@) een **brevis-kop** (het symbool
`||O||`) — **zonder** teken erboven (zoals in het toonboek/PDF). In het `.mscx`:

- `durationType` **half** (2 tellen afspelen én ruimte in de maat);
- `<headType>breve</headType>`;
- stok verborgen (`<noStem>1</noStem>`) op alle stemmen;
- **geen** fermata of decoratief symbool boven de noot.

YAML: `role: recite`. Mapping naar syllaben gebruikt later vooral de **rol**.

### Herhalingstekens (cycle-form)

Bij `cycle` + `final` in YAML zet de renderer in het `.mscx`:

- `<startRepeat/>` op de maat van het **eerste** cycle-frase-id;
- `<endRepeat>N</endRepeat>` op de maat van het **laatste** cycle-frase-id
  (`N` = aantal ids in `cycle`, bijv. `2` voor `1, 2`).

Dat correspondeert met `||: 1, 2 :||` op het blad. De cycle-tekst blijft in
de trailing HBox (of VBox als fallback).

### Ankers plaatsen

Twee opeenvolgende staff texts op de **noot** die het anker heeft (niet op
de maat): eerst de afkorting (`l. st.`), daaronder de pijl. Eén keer op de
S/A-partij volstaat.

### Tips tegen MuseScore-“intelligentie”

- Insert-modus bij ritmewijzigingen. Geen extra maatlengte of verborgen
  rusten: de MSCX is ook koorprint.
- Split/merge van formuleslots alleen als het blad dat zo heeft; VSA-tekst
  splitst later (instance).
- Eerst S, dan A (voice 2), dan TB.

## Formules aanwezig

| Map                                                              | Vorm      | Opmerking                                   |
| ---------------------------------------------------------------- | --------- | ------------------------------------------- |
| [`kondak-toon-1`](kondak-toon-1/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`kondak-toon-2`](kondak-toon-2/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`kondak-toon-5`](kondak-toon-5/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`kondak-toon-6`](kondak-toon-6/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`kondak-toon-7`](kondak-toon-7/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`kondak-toon-8`](kondak-toon-8/README.md)                       | cycle     | Groningen; also tropaar                     |
| [`tropaar-toon-1`](tropaar-toon-1/README.md)                     | cycle     |                                             |
| [`tropaar-toon-2`](tropaar-toon-2/README.md)                     | `same_as` | → kondak-toon-2                             |
| [`tropaar-toon-5`](tropaar-toon-5/README.md)                     | `same_as` | → kondak-toon-5                             |
| [`tropaar-toon-6`](tropaar-toon-6/README.md)                     | `same_as` | → kondak-toon-6                             |
| [`tropaar-toon-7`](tropaar-toon-7/README.md)                     | `same_as` | → kondak-toon-7                             |
| [`tropaar-toon-8`](tropaar-toon-8/README.md)                     | `same_as` | → kondak-toon-8                             |
| [`tropaar-toon-3`](tropaar-toon-3/README.md)                     | sequence  |                                             |
| [`tropaar-toon-4`](tropaar-toon-4/README.md)                     | cycle     | Hemelum; Elia-mapping + corpus              |
| [`groningen-tropaar-toon-4`](groningen-tropaar-toon-4/README.md) | cycle     | Groningen; also kondak; uit Nicolaas-schets |
| [`stichier-toon-5`](stichier-toon-5/README.md)                   | cycle     | PDF-stichier (niet Groningen kondak-5)      |
| [`vers-toon-1`](vers-toon-1/README.md)                           | cycle     |                                             |
| [`vers-toon-5`](vers-toon-5/README.md)                           | cycle     |                                             |

Normatieve syntax/semantiek: map erboven
([`../README.md`](../README.md)).
