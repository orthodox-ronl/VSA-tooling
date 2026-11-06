# Fase A/B — VSA + tropaar-toon-4-template → MVSA

## Opzet

- **Brontekst:** oorspronkelijke VSA uit het commentaar in elk bestand.
- **Template:** `docs/specification-vsa-templates/library/tropaar-toon-4/template.yaml`
  (uitvoerbare vorm; muzikaal gelijk aan het formule-onderzoek).
- **Mensformule:** `tropaar-toon-4.formule.mvsa` (nog niet door de mapper gelezen).
- **Mapper:** `vsa.template_instance.map_vsa_to_template` (bestaande H1–H9-logica).
- **Normalisatie:** bronnen zonder `*` krijgen per regel een frase (`*`)
  zodat cycle `1,2,…,laatste` kan werken.

## Fase A — resultaat per bestand

Geslaagde mapping: **6/19**

- **kondak-geboorte-van-h-johannes-aartsbisschop-van-shanghai-en-san-francisco-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA 'zuin' = C5, geen passend template-S-slot meer (verwacht o.a. mi)
- **kondak-h-apostel-thaddeos-toon-4.vsa**: OK — 7 frasen `['1', '2', '1', '2', '1', '2', 'laatste']`, 72 noten, S-identiek=True, ankers=6, optional_used=0, f2_optional_skip≈3
- **kondak-icoon-moeder-gods-vladimir-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA 'zijt' = G4, geen passend template-S-slot meer (verwacht o.a. mi, mi, fa, mi)
- **kondak-maria-magdalena-heiligenjaar-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA 'Daar' = Bb4, geen passend template-S-slot meer (verwacht o.a. —)
- **kondak-profeet-hosea-toon-4.vsa**: OK — 5 frasen `['1', '2', '1', '2', 'laatste']`, 61 noten, S-identiek=True, ankers=4, optional_used=0, f2_optional_skip≈2
- **kondak-tempelgang-van-de-moeder-gods-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. mi, re, mi)
- **tropaar-apostel-andreas-de-eerstgeroepene-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. mi, re, mi)
- **tropaar-geboorte-van-h-johannes-aartsbisschop-van-shanghai-en-san-francisco-toon-4.vsa**: OK — 7 frasen `['1', '2', '1', '2', '1', '2', 'laatste']`, 72 noten, S-identiek=True, ankers=6, optional_used=0, f2_optional_skip≈3
- **tropaar-geboorte-van-johannes-de-voorloper-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-REQUIRED-SLOT-UNUSED`: verplicht(e) template-slot(s) niet aangedaan in frase '2': fa, fa/l.st., mi
- **tropaar-gregorios-van-utrecht-ksl-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. re, mi)
- **tropaar-h-marina-toon-4.vsa**: OK — 7 frasen `['1', '2', '1', '2', '1', '2', 'laatste']`, 107 noten, S-identiek=True, ankers=4, optional_used=0, f2_optional_skip≈3
- **tropaar-hh-vaders-startsi-van-optina-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA 'die' = Bb4, geen passend template-S-slot meer (verwacht o.a. —)
- **tropaar-maria-hulp-der-christenen-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. mi, re, mi)
- **tropaar-monnik-martelaar-andreas-toon-4.vsa**: OK — 5 frasen `['1', '2', '1', '2', 'laatste']`, 64 noten, S-identiek=True, ankers=4, optional_used=0, f2_optional_skip≈2
- **tropaar-nikolaas-van-myra-liturgikon-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. re, mi)
- **tropaar-nikolaas-van-myra-toon-4-hemelum.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. re, mi)
- **tropaar-profeet-elia-toon-4.vsa**: OK — 7 frasen `['1', '2', '1', '2', '1', '2', 'laatste']`, 78 noten, S-identiek=True, ankers=4, optional_used=0, f2_optional_skip≈3
- **tropaar-tempelgang-van-de-moeder-gods-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA '(melisma)' = Bb4, geen passend template-S-slot meer (verwacht o.a. mi, re, mi)
- **tropaar-zaterdag-voor-kruisverheffing-toon-4.vsa**: MAPPING MISLUKT — `VSA-TEMPLATE-PITCH-MISMATCH`: hoogte-mismatch: VSA 'ken,' = C5, geen passend template-S-slot meer (verwacht o.a. fa, mi)

## Foutcodes (clusters)

- `VSA-TEMPLATE-PITCH-MISMATCH`: 12
  - kondak-geboorte-van-h-johannes-aartsbisschop-van-shanghai-en-san-francisco-toon-4.vsa: hoogte-mismatch: VSA 'zuin' = C5, geen passend template-S-slot meer (verwacht o.a. mi)
- `VSA-TEMPLATE-REQUIRED-SLOT-UNUSED`: 1
  - tropaar-geboorte-van-johannes-de-voorloper-toon-4.vsa: verplicht(e) template-slot(s) niet aangedaan in frase '2': fa, fa/l.st., mi

## Fase B — analyse en advies

### Wat deze ronde anders testte

Niet: “raad de melodie uit tekst+klemtoon”.
Wél: “past deze VSA op de bekende tropaar-toon-4-formule, en kunnen we
daaruit een SATB-MVSA schrijven?”.

Daardoor is **S-identiteit bij succes geen verrassing**: de mapper koppelt
VSA-noten aan template-slots en behoudt de VSA-pitch op S. De waarde zit in:

1. harde afwijzing als S niet op de formule past;
2. synchrone A/T/B uit de template;
3. optionals/ankers die wél of niet vuren.

### Lees de getallen zo

- Mapping OK: **6/19** bestanden.
- Een hoge OK-score betekent: dit corpus is *in principe* automatiseerbaar
  met de huidige tropaar-toon-4-template + bestaande mapper.
- Fouten zijn **bruikbare signalen** (verkeerde frasegrenzen, pitch buiten
  formule, mode/do, ontbrekende `*`), geen stille verkeerde partituren.

### Praktische bruikbaarheid (verwachting)

| Situatie | Bruikbaarheid | Toelichting |
| --- | --- | --- |
| Tropaar/kondak toon 4 met `*`-frasen, do/mode=F4/major | **Hoog** | Zelfde pad als Elia-tests in de repo |
| Zelfde zonder `*` (alleen regeleinden) | **Middel** | Werkt na normalisatie `*` per regel; moet redactioneel gecontroleerd |
| Vrije afwijkingen van de formule (extra toon, andere cadens) | **Laag t/m bewust handwerk** | Mapper faalt hard — goed voor kwaliteit, vraagt VSA- of template-fix |
| Productie-MVSA voor koor zonder nabewerking | **Voorzichtig** | A/T/B zijn provisional; layout/recite-print nog productstraat |
| Vervanging van ftxt-only als hoofdpad | **Ja, aanbevolen** | Veel minder raden; hergebruikt bestaande VSA-vaardigheid |

### Advies (gedegen)

1. **Maak VSA+template→MVSA het hoofdpad** voor formulematige toon-4-stukken.
   De ftxt-route (`'`/`*` alleen) blijft een mogelijk later auteurspad, niet
   de migratiebrug voor bestaand corpus.

2. **Houd `template.yaml` als uitvoerbare bron** tot `.formule.mvsa` een
   parser/validator heeft die naar hetzelfde eventmodel compileert. Anders
   dubbele waarheid.

3. **Redactionele checklist vóór mapping:** `do`/`mode`, expliciete `*`
   (of geaccepteerde normalisatie), één cycle-passende frase telling,
   geen stille toonsoortwissel.

4. **Menselijke steekproef** op A/T/B + ankers (3 stukken: Elia, Nicolaas,
   één kondak) in MuseScore/`mvsa mscz` — mapping-OK ≠ klank/partituur-OK.

5. **Verwachting in de praktijk:** voor netjes geschreven toon-4-VSA die
   bewust op de tropaarformule zit, is automatische SATB-schets **haalbaar
   als hulpmiddel** (schets/Coria/controle). Als eindpublicatie zonder oog
   nog niet; wél als versnelling t.o.v. alles handmatig in MVSA typen.

6. **Niet doen:** steeds uitzonderingen in de ftxt-mapper stapelen. Liever
   VSA iets strakker schrijven of template-slots optioneel maken.

