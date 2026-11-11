# `vsa mvsa`

Zet een **`.vsa`** om naar een SATB-**schets-`.mvsa`** via een
library-formule (VSA-melodie + template-stemmen). Contract:
[vsa-mvsa-contract.md](../../specification-vsa-templates/vsa-mvsa-contract.md)
(T1–T7). Lessen / checklist nieuwe tonen:
[conversion-lessons.md](../../specification-vsa-templates/conversion-lessons.md).

## Samenvatting

```text
vsa mvsa [--template ID] [-o OUT] [--melody S|A|T|B] [--tempo N] bestand.vsa
vsa mvsa --list-templates
```

| Onderdeel          | Betekenis                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| `bestand.vsa`      | Bron: melodie + tekst + frasen; frontmatter met **`soort`** en **`toon`** (T1)                     |
| `--template`       | Library-id of alias; zonder vlag: keuze op `soort`+`toon` (T1); ontbrekend/ambigu → fout           |
| `-o OUT`           | Uitvoerpad; default sibling `<bron>.mvsa`; bij hergeneratie telt bestaande MVSA-`template`         |
| `--melody`         | Melodiestem (T2); default `S`                                                                      |
| `--tempo`          | BPM in de MVSA; default **180** (tropaar/kondak); VSA-frontmatter negeert de converter             |
| `--list-templates` | Toon ids onder de library-map                                                                      |

## Uitvoer-vorm (T6)

De schets-MVSA volgt de gekuiste klaar-vorm (geen speelplan, geen `@blok`):

1. **Frontmatter** — nuttige VSA-catalogusvelden in vaste volgorde: `titel`,
   `taal`, `soort`, `toon`, `template` (+ eventueel `template_opgegeven`),
   `partituur`, `bron`, `gelegenheid`, `zoektekst`, …. Geen `do` / `mode` /
   `tempo` in YAML.
2. **Commentaar** — oorspronkelijke VSA (handig bij ELM-foutzoeken); daarna
   bronpad, template-id en notatie-regel.
3. **Waarschuwingen** — algemene schets-banner plus eventuele
   `# WAARSCHUWING:`-regels (T6).
4. **`@`-kop** — `@title`; daarna `@do`, `@mode`, `@tempo` (standaard 180)
   direct boven `@oct`.
5. **Systemen** — L + SATB per frase. Geen `@speelplan` en geen `@blok`.
6. **Secties** — `@sectie cyclus-1` (eerste cycle), `@sectie herhaling`
   (midden), `@sectie laatste` (slotfrase). Bij **toon 3** geen drie
   secties (zoals in de acceptatie-MVSA’s).

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa --list-templates
vsa mvsa docs\specification-vsa-templates\library\tropaar-toon-4-hemelum\examples\corpus\T4-06-profeet-elia.vsa
vsa mvsa lied.vsa --template tropaar-toon-4-groningen -o generated\lied.schets.mvsa
vsa mvsa lied.vsa --template kondak-toon-1-groningen
vsa mvsa lied.vsa --template tropaar-toon-2-groningen
vsa mvsa lied.vsa --template kondak-toon-5-groningen
```

Zonder `--template` zoekt de CLI formules bij `soort`+`toon`. Bestaan er
meerdere (Hemelum én Groningen), dan: bestaande `.mvsa` op het
uitvoerpad hergebruikt diens `template_opgegeven`/`template`, of de bron
uit het leaf-pad; anders moet je `--template` geven. Geen stille default.

Past de gekozen formule niet (hoogte-/mappingfout), dan blijft dat een
fout. Als een **andere** formule voor dezelfde soort en toon wél past,
staat in de hint welke dat is, plus een regel om opnieuw te proberen met
`--template` (T4).

Na een geslaagde schets: controle in MuseScore / oor; optioneel
`mvsa mxl` voor Coria-playback.

## Template-ids

Library:
[`docs/specification-vsa-templates/library/`](../../specification-vsa-templates/library/README.md).

| Voorbeeld-id               | Opmerking                                        |
| -------------------------- | ------------------------------------------------ |
| `tropaar-toon-4-hemelum`   | Hemelum; alias `hemelum-tropaar-toon-4`          |
| `tropaar-toon-4-groningen` | Groningen toon 4 (eigen B-pad frase 1)           |
| `kondak-toon-1-groningen`  | Groningen toon 1 (ook tropaar via plans)         |
| `tropaar-toon-2-groningen` | `same_as` → `kondak-toon-2-groningen`            |
| `tropaar-toon-5-groningen` | `same_as` → `kondak-toon-5-groningen`            |
| `tropaar-toon-6-groningen` | `same_as` → `kondak-toon-6-groningen`            |
| `tropaar-toon-8-groningen` | `same_as` → `kondak-toon-8-groningen`            |

Nieuwe formules: nieuwe map + YAML; de CLI vindt ze via
`--list-templates` zonder codewijziging (behalve optionele alias in
`library/aliases.yaml` / `template_library.template_aliases()`).

## Schrijfoctaven

Emit zet `@oct` uit de template-`voice_oct` (vaak `S=0 A=0 T=-1 B=-1`,
Groningen-kondak vaak `A=-1`). De alt op do=F4 met `A=0` wordt als `f`
geschreven (niet `f+`), zodat Coria-`.mxl` F4 speelt, niet F5.

## Zie ook

- Playbook (repo, niet op Pages):
  `examples/formule-tekst/PLAYBOOK.md`
  ([GitHub](https://github.com/orthodox-ronl/VSA-tooling/blob/main/examples/formule-tekst/PLAYBOOK.md))
- `mvsa mxl` (playback): [mvsa.md](mvsa.md#mvsa-mxl)
- `vsa template validate`
