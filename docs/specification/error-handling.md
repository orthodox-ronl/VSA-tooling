# Foutafhandeling

## Doel

Dit document beschrijft hoe VSA-implementaties fouten, waarschuwingen en [diagnostische meldingen](@) behoren te genereren en te rapporteren.

---

## Severity levels

[VSA](@) onderscheidt drie soorten [diagnostische meldingen](@):

* `error` — het document is ongeldig.
* `warning` — het document is geldig, maar bevat een mogelijk probleem.
* `info` — een informatieve melding zonder invloed op de geldigheid van het document.

---

## Foutcategorieën

[Diagnostische meldingen](@) worden onderverdeeld in de volgende categorieën:

* **syntax error** — de invoer voldoet niet aan de grammatica;
* **semantic error** — de invoer is syntactisch geldig, maar de betekenis is ongeldig;
* **validation error** — een normatieve validatieregel is geschonden;
* **rendering error** — het document kan niet correct worden gerenderd;
* **configuration error** — een configuratie- of omgevingsprobleem verhindert correcte verwerking.

---

## Diagnostiek

Het doel van diagnostiek is de gebruiker zoveel mogelijk bruikbare informatie te geven over problemen die tijdens de verwerking van een VSA-document worden aangetroffen.

Implementaties behoren daarom, waar redelijkerwijs mogelijk, de verwerking van een document voort te zetten nadat een fout is vastgesteld. Ook meldingen met [severity](@) `error` behoren niet automatisch te leiden tot onmiddellijke beëindiging van de verwerking. Hierdoor kunnen meerdere onafhankelijke fouten tijdens één verwerkingsronde worden gerapporteerd, zodat de auteur deze in één keer kan corrigeren.

Een implementatie mag de verwerking uitsluitend beëindigen wanneer verdere verwerking niet meer mogelijk is, bijvoorbeeld doordat de resterende documentstructuur niet meer betrouwbaar kan worden geïnterpreteerd of doordat geen zinvolle diagnostiek meer kan worden geproduceerd.

---

## Diagnostische meldingen

Standaard behoort iedere [diagnostische melding](@) minimaal de volgende informatie te bevatten:

* [severity](@);
* foutcode;
* foutcategorie;
* naam van het bronbestand;
* locatie in het bronbestand (regelnummer en positie);
* een korte beschrijving van het probleem;
* indien mogelijk een concrete suggestie voor herstel of een verwijzing naar documentatie die specifiek betrekking heeft op de betreffende foutcode.

---

## CLI- en omgevingsfouten

Fouten buiten de notatie-diagnostiek (verkeerde extensie, ontbrekend pad,
MuseScore niet gevonden, CLI-misbruik) volgen dezelfde leesbaarheid voor de
**beheerder**:

1. **Locatie** — `pad:regel:kolom:` wanneer bekend; anders `pad:regel:` of
   alleen `pad:`; bij puur CLI-gebruik (geen bronbestand) alleen de tekst.
2. **Beschrijving** — volledige Nederlandse zin: wat er misgaat. Mag over
   **meerdere regels** (niet alles op één regel proppen).
3. **Herstel** — daarna een `Hint:`-blok (ook meerregelig) met concrete
   actie (juiste straat-CLI, andere `--template`, `vsa validate`, …).

Geen kale `ERROR:`-prefix zonder pad of herstelhint. Implementatie in tooling:
`vsa.cli_messages` (`emit_cli_error` / `emit_cli_exception`).

Bronfouten in `.vsa` blijven via `vsa validate` de volle diagnostiekvorm
gebruiken (foutcode + context); zie hierboven.

---

## Compacte uitvoer

Implementaties behoren een optie te bieden waarmee [diagnostische meldingen](@) in een compacte, machinevriendelijke vorm worden weergegeven.

In deze modus bevat iedere melding uitsluitend:

* foutcode;
* naam van het bronbestand;
* regelnummer;
* positie.

Deze uitvoervorm is bedoeld voor geautomatiseerde omgevingen, zoals CI/CD-pipelines en GitHub Actions, waar compacte, stabiele en eenvoudig verwerkbare diagnostiek de voorkeur heeft boven uitgebreide toelichtingen.

---

## Samenvattingen

Implementaties mogen na afloop van de verwerking een samenvatting van de aangetroffen [diagnostische meldingen](@) tonen.

Een samenvatting kan bijvoorbeeld het aantal `error`-, `warning`- en `info`-meldingen bevatten en is uitsluitend informatief.

---

## Compatibiliteit

Nieuwe foutcodes mogen in een MINOR-versie worden toegevoegd.

Bestaande foutcodes en hun betekenis mogen binnen dezelfde MAJOR-versie niet worden gewijzigd.

Foutcodes mogen uitsluitend worden verwijderd in een volgende MAJOR-versie.
