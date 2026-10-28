# Kale muziek-SVG en uitgaven (afspraak)

| Veld            | Waarde                                                                                                                                                                 |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**      | afspraak vastgelegd; **niet normatief** tot specificatie; implementatie gefaseerd                                                                                      |
| **Doel**        | Eén model voor kale muziekbeelden (SVG) die zowel website als print-PDF voeden, zonder metadata-dubbeling tussen catalogus en koormap                                  |
| **Eigenaar**    | Tooling-contract: [VSA-tooling](@bron); samenstelling/PDF: bibliotheek (`pagina-pdf`, koormap-paginataal)                                                              |
| **Gerelateerd** | [mvsa-svg](../formats/mvsa-svg.md), [gebruikseisen-dragers](gebruikseisen-dragers.md), [partituur-ir](partituur-ir.md), bibliotheek `docs/specs/koormap-paginataal.md` |

---

## 1. Afspraak (vastgelegd)

### 1.1 Drie lagen

| Laag              | Wat het is                                                                 | Voorbeeld                                              |
| ----------------- | -------------------------------------------------------------------------- | ------------------------------------------------------ |
| Bron              | Notatie (+ muzikale metadata in het bronbestand)                           | `.mvsa` / `.vsa` / `.mscz`                             |
| Kale muziek       | Alleen notenbalken; **geen** titel, componist, copyright, catalogus-id     | layout ``muziek`` → SVG                                |
| Samenstelling     | Layout + welke metadata voor welke uitgave                                 | catalogus- of koormap-`index.md` + shortcodes          |

Menselijke metadata (titel, bron, id, koormapnummer, copyright-vermelding op
het blad) komt uit de **samenstelling** (Markdown / frontmatter / shortcodes),
niet opnieuw uit het MuseScore-titelblok wanneer je een pagina-PDF bouwt.

### 1.2 Twee kale SVG-rollen

| Rol            | Doel                                      | Vorm (doelbeeld)                                                                 |
| -------------- | ----------------------------------------- | -------------------------------------------------------------------------------- |
| **Scherm-SVG** | Website-fallback (pc, tablet, telefoon)   | **Één** tall compacte MuseScore-SVG; mag scrollen; dynamisch schalen             |
| **Print-PDF**  | `index.md.pdf` (Download/Print pagina)    | Zelfde tall-SVG, gesneden op systeembrenzen naar A4                              |

Zelfde sibling-SVG voor scherm-fallback én print-compose. Scherm-hoofdpad
blijft Score-IR/OSMD (§4). A4-bladreeks (`stem-N.svg`) is verlaten.

### 1.3 Twee PDF-soorten — niet door elkaar

| PDF                                 | Metadata uit                         | Mag catalogus-sibling-PDF als bouwsteen?           |
| ----------------------------------- | ------------------------------------ | -------------------------------------------------- |
| Catalogus-blad (sibling)            | Catalogus-samenstelling / oefenblad  | — (dit *is* de catalogus-PDF)                      |
| Koormap-pagina (`index.pagina.pdf`) | Koormap-`index.md` (`kop`, …)        | **Nee** — alleen kale blad-SVG’s + Markdown-layout |

Catalogus-`.mvsa.pdf` / `.vsa.pdf` mag blijven als download van **dat
catalogusstuk**. Die PDF mag **niet** de input zijn waarmee `pagina-pdf` een
koormapblad samenstelt (anders krijg je catalogus- én koormap-metadata).

### 1.4 Wat web en print wel/niet delen

- **Delen:** kale muziekbeelden (SVG).
- **Niet delen:** chrome (titels, colofon, nummers) — die zet de samenstelling
  per uitgave.
- **Web:** geen vaste A4-eis; langere stukken mogen hoog of gestapeld.
- **Print:** vaste paginering (A4); `pdf-bijelkaar` / `--compact` blijven
  middelen om “dit hoort op één blad” na te streven.

---

## 2. Huidige toestand (kort)

| Onderdeel                                    | Nu                                                                                          |
| -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `mvsa`/`mscz` `svg` + `products`             | Eén tall compacte kale SVG (geen bladreeks)                                                 |
| Catalogus-sibling PDF                        | MuseScore layout ``partituur`` (titel/colofon in het scorebestand)                          |
| bibliotheek `pdf.cmd` / `index.md.pdf`       | Bestaande tall-SVG + Markdown; systeemsnee naar A4 (lokaal exporteren alleen indien SVG ontbreekt) |
| Lange stukken                                | Tall-SVG + snede; scherm: Score-IR/OSMD (fase 3)                                            |

---

## 3. Gefaseerd werk (volgorde)

| Fase | Wat                                                                                          | Repo’s                              | Status            |
| ---- | -------------------------------------------------------------------------------------------- | ----------------------------------- | ----------------- |
| 0    | Deze afspraak vastleggen + herinnering schermpad / Score-IR                                  | VSA-tooling (+ pointer bibliotheek) | **gedaan**        |
| 1    | ~~Bladreeks~~ → **één tall compacte SVG** als product (scherm-fallback + print-bouwsteen)   | VSA-tooling                         | **gedaan** (tall) |
| 2    | `pagina-pdf`: samenstellen uit blad-SVG’s + Markdown; catalogus-PDF-plakpad uitfaseren       | bibliotheek                         | **gedaan**        |
| 3    | **Score-IR/OSMD** als productieschermpad (geen MuseScore-paginamodel op de site)             | VSA-tooling + bibliotheek           | **deels** — §4    |

Fase 3: richting is vast; bibliotheek toont canonieke `.mvsa` via from-ir →
OSMD (incl. S8 A1 — [osmd-s8-recite](osmd-s8-recite.md)). Rest open: zie §4.

---

## 4. Open verplichting: Score-IR/OSMD als schermpad

**Richting (vastgelegd):** productiescherm = **Score-IR → MusicXML (uit IR) →
OSMD**. MuseScore-tall-SVG is **fallback** + bouwsteen voor `index.md.pdf`,
niet de schermmotor. MSCZ / blad-PDF blijven MuseScore.

Contract voor koormap (shortcode `muziek`) en latere CoriB-consumptie:
[partituur-ir](partituur-ir.md) §7 (Scherm- en CoriB-brug). Tooling-siblings:
`lied.mvsa.score-ir.json` + `lied.mvsa.from-ir.musicxml` via
`mvsa score-ir … --musicxml`. Bewijs: spike
`examples/spikes/partituur-browser/`.

**Stand:** bibliotheek-shortcode `muziek` / catalogus gebruikt from-ir → OSMD
voor canonieke `.mvsa` (S8: A1-adapter, geen SVG-bypass —
[osmd-s8-recite](osmd-s8-recite.md)). **Nog open t.o.v. eindbeeld §4:** o.a.
`.vsa` zonder Score-IR, cue-/SVG-pariteit, CoriB. MuseScore-SVG blijft
fallback, niet het S8-schermpad.

**Herinneringsborging (naast dit plan):**

- Cursor-regel `.cursor/rules/kale-muziek-svg-uitgaven.mdc` — bij werk aan
  SVG-export, Score-IR of pagina-PDF: fase 3 noemen als productie-embed nog
  open is.
- Cross-link in [partituur-ir](partituur-ir.md) §7–§8.

---

## 5. Wat dit géén is

- Geen normatieve wijziging van CLI-gedrag in deze documentronde.
- Geen verplichting om catalogus-sibling-PDF af te schaffen — alleen om die
  niet meer als koormap-bouwsteen te gebruiken.
- Geen vervanging van OSMD door tall-SVG op het scherm (§4); tall-SVG = fallback + print.
