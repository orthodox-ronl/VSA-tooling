# Canonieke checklists (.mxl / .mscz)

Doel: vastleggen wat **wij** als normale vorm zien in gegenereerde of
genormaliseerde `.mxl` / `.mscz`. Dat zijn de targets voor export én voor
eventuele diagonaal-normalisatie (zelfde formaat → ons profiel).

Geen herdefinitie van MusicXML of MuseScore — alleen onze conventies.
Normatieve eenstemmige MusicXML-details:
[rendering — MusicXML-export](../specification/rendering.md#musicxml-export).
Partituur-valkuilen:
[vsa-templates — rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md).

## Gemeenschappelijke kern (MXL én MSCZ)

Zoveel mogelijk gelijk houden; afwijken alleen waar de consumer (Coria vs
MuseScore-partituur) het eist.

| # | Eis | Toelichting |
| - | --- | ----------- |
| K1 | **SATB = vier parts** | Apart: Soprano / Alto / Tenor / Bass (of P1–P4). Geen “alles op één balk” als canonieke meerstemmige output. |
| K2 | **Sync tekst ↔ toon** | Elke gezongen lettergreep/positie heeft minstens één klinkende noot in elke stem die meezingt; melisma = meerdere noten op één tekstpositie. |
| K3 | **Melisma-lyrics** | Tekst (lyric) op de **eerste** noot van het melisma; vervolgnoten zonder nieuwe woordtekst (extend volgens profiel). |
| K4 | **Streepjes / `syllabic`** | Lettergreepgrenzen via MusicXML `syllabic` begin/middle/end/single — consistent met `-` in de brontekst. |
| K5 | **Recite vs gewone duur** | Reciteertoon herkenbaar (bijv. breve / aparte encoding); geen normale kwart vermomd als recite zonder reden. |
| K6 | **Geen spookrusten** | Geen layout-truc-rusten die als zingbare stilte of foute pauzes klinken (tenzij bewust blad-aanwijzing → pauze in playback). |
| K7 | **Toonsoort / do-context** | Key/fifths (en waar van toepassing MIDI-instrumentatie) sluiten aan op `@do` / blokmetadata. |

## Checklist MXL (Coria / playback)

Primair profiel: **`playback`**. Zie ook
[MusicXML-exportprofielen](../specification/rendering.md#musicxml-exportprofielen).

| # | Eis | Toelichting |
| - | --- | ----------- |
| M1 | Kern K1–K7 | — |
| M2 | **Coria-vriendelijk** | Geen features die Coria stelselmatig breekt of negeert (volg `playback`-tabel in rendering.md). |
| M3 | **Melisma-extend** | Alleen op eerste noot: `<extend/>` zonder `type`; midden/eind **geen** `<lyric>`. |
| M4 | **Voice/stem** | Expliciete `<voice>` / `<stem>` zoals in `playback` (getest t.o.v. MuseScore-roundtrip + Coria). |
| M5 | **Blad-aanwijzing** | Scopeloze aanwijzingen → hele-nootrust zonder lyrics (pauze), geen “meegezongen” tekst. |
| M6 | **MIDI in part-list** | `midi-device` / `midi-instrument` aanwezig (defaults uit metadata). |
| M7 | **Geen engraving-only extras** | Geen verplichte `<defaults>`-typografie, geen `extend type="start/continue/stop"` als canonieke playback-vorm. |
| M8 | **SATB uit mvsa** | Bij export uit `.mvsa`: vier parts P1–P4 met lyrics (lyric number 1) op de sopraan-lijn als primaire tekstlaag. |

**Normalize-target MXL → MXL:** herschrijf naar deze checklist +
`playback`-encoding (nog te implementeren als CLI-diagonaal).

## Checklist MSCZ (partituur / MuseScore)

Primair: leesbare SATB-partituur in MuseScore 4. Bron van waarheid voor
layout-pitfalls: [rendering-pitfalls](../specification-vsa-templates/rendering-pitfalls.md).

| # | Eis | Toelichting |
| - | --- | ----------- |
| S1 | Kern K1–K7 | Semantiek gelijk aan MXL; layout mag rijker. |
| S2 | **Opent bruikbaar in MuseScore 4** | Geen “toevallig open”: SATB + lyrics zichtbaar/bewerkbaar voor de partituur-workflow. |
| S3 | **Layout die MusicXML kwijtraakt** | Style / VBox / spacer-conventies volgens template-pipeline waar van toepassing. |
| S4 | **Recite-print** | Collapse / spacers / `position` volgens pitfalls (geen longa-hack, geen joined lyric + extender onder recite-tekst). |
| S5 | **Maatstrepen / herhalingen** | Zichtbaarheid en herhaaltekens zoals MuseScore 4 ze leest (o.a. BarLine in voice waar nodig). |
| S6 | **Geen Coria-eis** | Mag engraving-achtige encodes bevatten; hoeft niet Coria-playback-vriendelijk te zijn. |
| S7 | **Keten ok** | Gegenereerd via `mvsa → mxl → MuseScore` mag: na opslaan voldoet het bestand aan S1–S5 voor jullie workflow. |

**Normalize-target MSCZ → MSCZ:** herschrijf/opnieuw genereren naar deze
checklist (beperkt wat wij vastleggen; geen volledige MuseScore-spec).

## Verschillen bewust hangende houden

| Onderwerp | `.mxl` (Coria) | `.mscz` (partituur) |
| --------- | -------------- | ------------------- |
| Melisma-extend | eenvoudige `<extend/>` | mag start/continue/stop |
| Typografie / Style | weglaten | wel (MuseScore) |
| Blad-aanwijzing | rust zonder lyric | mag op blad zichtbaar blijven |
| Doel | afspelen / Coria | lezen / bewerken / PDF |

## Bestandsnaamgeving (conventie)

Traceerbaarheid van conversies — **niet verplicht** op elke `-o`.

| Regel | Voorbeeld |
| ----- | --------- |
| Bij voorkeur in `generated/`: `stem.brontype.doeltype` | `alleluia.mvsa.mxl`, `alleluia.mscz.mvsa`, `tropaar.vsa.mxl` |
| **Laatste** segment = echte extensie voor tools | `.mxl`, `.mvsa`, `.mscz`, `.mid` / `.midi` |
| CLI-default mag enkelvoudig blijven | `-o out.mxl` of `<stem>.mxl` |
| Geen fout als de naam “simpel” is | normalize/export falen niet op ontbrekende dubbele extensie |

Zie ook [mvsa-conversies](../plans/mvsa-conversions.md).
