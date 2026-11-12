# MVSA → VSA (E-reeks)

**Contract-id:** E1–E6.  
Canonieke hub voor `mvsa vsa` (eenstemmige extractie uit `.mvsa`).  
Overzicht: [contract-index](contract-index.md). Spiegel (andere richting):
[vsa-mvsa-contract](../specification-vsa-templates/vsa-mvsa-contract.md) (T1–T7).

## Waartoe

Uit een meerstemmige `.mvsa` één (of later meer) **eenstemmige** `.vsa`
afleiden: tekst + relatieve hoogtemarkers van één stem. Dat is een
**product** naast de canonieke `.mvsa`, geen tweede canonieke notatiebron
(zie bibliotheek `catalogus-notatiebron`).

## Checklist

| Id  | Regel |
| --- | ----- |
| **E1** | Bron = `.mvsa` (straat `mvsa`). Invoer: bestand of map via [`input-pad`](../reference/cli/input-pad.md) / `collect_cli_sources`. Map: alleen kale bron-`.mvsa` (geen geneste `*.mscz.mvsa` e.d.). Expliciet bestandspad mag genest zijn (bijv. `lied.mscz.mvsa`). |
| **E2** | Uitvoernaam: **zonder** `--voice` of met **één** `--voice x` → altijd sibling `{bronnaam}.vsa` (bijv. `lied.mvsa.vsa`). Alleen bij `--voice all`: per stem `{bronnaam}.{stem}.vsa` met stem-id **lowercase** (ook S → `lied.mvsa.s.vsa`; A → `lied.mvsa.a.vsa`). `-o` alleen bij precies één bron én één uitvoerbestand (niet bij `all`). |
| **E3** | Zonder `--voice`: stem **S**. Met `--voice {id}`: die stem (case-insensitive match op stem-id in het bestand); uitvoer blijft `.mvsa.vsa` (E2). `--voice all`: alle niet-lyrics-stemmen, elk in `.mvsa.{stem}.vsa`. Ontbrekende stem → fout. |
| **E4** | Elke MVSA-**maat** wordt één VSA-**strofe**; frasescheiding `*` tussen maten (laatste maat sluit met `[:]`). Hoogten: openingsmarker `[…:]` t.o.v. schrijf-do (`@do` + `@oct` voor die stem), daarna EHM’s t.o.v. vorige toon. Melisma (`&` op L/stem) → `&` binnen één VSA-scope; duur-ELMs (`_` / `.` / `-`) in de lyric, `~` weglaten. Zelfde toon zonder melisma → **kale tekst** (geen `{-…}`). |
| **E5** | Frontmatter van de `.vsa` vermeldt **herkomst**: minstens `herkomst.generator: mvsa-vsa`, `herkomst.bron` (bestandsnaam), `herkomst.stem` (stem-id). Nuttige MVSA-velden (`titel`, `taal`, `soort`, `toon`, …) en afspeel (`do` / `mode` / `tempo` uit sticky `@`) mogen mee, zonder lege/`null`-sleutels. **`zoektekst`**: opnieuw afgeleid (`zoektekst: |-`, één frase per regel, geen lege regels) — bij voorkeur uit de VSA-body (zelfde `*`-strofen); anders L-extractie uit de MVSA. Geen kopie van een oude YAML-`zoektekst`. Zie [zoektekst.md](zoektekst.md). VSA-body zelf ook zonder lege regels. |
| **E6** | `mvsa products` schrijft key `vsa` → sibling `{bron}.mvsa.vsa` (default-stem S). Losse CLI: `mvsa vsa`. Geen stille overwrite van een handmatige canonieke `.vsa` in dezelfde leaf — dit bestand is altijd de **afgeleide** `.mvsa.vsa`. |

## CLI

```text
mvsa vsa PATH [-o OUT] [--voice {id}|all]
```

Man-pagina: [`mvsa` — subcommando vsa](../reference/cli/mvsa.md#mvsa-vsa).

## Niet in deze hub

- Formule-mapping VSA→MVSA (T1–T7).
- Canonieke catalogus-`.vsa` handmatig naast `.mvsa` zetten (bibliotheek
  notatiebron-regel).
