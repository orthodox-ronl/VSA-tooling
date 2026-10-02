# Canonieke checklists (.mxl / .mscz / PDF)

Doel: vastleggen wat **wij** als normale vorm zien in gegenereerde of
genormaliseerde `.mxl` / `.mscz` (en afgeleide MuseScore-PDF). Dat zijn de
targets voor export én voor eventuele diagonaal-normalisatie (zelfde formaat
→ ons profiel).

Geen herdefinitie van MusicXML of MuseScore — alleen onze conventies.
Normatieve eenstemmige MusicXML-details:
[rendering — MusicXML-export](../specification/rendering.md#musicxml-export).
Partituur-valkuilen:
[vsa-templates — rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md).
Oefenhoek-bronnen (VSA-demo; later hierheen):

- `VSA-demo/scripts/mscz-partituur-contract.md` — A4, typografie, maatstrepen, recite-print
- `VSA-demo/scripts/mscz-product-transforms.md` — PDF- en Coria-`.mxl`-transforms

## Gemeenschappelijke kern (MXL én MSCZ)

Zoveel mogelijk gelijk houden; **layout** (aantal balken, partijnamen) hoort
**niet** hier — die divergeert bewust (Coria vs leespartituur).

| #   | Eis                        | Toelichting                                                                                                                                                     |
| --- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K1  | **SATB-inhoud**            | Vier stemmen S/A/T/B zijn aanwezig (semantiek). *Hoe* ze op balken/parts liggen: zie checklist MXL vs MSCZ.                                                     |
| K2  | **Sync tekst ↔ toon**      | Elke gezongen lettergreep/positie heeft minstens één klinkende noot in elke stem die meezingt; melisma = meerdere noten op één tekstpositie.                    |
| K3  | **Melisma-lyrics**         | Tekst (lyric) op de **eerste** noot van het melisma; vervolgnoten zonder nieuwe woordtekst; canonieke export zet `<extend/>` (lyric-streep) op die eerste noot. |
| K4  | **Streepjes / `syllabic`** | Lettergreepgrenzen via MusicXML `syllabic` begin/middle/end/single — consistent met `-` in de brontekst.                                                        |
| K5  | **Recite vs gewone duur**  | Reciteertoon herkenbaar (encoding per kanaal); geen normale kwart vermomd als recite zonder reden.                                                              |
| K6  | **Geen spookrusten**       | Geen layout-truc-rusten die als zingbare stilte of foute pauzes klinken (tenzij bewust blad-aanwijzing → pauze in playback).                                    |
| K7  | **Toonsoort / do-context** | Key/fifths (en waar van toepassing MIDI-instrumentatie) sluiten aan op `@do` / blokmetadata.                                                                    |

## Checklist MXL (Coria / playback)

Primair profiel: **`playback`**. Zie ook
[MusicXML-exportprofielen](../specification/rendering.md#musicxml-exportprofielen)
en Oefenhoek `VSA-demo/scripts/mscz-product-transforms.md` (Coria-kolom).

| #   | Eis                            | Toelichting                                                                                                                                                                                                                                                                    |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| M1  | Kern K1–K7                     | —                                                                                                                                                                                                                                                                              |
| M2  | **Vier aparte parts**          | Soprano / Alto / Tenor / Bass (P1–P4). Coria kiest solo op **part**, niet op voice binnen één part. Geen canonieke “alles op twee balken” voor Coria-MXL.                                                                                                                      |
| M3  | **Lyrics per part**            | Elke part heeft de gezongen tekst (lyric number 1) zodat muted/solo stemmen tekst tonen.                                                                                                                                                                                       |
| M4  | **Coria-vriendelijk**          | Geen features die Coria stelselmatig breekt of negeert (volg `playback`-tabel in rendering.md).                                                                                                                                                                                |
| M5  | **Melisma-extend**             | Alleen op eerste noot: `<extend/>` zonder `type`; midden/eind **geen** `<lyric>`.                                                                                                                                                                                              |
| M5a | **Melisma same-pitch**         | Zelfde hoogte binnen één lettergreep → **één** noot (gestipte ELM behouden; Coria stript ties). Geen heraangeslagen half+kwart.                                                                                                                                                |
| M6  | **Voice/stem**                 | Expliciete `<voice>` / `<stem>` zoals in `playback` (getest t.o.v. MuseScore-roundtrip + Coria).                                                                                                                                                                               |
| M7  | **Blad-aanwijzing**            | Scopeloze aanwijzingen → hele-nootrust zonder lyrics (pauze), geen “meegezongen” tekst.                                                                                                                                                                                        |
| M8  | **MIDI: piano op elke part**   | Elke stempartij (P1–P4) heeft `midi-device` / `midi-instrument` met canonieke piano: `instrument-sound` = `keyboard.piano.grand`, `midi-program` = `1`, kanalen 1–4. Geen koorklank (`voice.choir.aahs`) als canonieke vorm. Eenstemmig `.vsa`-playback: zelfde piano-default. |
| M9  | **Geen engraving-only extras** | Geen verplichte `<defaults>`-typografie, geen `extend type="start/continue/stop"` als canonieke playback-vorm.                                                                                                                                                                 |
| M10 | **Recite-playback**            | **Geen** print-collapse / breve: elke lettergreep een klinkende noot (kwart of ELM). Feathered `\|\|O\|\|` uit MSCZ wordt bij Coria-export geëxplodeerd.                                                                                                                       |
| M11 | **SATB uit mvsa**              | Bij export uit `.mvsa`: vier parts P1–P4 zoals M2–M3.                                                                                                                                                                                                                          |
| M12 | **Dubbele maatstreep**         | Sectie-einde (`\|\|`) → `light-light`; Coria mag daar een pauzemaat van maken (Oefenhoek-transform).                                                                                                                                                                           |
| M13 | **Leidende gap-rusten**        | Bij Coria-export uit MSCZ: wissen; maat korter (`senza-misura`) — zie product-transforms.                                                                                                                                                                                      |
| M14 | **Voortekens**                 | `<accidental>` aanwezig voor betrouwbare playback.                                                                                                                                                                                                                             |
| M15 | **``@tekst``-pauze**           | Mid-flow `@tekst` (niet maat 1): zelfde `[PAUZE]`-maat als na `\|\|` (cue op de pauzemaat). Geen dubbele pauze als de vorige maat al sectie-einde is.                                                                                                                          |
| M16 | **Leidende `\|:`**             | Forward-repeat links op de **eerste inhoudsmaat**; geen lege rustmaat vóór die inhoud (zelfde semantiek als MSCZ S16).                                                                                                                                                         |

**Normalize-target MXL → MXL:** `mxl normalize` (zie
[`mxl` CLI](../reference/cli/mxl.md)) herschrijft naar deze checklist +
`playback`-encoding. Lees-gate zonder schrijven: `mxl validate`
(`--profile satb` of `mono`).

## Checklist MSCZ (partituur / MuseScore)

Primair: leesbare SATB-partituur in MuseScore 4 (en afgeleide print-PDF).
Bron van waarheid voor layout-pitfalls:
[rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md).
Oefenhoek-detailnorm (A4, typografie, copyright, recite-print):
`VSA-demo/scripts/mscz-partituur-contract.md`.
Leesregels in deze repo: [MSCZ-leesbaarheid](mscz-leesbaarheid.md).

| #   | Eis                                  | Toelichting                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S1  | Kern K1–K7                           | Semantiek gelijk aan MXL; **layout** wijkt af (S2–S4).                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| S2  | **Twee balken: SA + TB**             | Balk 1 = sopraan+alt (G-sleutel); balk 2 = tenor+bas (F-sleutel). Geen vier aparte notenbalken als canonieke partituur. Geen lege derde balk (na SAT+B-import weg).                                                                                                                                                                                                                                                                                                                                   |
| S3  | **Geen stem-indicaties**             | Geen partijnamen / instrumentnamen op de balken: niet `S`/`A`/`T`/`B`, niet `Soprano`, niet `S/A`, niet Women/Men als zichtbare balklabels. Stijl: partijnamen uit (`firstSystemInstNameVisibility` / `subsSystemInstNameVisibility` = 0).                                                                                                                                                                                                                                                            |
| S4  | **Stokrichting S/T↑ A/B↓**           | Per balk **twee voices**: S (voice 1) en T (voice 1) stok **omhoog**; A (voice 2) en B (voice 2) stok **omlaag** (zoals VSA-template / MuseScore-partituur). Geen Capella-achtige “één akkoordstok” als canonieke vorm.                                                                                                                                                                                                                                                                               |
| S5  | **Lyrics tussen de balken**          | Gezongen tekst onder de bovenste balk (niet vier keer herhaald, niet onder de bas als primaire plaats).                                                                                                                                                                                                                                                                                                                                                                                               |
| S6  | **Opent bruikbaar in MuseScore 4**   | SATB + lyrics zichtbaar/bewerkbaar voor de partituur-workflow.                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| S7  | **A4 + Style**                       | A4 staand, 15 mm marges; Source Sans 3 (lyrics 13 / word 12 / titel 18); geen eerste-systeem-inspring; laatste systeem vol; vaste systeemafstand (`minSystemDistance`/`maxSystemDistance`); geen vertical page-fill.                                                                                                                                                                                                                                                                                  |
| S8  | **Recite-print (spacers)**           | Bij `n ≥ 6`: **1–(n−2)–1** — randnoten + één stokloze `\|\|O\|\|` (eerste midden-lettergreep; MuseScore `headType` breve, metrisch = randduur) + **spacers** voor overige midden-lyrics (`visible=0` + `play=0` op de nootkop; lyrics zichtbaar; geen `print-object=no` op hele noot). Geen MusicXML `type=breve` als maatbreedte (MuseScore rekt die tot 8/4). Kortere recite = één noot per lettergreep. Zie [leesbaarheid](mscz-leesbaarheid.md).                                                  |
| S9  | **Maatstrepen**                      | Enkele streep = frase/adem; **dubbele** (`light-light`) = sectie-einde (`\|\|` in `.mvsa`) of scheiding vóór mid-flow `@tekst` (S15); slot = `light-heavy`. Eindstreep per systeem zichtbaar. Herhaalstrepen (`\|:` / `:\|` / `:\|\|`) blijven herhaalpunten tonen (S16).                                                                                                                                                                                                                             |
| S10 | **Maatnummers**                      | Eerste maat per systeem; interval 0.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| S11 | **Geen Coria-eis**                   | Mag engraving-achtige encodes bevatten; hoeft niet Coria-playback-vriendelijk te zijn.                                                                                                                                                                                                                                                                                                                                                                                                                |
| S12 | **Keten ok**                         | Gegenereerd via `mvsa → partituur-mxl → MuseScore` mag: na opslaan voldoet het bestand aan S1–S10 en S13–S19 (of wordt genormaliseerd).                                                                                                                                                                                                                                                                                                                                                               |
| S13 | **Melisma**                          | **MXL en MSCZ** (zie ook M5a). Lyric op eerste noot + `<extend/>`; bij **toonwissels** ook melisma-slur. **Zelfde-hoogte:** MusicXML-tussenbestand (partituur) blijft **I1** — ongestipte standaardduuren ≤ whole of **tie-keten** (veilige MuseScore-import; geen gestipte MusicXML-collapse / geen `type=breve`). **MSCZ-postprocess** trekt die tie-ketens daarna samen tot **één compacte noot, inclusief gestipt** (bijv. half+kwart → gestipte half) — leesbaar blad. Pure same-pitch-hold: ties in het tussenbestand, **geen** slur; op het eindblad bij voorkeur één noot. Geen Capella-fraseslurs. Zie [leesbaarheid R7](mscz-leesbaarheid.md). |
| S14 | **Geen mid-systeem-HBox**            | **Geen** horizontale frame (`HBox`) *tussen* maten van hetzelfde MuseScore-systeem. MuseScore tekent dan een **accolade/bracket middenin** het systeem. HBox alleen aan systeem-/staff-einde waar templates dat bewust doen; trailing lege HBox vóór `</Staff>` / colofon weg.                                                                                                                                                                                                                        |
| S15 | **Mid-flow `@tekst`**                | Cue als **SystemText** boven de ge-cue-de maat. Vorige maat: **dubbele streep** (`light-light`), tenzij daar al `:\|` / `:\|\|` / `\|\|` staat (die blijft). **Geen** spacermaat met notenbalklijnen en **geen** mid-systeem-HBox (S14). Wil je een regelsprong: `@mscz-newline`.                                                                                                                                                                                                                     |
| S16 | **Herhalingen zonder spookmaat**     | Leidende `\|:` → **linker** forward-repeat op de **eerste inhoudsmaat** (`start_bar`); **geen** lege rustmaat vóór die inhoud. `:\|` → rechter backward-repeat (`light-heavy` + dots); niet “opwaarderen” naar alleen `light-light` (dan verdwijnen de herhaalpunten).                                                                                                                                                                                                                                |
| S17 | **Geen lege spacer-maten**           | Geen korte rust-only maten (MusicXML-cue-spacers, `print-object=no`, lege `\|:`-restanten) in de canonieke partituur. Postprocess **stript** die maten; vervangt ze **niet** door mid-systeem-HBox.                                                                                                                                                                                                                                                                                                   |
| S18 | **Accolade alleen bij systeembegin** | Bracket/accolade hoort alleen aan het **begin van een MuseScore-systeem**. Geen extra accolade vóór een mid-flow cue of na een gap/HBox.                                                                                                                                                                                                                                                                                                                                                              |
| S19 | **`@tekst` = SystemText**            | Alle `@tekst`-cues zijn `SystemText` (niet `StaffText`). Match ook MuseScore-`<br/>` bij meerregelige cues (`...` op regel 2).                                                                                                                                                                                                                                                                                                                                                                        |

**Normalize-target MSCZ → MSCZ:** herschrijf/opnieuw genereren naar deze
checklist (beperkt wat wij vastleggen; geen volledige MuseScore-spec).

## Checklist PDF (afgeleide van MSCZ)

MuseScore-/basispartituur-PDF is **geen** apart bronformaat: dezelfde
visuele afspraken als MSCZ (twee balken, geen stem-indicaties, lyrics tussen
de balken, A4). Geen lettergreep-explosie, geen vier Coria-parts in de PDF.
Transforms: Oefenhoek `mscz-product-transforms.md` (PDF-kolom).

| #   | Eis                                  | Toelichting                                                                                                                                                                                      |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P1  | **Erft MSCZ S2–S5, S7–S10, S14–S19** | SA/TB, geen partijnamen, lyrics tussen balken, A4/Style, recite-spacers, maatstrepen; geen mid-systeem-HBox/spookmaten; cues als SystemText.                                                     |
| P2  | **Recite blijft compact**            | Printmodel (`\|\|O\|\|`); geen Coria-kwart-per-lettergreep.                                                                                                                                      |
| P3  | **Geen Coria-links**                 | Oefenmateriaal hoort niet in papieren/PDF-uitgave (tenzij later bewust toegevoegd).                                                                                                              |
| P4  | **Copyright-regel + colofon**        | **Later** (nog niet verplicht in deze toolchain): korte copyright-regel op **elke** pagina (footer) én een colofon (zoals Oefenhoek `mscz-partituur-contract`). Niet vergeten bij PDF-producten. |
| P5  | **Provenance (Oefenhoek)**           | Optioneel: partituur-hash / generator-meta zoals in product-transforms — nog niet verplicht in VSA-tooling-export.                                                                               |

*(Los daarvan: [`vsa pdf`](../reference/cli/pdf.md) render Markdown+VSA naar A4 —
andere pipeline, geen MuseScore-partituur.)*

## Verschillen bewust hangende houden

| Onderwerp          | `.mxl` (Coria)                                                        | `.mscz` / MuseScore-PDF (partituur)                                                                                |
| ------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Balken / parts     | vier parts S/A/T/B                                                    | twee balken SA + TB                                                                                                |
| Stem-labels        | part-namen Soprano…Bass (Coria-UI)                                    | **geen** zichtbare stem-indicaties                                                                                 |
| Instrument / MIDI  | piano op elke part (`keyboard.piano.grand`, M8)                       | geen Coria-MIDI-eis (leesblad); MuseScore kiest bij openen meestal piano                                           |
| Lyrics             | op elke part                                                          | één laag tussen de balken                                                                                          |
| Recite             | per lettergreep een noot                                              | 1–(n−2)–1 + spacers (zichtbare lyrics)                                                                             |
| Melisma-extend     | `<extend/>`; slur bij toonwissels                                     | `<extend/>`; slur bij toonwissels; geen extender onder recite                                                      |
| Melisma same-pitch | collapse tot **één** noot incl. gestipte ELM (M5a; Coria stript ties) | MusicXML: I1 tie-keten ongestipt; **MSCZ-postprocess**: compacte noot incl. stip (S13/R7) |
| Stokrichting       | (per part, vaak auto)                                                 | S/T omhoog, A/B omlaag (twee voices per balk)                                                                      |
| Typografie / Style | weglaten                                                              | wel (MuseScore A4)                                                                                                 |
| Blad-aanwijzing    | rust zonder lyric                                                     | mag op blad zichtbaar blijven                                                                                      |
| Mid-flow `@tekst`  | `[PAUZE]`-maat + cue (M15)                                            | dubbele streep + SystemText; **geen** HBox/spacermaat (S14–S15, S17–S19)                                           |
| Leidende `\|:`     | forward op eerste inhoudsmaat (M16)                                   | idem; geen lege rustmaat (S16)                                                                                     |
| Doel               | afspelen / Coria                                                      | lezen / bewerken / PDF                                                                                             |

## Bestandsnaamgeving (conventie)

Traceerbaarheid van conversies — **niet verplicht** op elke `-o`.

| Regel                                                  | Voorbeeld                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------ |
| Bij voorkeur in `generated/`: `stem.brontype.doeltype` | `alleluia.mvsa.mxl`, `alleluia.mscz.mvsa`, `tropaar.vsa.mxl` |
| **Laatste** segment = echte extensie voor tools        | `.mxl`, `.mvsa`, `.mscz`, `.mp3` / `.ogg` / `.wav`           |
| CLI-default mag enkelvoudig blijven                    | `-o out.mxl` of `<stem>.mxl`                                 |
| Geen fout als de naam “simpel” is                      | normalize/export falen niet op ontbrekende dubbele extensie  |

In `examples/mvsa/` worden conversieproducten **niet** gecommit (zie
`.gitignore`); alleen bron-`.mvsa` (+ README / ISSUES).

Zie ook [mvsa-conversies](../plans/mvsa-conversions.md).
