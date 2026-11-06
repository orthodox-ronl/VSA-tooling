# Formule + tekst → partituur (herstart)

Werkmap voor een **nieuwe** kijk op formulematige stukken (eerst tropaar /
kondak toon 4).

## Uitgangspunt

| Rol           | Bron                         | Inhoud                                     |
| ------------- | ---------------------------- | ------------------------------------------ |
| **Formule**   | herbruikbaar, per genre×toon | de **muziek** (SATB, ankers, optionals, …) |
| **Tekst**     | per zangstuk                 | **lettergrepen + klemtoon** (geen melodie) |
| **Instantie** | formule + één tekst          | uitgewerkte partituur (later: Score-IR)    |

Oude aanpak (VSA-melodie + template-A/T/B): zie [`.archief/`](.archief/README.md).

## Score-IR (IR)

**IR** = tussenmodel. **Score-IR** = JSON van de uitgewerkte partituur voor
scherm/CoriB — leesbaar in VS Code, niet bedoeld om handmatig te schrijven.
Zie [`docs/formats/score-ir.md`](../../docs/formats/score-ir.md).

## Formule-notatie (keuze in deze map)

| Formaat                       | Rol                                      |
| ----------------------------- | ---------------------------------------- |
| `.formule.mvsa`               | **Wel** — canonieke formule-syntax       |
| YAML-formule                  | **Niet** — te onleesbaar om te editen    |
| Score-IR                      | Alleen **uitvoer** van een instantie     |

Formule hergebruikt MVSA/VSA (`@do`, `@oct`, `@blok`, `@speelplan`, a–g, EHM).
Extra: geen L; `a?`; `@e.st.`/`@l.st.`; ELM op de stem. Zie
[`tropaar-toon-4/formules/README.md`](tropaar-toon-4/formules/README.md).
Corpus Fase A: [`vsa-bestanden/`](vsa-bestanden/).

## Mapstructuur

```text
formule-tekst/
  README.md
  .archief/                 ← eerdere VSA+template-aanpak (+ verworpen YAML)
  tropaar-toon-4/
    tekst/                  ← .ftxt
    formules/               ← .formule.mvsa
    vsa-bestanden/          ← tropaar/kondak bronnen (Fase A)
    instanties/
    lastig/
```

## Conventie `.ftxt`

| Teken        | Betekenis                                                                 |
| ------------ | ------------------------------------------------------------------------- |
| `-`          | lettergreepgrens binnen een woord (`zacht-moe'-dig-heid'`)                |
| `'`          | klemtoon op de lettergreep erdirect vóór (`Re'gel`)                       |
| `*` of `/`   | einde van een tekstfrase → volgende formuleblok volgens `@speelplan`      |
| `**` of `//` | einde herhaling: deze frase is de **laatste**; daarna blok `laatste`      |
| `@…`         | metadata (`@title`, `@formule`, …)                                        |

Spaties scheiden woorden. Geen toonhoogte, geen ELM, geen `{/…}`.

Voorbeeld speelplan `|:` f1, f2 `:|` laatste: frasen vóór `**`/`//` vullen
cyclisch `f1`, `f2`, …; de frase mét `**`/`//` gaat naar `laatste` (ook als
je technisch nét na een `f1` zit). `**` is voor de beheerder dus handig,
zeker bij tekst op één regel om papier te sparen.

### Zijn dit alle tekens?

Voor **tropaar/kondak-achtige** formules met ankers uit klemtoon: dit is de
kernset. Waarschijnlijk later nog nodig (niet in de voorbeelden gezet):

| Mogelijk later                         | Waarom                                               |
| -------------------------------------- | ---------------------------------------------------- |
| commentaar / bronregel (`#` of `//`?)  | redactioneel; botst nu met `//` als frase-einde      |
| expliciet anker in tekst               | alleen als klemtoon alleen `e.st.`/`l.st.` niet dekt |
| meerstemmige of parallelle tekstlaag   | andere taal / hulptekst                              |
| “deze frase breekt de formule”         | uitzondering → vrije `.mvsa` i.p.v. formule          |

**Klemtoon `'` hoort er wél bij** — zonder klemtoon geen `e.st.`/`l.st.` uit
de tekst. Lettergreepstreepjes en frase-/slottekens alleen zijn niet genoeg.

Conflict om te beslissen: `//` als **slotfrase** vs `//` als **commentaar**
(zoals in veel bestanden). Alternatief: slot alleen `**`, commentaar `#`.

## Playbook + CLI-afspraak

Gepland (nog niet geïmplementeerd):

```text
vsa mvsa [--template {template-id}] {vsa-bestand}
```

Default-template: tropaar/kondak **Hemelum** (niet Groningen). Zie
[`PLAYBOOK.md`](PLAYBOOK.md) en
[`disclaimer-vsa-mvsa.sjabloon.txt`](disclaimer-vsa-mvsa.sjabloon.txt).

## Status

Werkmap + playbook-skelet. CLI `vsa mvsa` nog niet gebouwd. Doel: notatie
en proces scherp vóór tools.
