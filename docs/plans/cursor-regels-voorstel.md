# Voorstel: Cursor-regels en -rechten opschonen

Status: **voorstel** (2026-11-16), niet normatief. Er is niets in `.cursor` of
in `AGENTS.md` gewijzigd. Dit bestand beschrijft alleen wat gewijzigd kan
worden, zodat jij per punt kunt beslissen.

Aanleiding: bij het nalopen van `AGENTS.md`, `AI-INSTRUCTIONS.md`,
`.cursor/permissions.json` en de 13 bestanden in `.cursor/rules` vielen vijf
dingen op. Ze staan hieronder van klein en veilig naar groter.

## 1. Twee regels hebben geen frontmatter

**Bevinding:** `cli-entrypoints-mvsa.mdc` en `cli-input-bestand-of-map.mdc`
beginnen direct met een kop. Alle andere regels beginnen met een
frontmatter-blok met `description` en `alwaysApply`. Cursor laadt een regel
zonder frontmatter waarschijnlijk niet automatisch; dat is niet getest.
`AGENTS.md` noemt `cli-input-bestand-of-map.mdc` wel als handhaving.

**Voorstel:** zet bovenaan `cli-entrypoints-mvsa.mdc`:

```text
---
description: CLI-entrypoints; nooit `vsa mvsa`, elk brontype heeft een eigen commando
globs: src/vsa/cli*.py,docs/reference/cli/**/*.md,docs/guides/*.md
alwaysApply: false
---
```

en bovenaan `cli-input-bestand-of-map.mdc`:

```text
---
description: Gedeeld CLI-contract G1-G8 bij nieuwe of gewijzigde CLI-handlers
globs: src/vsa/cli*.py,docs/reference/cli/**/*.md
alwaysApply: false
---
```

**Controle:** open daarna een nieuwe chat in Cursor, bewerk een bestand in
`src/vsa/cli.py` en vraag welke regels actief zijn.

## 2. `permissions.json` noemt dingen die niet meer bestaan

**Bevinding:** het bestand verwijst naar `examples\hugo-demo` en naar
`scripts\sync_bron_zondagen.py`. Geen van beide bestaat in de repo; de
Hugo-demo staat nu in de aparte repo `VSA-demo`. `scripts\test.cmd` en
`scripts\ci.cmd` bestaan wel.

**Voorstel:** vervang de inhoud door het volgende. De laatste regel is
optioneel; hij volgt de afspraak in `AGENTS.md` dat commits alleen op verzoek
gemaakt worden.

```json
{
  "autoRun": {
    "allow_instructions": [
      "Auto-run VSA-tooling CI fixes: edit .github/workflows, run pytest, vsa validate, vsa build-markdown, scripts\\test.cmd and scripts\\ci.cmd when fixing workflows or tests.",
      "Auto-run routine file edits in src/, tests/, scripts/, docs/, and .github/ for tasks the user requested."
    ],
    "block_instructions": [
      "Block git commit and git push unless the user explicitly asks for it in the current message."
    ]
  }
}
```

## 3. De regeltabel in `AGENTS.md` mist vier regels

**Bevinding:** de tabel "Cursor-regels" noemt 9 van de 13 regels. Er ontbreken
`cost-control.mdc`, `cli-entrypoints-mvsa.mdc`, `cli-input-bestand-of-map.mdc`
en `kale-muziek-svg-uitgaven.mdc`.

**Voorstel:** voeg deze vier rijen toe aan de tabel en lijn de kolommen uit
(regel `markdown-table-layout.mdc`):

```text
| `cost-control.mdc`                    | Alleen Composer of Grok; stop vóór dure scope                 |
| `cli-entrypoints-mvsa.mdc`            | Nooit `vsa mvsa`; elk brontype heeft een eigen commando       |
| `cli-input-bestand-of-map.mdc`        | Gedeeld CLI-contract G1-G8 voor CLI-handlers                  |
| `kale-muziek-svg-uitgaven.mdc`        | Kale SVG, scherm versus blad, open fase 3                     |
```

## 4. Veel regels zijn bij elke chat geladen

**Bevinding:** negen regels staan op `alwaysApply: true`, samen circa 16 KB,
plus `AGENTS.md` met circa 12 KB. Dat is context bij elke chat, ook bij een
korte vraag. Daarnaast overlapt `canonieke-bestanden.mdc` met de
contract-index: het "verplichte proces" voor nieuwe of gewijzigde regels staat
volledig in `docs/formats/contract-index.md`, onder het kopje "Nieuwe regel →
contracten → naleving".

**Voorstel, in twee stappen:**

1. Meet eerst hoeveel context een lege chat in Cursor al gebruikt. Pas als dat
   zwaar is, ga je naar stap 2.
2. Kort `canonieke-bestanden.mdc` in tot een verwijzing naar de contract-index,
   en zet `documentatie-duidelijkheid.mdc` en `markdown-table-layout.mdc` op
   `globs: docs/**/*.md` met `alwaysApply: false`.

**Risico:** een chat zonder geopend documentatiebestand krijgt die regels dan
niet. Daarom pas na meting, en niet in dezelfde ronde als punt 1 tot en met 3.

## 5. `AI-INSTRUCTIONS.md` heeft een brede naam voor een smalle taak

**Bevinding:** het bestand gaat alleen over wijzigingen aan de VSA-specificatie
(Wijzigingsanalyse, breaking changes). De naam doet denken aan algemene
AI-regels, maar die staan in `AGENTS.md`. `CONTRIBUTING.md` verwijst één keer
naar het bestand.

**Voorstel:** voeg onder de eerste kop één zin toe: "Dit document geldt alleen
voor wijzigingen aan de VSA-specificatie. Algemene regels voor
AI-assistenten staan in `AGENTS.md`." Hernoemen is niet nodig.

## Volgorde

Eerst punt 1, 2, 3 en 5: klein en veilig, elk in een eigen commit. Punt 4 komt
pas na meting. Geen enkel punt wordt uitgevoerd zonder jouw OK.

## Wat in dit voorstel ontbreekt

De regels die je in Cursor zelf hebt ingesteld (Settings) staan niet in de repo
en zijn niet bekeken. De regels van `bibliotheek` (10 bestanden) en `bron`
(2 bestanden) zijn niet in detail beoordeeld.
