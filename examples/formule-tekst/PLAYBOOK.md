# Playbook — VSA (+ template) → werkbank-`.mvsa`

Skelet voor chats en later CLI. Doel: **schets** die minder werk vraagt dan
vanaf scratch; geen kant-en-klare catalogusbron.

Analoog aan score→mvsa (`mscz mvsa` / `mxl mvsa`): bron eerst, doel daarna,
output met **concrete disclaimer** in het commentaar.

## CLI-syntax (afspraak)

Conventie **bron → doel**, zoals bij `mscz mvsa` en `mxl mvsa`:

```text
vsa mvsa [--template {template-id}] [-o OUT] {vsa-bestand}
```

| Onderdeel              | Betekenis                                                                 |
| ---------------------- | ------------------------------------------------------------------------- |
| `vsa`                  | Bronformaat: `.vsa` (melodie + tekst + frasen)                            |
| `mvsa`                 | Doel: werkbank-`.mvsa` (SATB-schets)                                      |
| `--template`           | Welke formule / library-template; zie [template-id](#template-id)         |
| (geen `--template`)    | **Default:** tropaar/kondak-formule **Hemelum** (niet Groningen)          |
| `-o OUT`               | Optioneel; anders sibling `<bronnaam>.mvsa` (zelfde patroon als import)   |
| `{vsa-bestand}`        | Pad naar één `.vsa`                                                       |

Voorbeelden (nog niet geïmplementeerd — vastgelegd als contract voor de CLI):

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa examples\formule-tekst\vsa-bestanden\tropaar-profeet-elia-toon-4.vsa
vsa mvsa --template hemelum-tropaar-toon-4 tropaar-nikolaas-van-myra-toon-4-hemelum.vsa
vsa mvsa --template groningen-tropaar-toon-4 lied.vsa -o generated\lied.schets.mvsa
```

**Nog niet in scope van dit playbook:** platte tekst / `.ftxt` → `.mvsa`.
Dat blijft een apart auteurspad; hoofdpad is **VSA + template**.

### template-id

Voorstel (invullen naarmate library groeit):

```text
{traditie}-{genre}-toon-{n}
```

| Deel        | Voorbeelden                                      |
| ----------- | ------------------------------------------------ |
| `traditie`  | `hemelum`, `znameni`, `kiev`, `groningen`, …     |
| `genre`     | `tropaar`, `kondak`, `stichier`, `prokimen`, …   |
| `toon`      | `1` … `8`                                        |

**Default (nu):** Hemelum tropaar/kondak toon 4.

| String                         | Betekenis                                                                 |
| ------------------------------ | ------------------------------------------------------------------------- |
| `tropaar-toon-4`               | Canonieke library-`id` (bestand in `library/tropaar-toon-4/`)             |
| `hemelum-tropaar-toon-4`       | Playbook-alias → zelfde template (voor CLI `--template`)                  |
| (geen `--template`)            | Zelfde default: Hemelum tropaar/kondak; toon uit VSA of dit toon-4-pad    |

Library:
[`docs/specification-vsa-templates/library/tropaar-toon-4/`](../../docs/specification-vsa-templates/library/tropaar-toon-4/).
Mensformule (pad 0): [`tropaar-toon-4/formules/`](tropaar-toon-4/formules/).
`laatste` heeft twee `of:`-paden (re / fa); formuleblad toont re-close.

**Niet:** Groningen als default. Groningen alleen met expliciet `--template`.

Tradities = **aparte** template-ids. Binnen één Hemelum-formule wél beperkte
`of:`-takken (alleen herhaalde, getelde cadensvarianten).

## Wat succes betekent

| Groen                                      | Rood / handwerk                                       |
| ------------------------------------------ | ----------------------------------------------------- |
| Mapping past op de gekozen template        | Pitch/frase buiten formule → harde fout of disclaimer |
| Output `.mvsa` met disclaimer-banner       | Stille “nearest path” naar SATB                       |
| Beheerder kan in MuseScore nabewerken      | Publiceren zonder checklist                           |

Zie disclaimer-sjabloon:
[`disclaimer-vsa-mvsa.sjabloon.txt`](disclaimer-vsa-mvsa.sjabloon.txt).

## Chat-proces (één mijlpaal per run)

1. Kies **één** cel: genre × traditie × toon (bijv. tropaar × hemelum × 4).
2. Verzamel catalogus- / corpus-`.vsa` die **bij die formule** horen.
3. (a) Template scherp maken of bijstellen (`template.yaml` / `.formule.mvsa`).
4. (b) Converter-pad toetsen: VSA → schets-`.mvsa` + disclaimer.
5. Lessen hieronder bijwerken (valkuilen / wel-doen) — **vóór** de volgende cel.

Formuleer goedkoop: *«alleen tropaar hemelum toon 4 — playbook + 1 voorbeeld;
geen andere tonen»*.

## Checklist vóór mapping (redactie)

- [ ] `@do` / mode kloppen met de template
- [ ] Frasegrenzen expliciet (`*` of geaccepteerde normalisatie)
- [ ] Speelplan / frase-telling past bij de formule (incl. `laatste`)
- [ ] Geen stille toonsoortwissel midden in het stuk
- [ ] Juiste `--template` (of bewust default Hemelum)

## Valkuilen (levend — bijwerken na chats)

| Les         | Wel                                                            | Niet                                               |
| ----------- | -------------------------------------------------------------- | -------------------------------------------------- |
| Invoer      | VSA + template als hoofdpad                                    | Platte tekst als migratiebrug voor bestaand corpus |
| Cadens      | `laatste` `of:` re-close + fa-close in Hemelum toon-4-template | Eén pad forceren en de rest stil “dichtstbij”      |
| Optionals   | `a?` / ankers uit klemtoon; recite ≠ open-slot print           | `[open]` als synoniem voor recite 1-n-1            |
| Formulebron | Eén uitvoerbare bron tot `.formule.mvsa` compileert            | YAML én `.formule.mvsa` als twee waarheden         |
| Scope chat  | Eén genre×traditie×toon                                        | Alle tonen/varianten in één run                    |
| Output      | Schets + disclaimer; unieke `@blok` + `&`-melisma              | Catalogus-commit zonder check; bron-VSA overschrijven |
| Emitter L   | Melisma-vervolg als `li_&_` op vorige lettergreep              | Losse `-_` / `__` (telt niet als L-slot)              |

Uit Fase A/B (toon 4): zie
[`vsa-bestanden/FASE-A-B-RAPPORT-VSA-TEMPLATE.md`](vsa-bestanden/FASE-A-B-RAPPORT-VSA-TEMPLATE.md).

## Disclaimer (waar en hoe)

- Zelfde geest als `IMPORT_SKETCH_WARNING_BANNER` in `src/vsa/mvsa_import.py`
  (score→mvsa).
- Na een herkomstregel (`# From-vsa: …` / `# Template: …`) de ASCII-banner
  uit [`disclaimer-vsa-mvsa.sjabloon.txt`](disclaimer-vsa-mvsa.sjabloon.txt).
- Banner noemt **concrete** controlpunten (frasen, S↔formule, A/T/B, ankers,
  metadata) — geen vage “controleer alles”.

## Open (invullen bij implementatie)

| Onderwerp                         | Status / besluit                                         |
| --------------------------------- | -------------------------------------------------------- |
| Exacte default-`template-id`      | `tropaar-toon-4`; alias `hemelum-tropaar-toon-4`         |
| Alias `hemelum` → toon uit VSA?   | TBD (nu alleen toon 4 vastgelegd)                        |
| Kondak = zelfde id als tropaar?   | Ja: `also_used_as: [kondak]` op `tropaar-toon-4`         |
| Exitcode bij mapping-fout         | Voorstel: non-zero + geen stille half-schets             |
| Man-pagina / formats-hub          | Bij echte CLI, zelfde ronde als code (`docs-sync`)       |

## Zie ook

- Werkmap: [`README.md`](README.md)
- Library tropaar toon 4: [`docs/specification-vsa-templates/library/tropaar-toon-4/`](../../docs/specification-vsa-templates/library/tropaar-toon-4/)
- Score→mvsa (banner-voorbeeld): [`docs/formats/mvsa.md`](../../docs/formats/mvsa.md#score-naar-mvsa)
- Conversiematrix: [`docs/plans/mvsa-conversions.md`](../../docs/plans/mvsa-conversions.md)
