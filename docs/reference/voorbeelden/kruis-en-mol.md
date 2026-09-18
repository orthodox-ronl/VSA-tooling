# Kruis en mol

Wat een kruis (`#` / `+`) en een mol (`b` / `♭`) in [VSA](@) doen — met
concrete frasen die je lokaal kunt valideren en naar MusicXML kunt exporteren.

Normatieve regels:
[Interpretatie van EHMs](../../specification/semantics.md#interpretatie-van-ehms),
[Tot hoever werkt de halftoon?](../../specification/semantics.md#tot-hoever-werkt-de-halftoon-normatief).
Historische achtergrond:
[Relatie Liturgikon ↔ VSA](../../guides/liturgikon-notatie.md#relatie-tussen-de-liturgikon-notatie-en-vsa).

## Twee lagen (kort)

| Laag | Wat het bestuurt | Voorbeelden |
| ---- | ---------------- | ----------- |
| Diatonische cursor | laddergraad (do, re, mi, …) | `/`, `\`, `-`, `~`, `//`, … |
| Accidens | klinkende toon op de aankomstgraad | `#` / `+` / `♯` (kruis), `b` / `♭` (mol) |

De halftoon-prefix staat **vóór** de basisbeweging en wijzigt alleen de
klinkende aankomsttoon. De prefix schuift de cursor niet chromatisch mee.

## Tot hoever werkt de halftoon?

In **klassieke muzieknotatie** geldt een kruis of mol tot de **volgende
maatstreep**, of tot een **herstelteken** / nieuw voorteken op dezelfde
nootletter. Alle latere noten van die letter in dezelfde maat blijven
gewijzigd.

In **[VSA](@)** is de reikwijdte **korter én anders**:

| Regel | Klassieke notatie | [VSA](@) |
| ----- | ----------------- | -------- |
| Tot wanneer? | maatstreep of ♮ / nieuw voorteken | tot de **volgende ladderstap** (`/`, `\`, …) zonder nieuwe prefix |
| Zelfde toon erna (`-`, `~`, recite) | blijft gewijzigd (binnen de maat) | blijft gewijzigd (**ook over een maatstreep**) |
| Terug naar dezelfde nootletter via andere tonen | blijft gewijzigd tot maatstreep/♮ | ladderstap zonder prefix → **natuurlijke** laddertoon |
| Maatstreep alleen | beëindigt het voorteken | beëindigt het VSA-accidens **niet** |

### Voorbeeld A — stopt bij de volgende ladderstap

```text
[:] {#-Cis}{/Re}{\Do} [:]
```

| Lettergreep | Klinkend (do=C4) | Waarom |
| ----------- | ---------------- | ------ |
| Cis | C♯ | `#-` zet kruis op do |
| Re | D | `/` = ladderstap → natuurlijke re |
| Do | C | `\` = ladderstap → **natuurlijke** do |

In klassieke notatie zou die laatste C in dezelfde maat nog C♯ zijn, tenzij
er een herstelteken staat. [VSA](@) heeft geen aparte ♮-prefix nodig: de
ladderstap zonder prefix volstaat. MusicXML-export zet wél een zichtbaar
`natural` op Do, zodat de partituur dezelfde reeks toont.

### Voorbeeld B — blijft op zelfde-toon, ook over een maatstreep

```text
[:] {#-Cis}{-nog} // {-verder} [:]
```

| Lettergreep | Klinkend | Waarom |
| ----------- | -------- | ------ |
| Cis | C♯ | `#-` |
| nog | C♯ | `-` = zelfde toon |
| (maatstreep `//`) | — | beëindigt het VSA-accidens **niet** |
| verder | C♯ | `-` na de maatstreep houdt nog steeds Cis |

In klassieke notatie zou `verder` zonder nieuw kruis meestal natuurlijke C
zijn. In [VSA](@) blijft de klinkende toon chromatisch tot er een
ladderstap zonder prefix komt.

### Voorbeeld C — na maatstreep natuurlijk door een ladderstap

```text
[:] {#-Cis} // {/Re} [:]
```

Hier is Re natuurlijk (D), niet omdat de maatstreep het kruis “wiste”, maar
omdat `/` een ladderstap zonder prefix is.

## Invoer (cursor vs. klinktoon)

[Fixture](@): `examples/docs-walkthroughs/halftoon-accidens-cursor.vsa`

```text
[:] {+\neer}{/terug_} op do. [:]

[:] {b/om}{-hoog_} op re. [/:]
```

| Frase | Cursor | Klinkende tonen | Waarom |
| ----- | ------ | --------------- | ------ |
| `{+\neer}{/terug}` | do → ti → do | B♯, daarna C | `+` = kruis op ti; `/` herstelt de **natuurlijke** do |
| `{b/om}{-hoog}` | do → re → re | D♭, daarna D♭ | mol op re; `-` houdt dezelfde klinktoon (inclusief mol) |

Gregos-stijl — zelfde-toon houdt het kruis vast tot de ladderstap:

```text
[/:] {+\go}{ri}{/os} [/:]
```

klinkt als D → C♯ → C♯ → D. De lettergreep `ri` heeft geen `#-` nodig; `os`
is weer natuurlijk omdat `/` een ladderstap is.

## Geen aparte herstelteken-prefix

Het Liturgikon tekent `+` / `♭` soms als herstellingsteken op het blad.
[VSA](@) heeft daar geen aparte glyph voor. “Herstel” naar de natuurlijke
laddertoon = ladderstap **zonder** nieuwe halftoon-prefix (zie voorbeeld A).

## Commando’s

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa validate examples\docs-walkthroughs\halftoon-accidens-cursor.vsa
vsa musicxml examples\docs-walkthroughs\halftoon-accidens-cursor.vsa generated\halftoon-accidens.musicxml
```

Meer combinaties:
[Halftoon-prefix combinaties (voorbeelden)](../../specification/semantics.md#halftoon-prefix-combinaties-voorbeelden).
