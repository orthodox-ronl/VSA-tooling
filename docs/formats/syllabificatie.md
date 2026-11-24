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

**Elke scope = één lettergreep:** `vsa syllabify` herverdeelt letters
zodat de tekst ín `{…}` precies één zing-lettergreep is. Restletters
komen in platte tekst ernaast (geen soft `-` bij de accolade). Voorbeeld:
`{/sche_}pping` → `{/schep_}ping`; `{/Adam}` → `{/A}dam`. Niet:
`{/sche_}p-ping` of `{/schep_}-ping`.

Handmatige soft `-` **binnen** platte tekst winnen: geen her-hyphenatie
van dat token.

## Wat de bron eist

1. Platte recite-woorden die uit meer dan één lettergreep bestaan, hebben
   soft `-` op de zing-grenzen (`eeu-wig`, niet `eeuwig`).
2. Hetzelfde geldt voor L-tekst in `.mvsa` (recite tussen haakjes, cadens
   met hyphen-keten): de zichtbare deling is de canonieke.
   `mvsa syllabify` (en kolom-align) werken **alleen** op die zingtekst in
   L-regels — parallel aan `vsa syllabify` op de VSA-body. Wat blijft staan:
   maatstrepen en herhalingstekens (`|`, `|:`, `:|`), recite-haakjes `(…)`
   (op woord- of lettergreepgrens), ELMs/`&`-kolommen, uitvoeraanwijzingen
   `[…]` (zoals `[//.]`), hard `=` (orthografisch koppelteken), YAML-frontmatter
   (inclusief `zoektekst`), `@`-directives, S/A/T/B, en commentaar
   (`#`-regels én HTML-comments `<!-- … -->`). Alleen soft `-` in L-zingtekst
   wijzigt. Voorbeelden:
   [`syllabificatie-structural-marks.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/development/examples/mvsa/syllabificatie-structural-marks.mvsa),
   [`syllabificatie-marks-hemelum.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/development/examples/mvsa/syllabificatie-marks-hemelum.mvsa).
3. Scopes blijven de structurele zangposities: één lettergreep per scope.
   Soft `-` naast `{`/`}` hoort niet in de bron. Tooling mag letters tussen
   scope en platte tekst herverdelen (`{/A}dam`), maar zet geen soft `-`
   tegen een accolade.

### Voorbeeld `.mvsa` (recite + cadens)

Klein demo-bestand met meerdere recite-runs
[`examples/mvsa/syllabificatie-recite-mini.mvsa`](https://github.com/orthodox-ronl/VSA-tooling/blob/development/examples/mvsa/syllabificatie-recite-mini.mvsa):

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

Elk lemma (letters zonder soft `-` en zonder hard `=`) heeft **standaard
één** canonieke hyphenvorm. Zeldzame uitzonderingen (bijv. alleluia met
vier of vijf lettergrepen) mogen **expliciete** extra vormen hebben via
een regel die met `+` begint. Die lijst is de norm voor gezongen body-tekst
(niet frontmatter, comments, ids of `lyrics.txt`).

| Afspraak       | Inhoud                                                                                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Talen          | `nl` (Latijn) en `ksl` (Cyrillisch); CLI `--lyrics-lang {auto,nl,ksl}`                                                                                                       |
| Default `auto` | **Per woord:** Latijn → `syllable_dictionary.nl.txt`, Cyrillisch → `.ksl.txt`. Beide schriften in één bron worden nagelopen.                                                |
| Force CLI      | `--lyrics-lang nl` of `ksl`: alleen dat schrift; andere taal overslaan + `VSA-SYLLABLE-LANG-SKIPPED`                                                                         |
| Frontmatter    | `taal: nl` · `ksl` · of `[nl, ksl]` = welke talen in **dit** bestand horen; mismatch → `VSA-SYLLABLE-TAAL-MISMATCH` (warning). Geen sessie-uitschakelaar.                   |
| `@taal xx`     | **Kiest welke woordenlijst** voor een passage geldt (geen taalkundige claim: `Kyrie eleison` in Latijns schrift mag gewoon in de `nl`-lijst). Voor codes **zonder woordenlijst** (`ro`, `el`, `ka`, …): `@taal ro` op een eigen regel geldt voor alles daarna tot de volgende `@taal`; `@taal auto` = terug naar herkenning op schrift. In `.mvsa` is het de bestaande sticky `@taal` (vóór de `L:`-regel), in `.vsa` een regel in de tekst. Woorden in zo'n taal worden **niet gecontroleerd** en **niet door syllabify aangepast**. Alleen `nl`/`ksl` hebben een lijst; Latijns schrift is anders niet van Nederlands te onderscheiden. Een code is 2–3 kleine letters. |
| Canon (org)    | `bibliotheek/data/syllable_dictionary.nl.txt` en `.ksl.txt` (content-repo; commit/push daar)                                                                                |
| Config         | `vsa.toml` → `[syllabificatie] dictionary = "…"` (historisch NL; bij `--lyrics-lang ksl` alleen als pad al op `.ksl.txt` eindigt)                                           |
| CLI            | `--syllable-dictionary PAD` en `--lyrics-lang` op `vsa`/`mvsa` `validate` / `syllabify`                                                                                     |
| Env            | `VSA_SYLLABLE_DICTIONARY` (nl); `VSA_SYLLABLE_DICTIONARY_KSL` (ksl)                                                                                                         |
| Pad-auto       | `data/syllable_dictionary.<lang>.txt` in de werkmap, of sibling `bibliotheek/data/…`                                                                                        |
| Loader         | `vsa.syllable_dictionary`                                                                                                                                                   |
| Vorm           | Eén hyphenvorm per regel (kleine letters); soft `-` / hard `=`; `#` = commentaar; `+vorm` = toegestaan alternatief voor het open lemma                                      |
| Primair / alt  | Regel zonder `+` = primaire vorm (syllabify-default); `+vorm` = zelfde lemma, ook OK bij validate                                                                           |
| Volgorde       | Entries alfabetisch op **lemma** (daarna `+`-alts); TTY/append herschrijft gesorteerd                                                                                       |
| Matching       | Lemma = letters zonder `-`/`=`, case-fold; validate OK als bronvorm ∈ {primair} ∪ {alts}                                                                                    |
| Schriftfilter  | Bij force `nl`/`ksl`: alleen kernen van dat schrift. Bij `auto`: geen uitsluiting — per kern de bijbehorende lijst (ksl: geen NL-Pyphen-voorstel)                           |
| Onderhoud      | Wijziging in de content-repo, of interactief op TTY (schrijft naar het actieve pad)                                                                                         |

**`--lyrics-lang auto` (default):** validate/syllabify lopen **alle**
lyric-woorden na. Elk woord met Cyrillisch gebruikt
`syllable_dictionary.ksl.txt`; elk Latijns woord
`syllable_dictionary.nl.txt`. Nooit: “één Cyrillisch teken → heel bestand
alleen ksl”.

**Force:** `--lyrics-lang nl` of `ksl` behandelt tijdelijk alleen dat
schrift (sessie). Overgeslagen lyrics → één melding
`VSA-SYLLABLE-LANG-SKIPPED` per bron. Frontmatter `taal` zet geen taal uit.

Padvoorrang per gekozen taal: CLI-pad → (nl) `vsa.toml` → env →
bestands-auto-detect. Andere repo’s zetten hun eigen lijst in hun
`vsa.toml`. Zonder pad is de mapping leeg (geen stille package-lijst in
VSA-tooling). De ksl-lijst mag **leeg** starten; vullen via
TTY/catalogus-review volgt later.

Startset (nl): catalogus-review plus handmatige correcties (o.a. `a-pos-tel`,
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

In `.mvsa` tellen **recite-haakjes** `(…)` (en ELMs) niet mee als
woordbreuk voor de woordenlijst: `Al-le-(lu-ja` hoort bij `Al-le-lu-ja`
(canoniek schrijven blijft `Al-le (-lu-ja…)` met soft `-` *in* de haakjes;
zie [MVSA-syntax](../specification-mvsa/syntax.md)).

Positie-meldingen en dictionary-vervangingen zoeken **alleen** in de
gezongen body (na strip van YAML-frontmatter inclusief `zoektekst`, en na
HTML/`#`-commentaar) — nooit in metadata of commentaarregels. Esc of
**Ctrl+C** in de interactieve check stopt de hele validate-/syllabify-run
zonder een stapel verdere dictionary-meldingen.

`vsa validate` / `mvsa validate` vullen ontbrekende soft `-` automatisch bij
(zelfde logica als `vsa syllabify` / `mvsa syllabify`), schrijven het bestand
terug, en melden `VSA-SYLLABIFY-APPLIED` / `MVSA-SYLLABIFY-APPLIED`.
`zoektekst` blijft onaangeroerd.

| Code                           | Wanneer                                                                                         | Standaard                                            |
| ------------------------------ | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `VSA-SYLLABLE-DICT-MISMATCH`   | Lemma staat in de lijst, bronvorm wijkt af (bijv. `eeuwig` i.p.v. `eeu-wig`)                    | **error** (`.vsa`); op `.mvsa` voorlopig **warning** |
| `VSA-SYLLABLE-DICT-UNKNOWN`    | Lemma ontbreekt, én het woord heeft soft `-`/`=` óf Pyphen ziet breuken                         | **error** (`.vsa`); op `.mvsa` voorlopig **warning** |
| `VSA-SYLLABLE-LANG-SKIPPED`    | CLI forceerde `nl`/`ksl` terwijl de bron ook lyrics van de andere taal heeft                    | **warning**                                          |
| `VSA-SYLLABLE-TAAL-MISMATCH`   | Frontmatter `taal` dekt niet alle schriften in de lyrics (bijv. `taal: nl` + Cyrillisch in body) | **warning**                                          |

Op een **TTY** kun je findings meteen afhandelen. Bij batch verschijnt
`--- <catalogus-id> ---` per stuk. Elke vraag toont eerst een klikbare
locatie relatief t.o.v. de werkmap (`pad\bestand.vsa:regel:kolom:`), dan
de melding, dan de toetsen.

| Situatie                                | Enter / Spatie                                              | Andere toetsen                                                                   |
| --------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `MISMATCH`                              | Corrigeer de bron naar de canonieke vorm                    | `+`/`=` = huidige vorm in lijst; Tab = overslaan; Esc = stop; of typ andere vorm |
| `UNKNOWN` (met of zonder streepjes)     | Voeg voorstel / huidige vorm toe aan de lijst               | `+`/`=` = huidige vorm in lijst; Tab = overslaan; Esc = stop; of typ andere vorm |

Afbreken met **Esc** (of Ctrl+C): exitcode **2**; batch-validate/syllabify/kuiser
**én** `{straat} products` gaan geen volgende bestanden meer langs. `+`/`=`
schrijft de huidige vorm naar de woordenlijst (nieuw lemma, of `+`-alternatief
als het lemma al bestaat).

**Products / C3:** `vsa`/`mvsa`/`mscz products` opent **geen**
dictionary-TTY-prompt — ook niet via de score-ir-brug (`import` → kuiser
op tijdelijke `.mvsa`). Canoniciteitscheck (C3) en import-kuiser zijn
altijd non-interactief. Streepjesproblemen daar zijn harde fouten of
(bij `.mvsa`) warnings zonder vraag. Interactief corrigeren hoort bij
`validate` / `syllabify` / `kuiser`.

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
| 4b   | Lege `syllable_dictionary.ksl.txt` + `--lyrics-lang {nl,ksl}`       | gedaan                                     |
| 4c   | Default `--lyrics-lang auto` (eerst: één taal per bron)             | gedaan (vervangen door 4e)                 |
| 4d   | Catalogus-vulling ksl                                               | open                                       |
| 4e   | `auto` = per woord nl+ksl; FM `taal`; `LANG-SKIPPED` / `TAAL-MISMATCH` | gedaan                                  |
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
