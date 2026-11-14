# Syllabificatie (zing-deling in de bron)

**Status:** normatief contract (afspraak). `vsa validate` controleert de
canonieke syllable-dictionary (`VSA-SYLLABLE-DICT-MISMATCH` /
`VSA-SYLLABLE-DICT-UNKNOWN`, standaard **error**) en waarschuwt bij
ontbrekende soft `-` zonder dictionary-treffer
(`VSA-SYLLABIFY-MISSING-HYPHENS`; severity via `vsa.toml`).

**Contract-anker:** lettergreep = tekstpositie met minstens één noot
([canonical-checklists](canonical-checklists.md) **K2**, **L3**, **M10**).
Hyphen ≠ melisma (L3/L4).

## Antwoord eerst

In canonieke [`.vsa`](vsa.md)- en [`.mvsa`](mvsa.md)-bronnen hoort de
**zing-deling** zichtbaar in de tekst: zachte lettergreepstreepjes (`-`).
Die deling is redactioneel. Tooling mag helpen zetten (`vsa syllabify`),
maar mag die deling niet stil opnieuw verzinnen als stille waarheid voor
producten. Wat doorlopende woorden nodig heeft (zoektekst, sommige prints),
**haalt** zachte streepjes deterministisch weg.

## Soft `-` versus hard `=`

| Teken in de bron | Betekenis                                                   | Voorbeeld                                |
| ---------------- | ----------------------------------------------------------- | ---------------------------------------- |
| Soft `-`         | Zing-deling: grens tussen lettergrepen / notenposities (L3) | `eeu-wig`, `Va-der`                      |
| Hard `=`         | Orthografisch koppelteken (leesvorm met gewoon streepje)    | `mede=eeuwige` → weergave `mede-eeuwige` |

Binnen een scope `{…}` blijft `-` een [ELM](../specification/README.md)
(duur); daar hoort geen Pyphen-herschrijving.

**Scope-accolade = grens:** elke `{` / `}` is al een lettergreep- of
woordgrens. Zet **geen** soft `-` tussen een letter en een accolade, en
**niet** tussen twee scopes. Fout: `ver-{/&\heer}-{\lijkt}`. Goed:
`ver{/&\heer}{\lijkt}`. Hetzelfde voor `Chris{/tus}` (niet `Chris-{/tus}`)
en `{/stra_}{len_}` (niet `{/stra_}-{len_}`).

Handmatige soft `-` **binnen** platte tekst winnen: geen her-hyphenatie
van dat token.

## Wat de bron eist

1. Platte recite-woorden die uit meer dan één lettergreep bestaan, hebben
   soft `-` op de zing-grenzen (`eeu-wig`, niet `eeuwig`).
2. Hetzelfde geldt voor L-tekst in `.mvsa` (recite tussen haakjes, cadens
   met hyphen-keten): de zichtbare deling is de canonieke.
3. Scopes blijven de structurele zangposities; je syllabificeert niet de
   inhoud van `{…}` opnieuw. Soft `-` naast `{`/`}` hoort niet in de bron.

### Voorbeeld `.mvsa` (recite + cadens)

Klein demo-bestand met meerdere recite-runs
[`examples/mvsa/syllabificatie-recite-mini.mvsa`](../../examples/mvsa/syllabificatie-recite-mini.mvsa):

| L-fragment                      | Betekenis                                                           |
| ------------------------------- | ------------------------------------------------------------------- |
| `(Leer-lin-gen toon-de Gij Uw)` | Soft `-` **binnen** de recite = lettergrepen; spaties = woorden     |
| `(Gij werd ver-heer)-lijkt_`    | `)-` + `lijkt` = het woord loopt door **buiten** de recite (cadens) |
| `(zon-daars, Uw eeu-wig) Licht` | Recite eindigt; `Licht` is een nieuw woord (geen `)-`)              |

Catalogus-schets met dezelfde patronen (na `vsa mvsa`):
`bibliotheek/.../tropaar-transfiguratie-toon-7-hemelum.vsa.mvsa`
(bijv.
`C:\Git\orthodox-ronl\bibliotheek\content-source\catalogus\tropaar\transfiguratie-toon-7\hemelum\tropaar-transfiguratie-toon-7-hemelum.vsa.mvsa`).

**Schrijfhulp:** [`vsa syllabify`](../reference/cli/syllabify.md) voor
`.vsa`, [`mvsa syllabify`](../reference/cli/mvsa.md#mvsa-syllabify) voor
`.mvsa` (Pyphen `nl_NL`; cadens-expansie houdt L↔stem-sync). Controleer
altijd: orthografie ≠ liturgische zing-deling.

## Canonieke woordenlijst (zing-deling)

Elk lemma (letters zonder soft `-` en zonder hard `=`) heeft **hoogstens één**
canonieke hyphenvorm. Die lijst is de norm voor gezongen body-tekst (niet
frontmatter, comments, ids of `lyrics.txt`).

| Afspraak    | Inhoud                                                                              |
| ----------- | ----------------------------------------------------------------------------------- |
| Canon (org) | `bibliotheek/data/syllable_dictionary.nl.txt` (content-repo; commit/push daar)      |
| Config      | `vsa.toml` → `[syllabificatie] dictionary = "…"` (relatief t.o.v. die toml)         |
| CLI         | `--syllable-dictionary PAD` op `vsa`/`mvsa` `validate` / `syllabify`                |
| Env         | `VSA_SYLLABLE_DICTIONARY`                                                           |
| Auto        | `data/syllable_dictionary.nl.txt` in de werkmap, of sibling `bibliotheek/data/…`    |
| Loader      | `vsa.syllable_dictionary`                                                           |
| Vorm        | Eén hyphenvorm per regel (kleine letters); soft `-` en hard `=`; `#` = commentaar   |
| Volgorde    | Entries alfabetisch op **lemma**; TTY/append herschrijft de lijst gesorteerd        |
| Matching    | Lemma = letters zonder `-`/`=`, case-fold → unieke vorm                             |
| Onderhoud   | Wijziging in de content-repo, of interactief op TTY (schrijft naar het actieve pad) |

Voorrang: CLI → `vsa.toml` → env → auto-detect. Andere repo’s zetten hun
eigen lijst in hun `vsa.toml`. Zonder pad is de mapping leeg (geen stille
package-lijst in VSA-tooling).

Startset: catalogus-review plus handmatige correcties (o.a. `a-pos-tel`,
`eeu-wi-ge`, `me-de=eeu-wi-ge`, `o-ver-…`).

### Dictionary-controle (`validate` / `syllabify`)

`vsa validate` / `vsa syllabify` (alleen `.vsa` of Markdown-VSA-blokken) en
`mvsa validate` (alleen `.mvsa`) vergelijken **uitsluitend lyrics** met die
lijst: in VSA de gezongen body (platte tekst + scope-tekst); in MVSA alleen
**L-regels**. Geen frontmatter, geen `zoektekst`, geen `@title`/`@do`/andere
directives, geen S/A/T/B-regels, geen commentaar.

In VSA telt een **scopegrens** (tekst↔`{…}` of `{…}`↔`{…}` zonder spatie)
als zing-deling: de checker zet daar een virtueel soft `-` voor de
vergelijking met de lijst. Zo hoort `ver{/heer}{\lijkt}` bij `ver-heer-lijkt`
zonder dat er een soft `-` naast `{`/`}` in de bron staat.

Positie-meldingen en dictionary-vervangingen zoeken **alleen** in de
gezongen body (na strip van YAML-frontmatter inclusief `zoektekst`, en na
HTML/`#`-commentaar) — nooit in metadata.

`vsa validate` / `mvsa validate` vullen ontbrekende soft `-` automatisch bij
(zelfde logica als `vsa syllabify` / `mvsa syllabify`), schrijven het bestand
terug, en melden `VSA-SYLLABIFY-APPLIED` / `MVSA-SYLLABIFY-APPLIED`.
`zoektekst` blijft onaangeroerd.

| Code                         | Wanneer                                                                      | Standaard                                            |
| ---------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------- |
| `VSA-SYLLABLE-DICT-MISMATCH` | Lemma staat in de lijst, bronvorm wijkt af (bijv. `eeuwig` i.p.v. `eeu-wig`) | **error** (`.vsa`); op `.mvsa` voorlopig **warning** |
| `VSA-SYLLABLE-DICT-UNKNOWN`  | Lemma ontbreekt, én het woord heeft soft `-`/`=` óf Pyphen ziet breuken      | **error** (`.vsa`); op `.mvsa` voorlopig **warning** |

Op een **TTY** kun je findings meteen afhandelen. Bij batch (map of
meerdere bestanden) verschijnt **één keer per stuk** een regel
`--- <catalogus-id of bestandsstam> ---` vóór de vragen, zodat je ziet
welk zangstuk je corrigeert.

| Situatie                                                   | Enter (voorstel)                                                            | Andere keuzes                                                                                    |
| ---------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `MISMATCH` (bijv. `eeuwig` ↔ `eeu-wig`)                    | Vervang in de **body** (niet in `zoektekst`) naar de canonieke vorm         | `a` = huidige vorm als canon in de lijst; `s` = overslaan; of typ een andere vorm (lijst + body) |
| `UNKNOWN` met al streepjes (bijv. `eeu-wig-heids-waar-de`) | Voeg **die** vorm toe aan de lijst                                          | `s` = overslaan; of typ een andere vorm                                                          |
| `UNKNOWN` zonder streepjes                                 | Voeg Pyphen-/dictionary-voorstel toe                                        | `v` = vervang in bron én voeg toe; `s` = overslaan                                               |

In CI (geen TTY) blijven `MISMATCH` / `UNKNOWN` fouten tot bron of lijst
handmatig klopt. Hints noemen dezelfde keuzes.

`vsa syllabify` / `mvsa syllabify` hypheneren met Pyphen, maar als het
lemma al in de dictionary staat wint die vorm (inclusief
hoofdletteroverdracht van de bron). Bij `.mvsa` blijft de sync L↔stemmen
geldig (extra lettergrepen in cadens krijgen `-`-holds op de stemmen).
Na schrijven geldt dezelfde interactieve gate. Vervangingen en syllabify
raken **niet** het YAML-veld `zoektekst` — dat blijft platte tekst zonder
soft `-` (hard `=` → zichtbaar `-` via [zoektekst](zoektekst.md)).

Implementatie: `vsa.syllable_dict_check` + `vsa.syllable_dictionary`.

## Stappenplan (implementatie)

| Stap | Inhoud                                                              | Status                                     |
| ---- | ------------------------------------------------------------------- | ------------------------------------------ |
| 1    | Canonieke `syllable_dictionary.nl.txt` + correcties                 | gedaan                                     |
| 2    | Validate/syllabify: `MISMATCH` / `UNKNOWN` (+ TTY toevoegen)        | gedaan                                     |
| 3    | TTY: bron meteen corrigeren of vorm accepteren in de lijst          | gedaan                                     |
| 4    | Lijst in bibliotheek (of andere content-repo) + pad via config/CLI  | gedaan                                     |
| 5.1  | Pitch-fix steekproef-leaf (transfiguratie-toon-7-hemelum)           | gedaan (`vsa mvsa` OK; zie cadens `{/e_}`) |
| 5.1b | `mvsa validate` / `mvsa syllabify` (L-recite + sync-veilige cadens) | gedaan                                     |
| 5.2  | Dry-run syllabify+validate die leaf (zonder TTY-auto)               | open (CLI klaar; leaf-dry-run apart)       |
| 5.3  | (optioneel) Meer leafs / corpus                                     | open                                       |

## Uitzonderingslijst (bewust eenlettergrepig)

Validate mag waarschuwen of falen wanneer een plat token **geen** soft `-`
heeft, terwijl Pyphen (`nl_NL`) wél breekposities ziet (“lijkt
meerlettergrepig”), **en** het lemma niet in de canonieke woordenlijst
staat (dictionary-UNKNOWN dekt woorden die al streepjes hebben of daar
horen).

Soms moet dat woord in de zang **toch één lettergreep** blijven. Zulke
woorden staan op een canonieke uitzonderingslijst:

| Afspraak  | Inhoud                                                                                                                              |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Pad       | `src/vsa/data/monosyllable_exceptions.nl.txt`                                                                                       |
| Vorm      | Eén woord per regel; matching case-fold (kleine letters in het bestand); lege regels en regels die met `#` beginnen zijn commentaar |
| Onderhoud | Alleen via bewuste wijziging in de repo (PR); geen stille runtime-aanvulling                                                        |

**Melding bij waarschuwing/falen** noemt altijd beide herstelpaden, kort en
concreet, in deze geest:

> Woord `X` heeft geen lettergreepstreepje(s), maar lijkt meerlettergrepig
> (Pyphen: `X-y-z`). Doe één van beide:
>
> 1. Zet soft `-` in de bron op de juiste plekken, bijv. `X` → `X-y-z`
>    (zing-deling; ter hulp: eerst
>    `vsa syllabify pad\naar\bestand.vsa --dry-run`, daarna controleren en
>    `vsa syllabify pad\naar\bestand.vsa` zonder `--dry-run`, of handmatig
>    vastleggen).
> 2. Of: als het woord **één** lettergreep moet blijven, voeg het woord in
>    kleine letters toe als nieuwe regel in
>    `src/vsa/data/monosyllable_exceptions.nl.txt`, en draai validate
>    opnieuw.

Implementatie: `vsa.syllabify_validate` + `vsa.monosyllable_exceptions`;
aanroep vanuit `vsa validate` na geslaagde parse. Alleen **platte**
`TextNode`-tokens (niet de tekst binnen scopes).

## Strip versus vertrouwen per consument

| Consument                                         | Soft `-`                                                                                                       |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| MusicXML / audio / recite-noten (aantal posities) | **Vertrouw** de bron-deling; geen stille Pyphen als bron van waarheid                                          |
| SVG (VSA-blad) / zoektekst / `vsa text` / lyrics  | **Strip** soft `-`; hard `=` wordt zichtbaar `-`                                                               |
| MSCZ print / partituur-recite                     | Soft `-` / hyphen-glyphs **binnen** recite verborgen (R8); noot-aantal = bron-deling; brug `(…)-cadens` blijft |
| `vsa syllabify`                                   | Schrijfhulp op de bron; geen verplichte products-stap                                                          |

Zie ook [zoektekst.md](zoektekst.md) (niet-gesyllabiseerde platte tekst voor
editorzoeken).

## Products / audio

`vsa products` (MXL, score-ir-brug, mscz-via-mxl) en `vsa audio` uit `.vsa`
gebruiken **geen** stille Pyphen meer: dezelfde playback-export met
`syllabify=False` + Coria-finalize waar van toepassing. Los `vsa mxl`
syllabificeert alleen met expliciete `--syllabify`. Ongesplitste bronnen
geven dan te weinig recite-noten — gebruik validate-waarschuwing
`VSA-SYLLABIFY-MISSING-HYPHENS` en `vsa syllabify` als schrijfhulp.

## Zie ook

- CLI: [`vsa syllabify`](../reference/cli/syllabify.md)
- Contract-index: [contract-index.md](contract-index.md)
- Checklists L3/K2: [canonical-checklists.md](canonical-checklists.md),
  [mscz-leesbaarheid.md](mscz-leesbaarheid.md)
