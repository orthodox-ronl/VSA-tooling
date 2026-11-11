# Tropaar / kondak — toon 4 (Groningen)

**Traditie:** Groningen. **Ook voor kondak** toon 4
(`also_used_as: [kondak]`). Canonieke id: `tropaar-toon-4-groningen`.

Hemelum toon 4 blijft een **aparte** formule:
[`tropaar-toon-4-hemelum`](../tropaar-toon-4-hemelum/) (playbook-alias
`hemelum-tropaar-toon-4`). Nieuwe tradities = nieuwe library-map met
id `{traditie}-{genre}-toon-{n}` — zie [library README](../README.md).

**Frase 1 B-pad:** Groningen `/` → `re-1` (hold) → `la-2`; Hemelum `/2` →
`mi-1` → `re-1` → `la-2`. Dat verschil blijft — koorleden oefenen erop.
Tempo (`@tempo 180` voor tropaar/kondak) hoort in het stuk, niet in deze
formule.

| Veld              | Waarde                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Formule-bron      | [`template.yaml`](template.yaml) — **bewerk dit**                                            |
| Traditie / genres | Groningen; tropaar + kondak                                                                  |
| `laatste` cadens  | mi–re–mi (re-close), zoals in de Nicolaas-schets                                             |
| Formule-MSCZ/MXL  | [`template.mscz`](template.mscz) / [`template.mxl`](template.mxl) — afgeleid uit *deze* YAML |
| Status pitches    | `provisional`                                                                                |
| Mapping           | S=VSA, A/T/B=template ([mapping-vsa.md](../../mapping-vsa.md))                               |

## Bron

Afgeleid uit

`bibliotheek/…/_klaar_voor_acceptatie/tropaar-nikolaas-van-myra-toon-4-groningen.mvsa`

Vergelijk met de Hemelum-sibling `…-hemelum.mvsa` (B-pad in frase 1).

Mensformule (zonder lyrics), in de repo (niet op Pages):
`examples/formule-tekst/tropaar-toon-4-groningen/`
([GitHub](https://github.com/orthodox-ronl/VSA-tooling/tree/main/examples/formule-tekst/tropaar-toon-4-groningen)).

## Wat hoort in deze map

```text
tropaar-toon-4-groningen/
  template.yaml          ← canonieke formule (bewerk hier)
  template.mscz          ← afgeleid uit template.yaml (Groningen)
  template.mxl           ← afgeleid uit template.yaml (Groningen)
  README.md
  notes/                 ← later: mappinglessen, corpus
  examples/corpus/       ← later: .vsa + goedgekeurde .mvsa
```

Na elke YAML-wijziging:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python scripts\sync_library_templates.py tropaar-toon-4-groningen
python scripts\sync_library_templates.py --check tropaar-toon-4-groningen
```
