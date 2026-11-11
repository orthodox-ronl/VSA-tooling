# Werkwijze: YAML-template maken

Taakbeschrijving voor het **opstellen of uitbreiden** van een
[vsa-template](vsa-template@) in de library. Doel: een geldige `template.yaml`
die je in MuseScore kunt controleren via het formuleblad — zonder alles tegelijk
te hoeven bedenken.

Normatieve details: [syntax](syntax.md), [semantiek](semantics.md),
[validatie](validation.md), [mapping](mapping-vsa.md).
Mapafspraken: [library/README.md](library/README.md).

## Wat is de bron?

| Artefact             | Rol                                              |
| -------------------- | ------------------------------------------------ |
| `template.yaml`      | **Canonieke formule** — hier bewerk je           |
| Toonboek / onderzoek | Pitches en frase-indeling                        |
| `template.mscz`      | Afgeleid formuleblad (MuseScore-controle)        |
| Corpus-`.vsa`        | Testen van **instanties**, niet om YAML te maken |

VSA-voorbeelden maken het template **niet**. Ze toetsen of de mapping (S uit
VSA, A/T/B uit template) klopt nadat de YAML staat.

## Aanbevolen aanpak: mal + drie lagen

### 1. Start van een mal

Kopieer een bestaande formulemap (bijv.
[`library/tropaar-toon-4-hemelum/`](library/tropaar-toon-4-hemelum/README.md)) naar
`library/<genre>-toon-<n>/`. Pas daarna `id`, `title`, `do`, `mode` en de
frases aan. Liever knippen in een werkend bestand dan vanaf nul de metamodel-boom
typen.

Optioneel: koppel in je editor het schema
[`schema/vsa-template.schema.json`](schema/vsa-template.schema.json) aan
`template.yaml` voor rode krullen tijdens het typen.

### 2. Structuur (zonder echte pitches)

Zet eerst vast:

- `cycle` / `final` (of `sequence` / `text_mapping`);
- frase-ids (`"1"`, `"2"`, `"laatste"`, …);
- per event: `role`, `duration` (ELM), eventueel `anchor` / `optional`.

Pitches mogen tijdelijk overal dezelfde graad zijn (bijv. `do`) — alleen om
schema + validate groen te krijgen.

### 3. Pitches

Vul S/A/T/B per event tegen het bronblad. Status `provisional` in de map-README
zolang de audit niet klaar is.

### 4. Keuzes (`of`) — pas als nodig

Pas daarna `of`-groepen toe (alternatieven op een plek in de eventreeks). Het
formuleblad toont per groep **alternatief 0** (eerste tak). Andere takken
controleer je met een VSA die die hoogten kiest (instance), of tijdelijk door
die tak als eerste te zetten.

Details: [mapping-vsa.md](mapping-vsa.md) (`of`-alternatieven).

## Checklist per iteratie

Na elke laag:

1. `vsa template validate` op het bestand of de library-map.
2. Formuleblad regenereren en in MuseScore openen.
3. Klopt het blad niet → YAML nog niet klaar (ook als validate groen is).

## Commando's (Windows)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
call .venv\Scripts\activate
vsa template validate docs\specification-vsa-templates\library\tropaar-toon-4-hemelum\template.yaml
python scripts\render_tropaar_toon4_corpus.py --template
```

Andere formules: zelfde validate; render via
`python scripts\render_vsa_template_musicxml.py docs\specification-vsa-templates\library\<map>\template.yaml`
of `--all` waar van toepassing. Corpus-instanties (pas na stabiele YAML):

```cmd
python scripts\render_tropaar_toon4_corpus.py
python scripts\render_tropaar_toon4_corpus.py --pdf
```

## Wat je níet hoeft te doen (nu)

- Geen GUI of “VSA → YAML afleiden”.
- Geen ossia / alle `of`-takken tegelijk op het formuleblad (alleen alternatief 0).
- Geen geneste `of` (verboden).

## Gerelateerd

| Document                                                | Wanneer                      |
| ------------------------------------------------------- | ---------------------------- |
| [library/README.md](library/README.md)                  | Mapstructuur, wat in git     |
| [rendering-pitfalls.md](rendering-pitfalls.md)          | Layout / MuseScore-valkuilen |
| [CLI: `vsa template validate`](../specification/cli.md) | Validatie-commando           |
| [open-points.md](open-points.md)                        | Open vervolgstappen          |
