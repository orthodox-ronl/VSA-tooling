# Steekproef — VSA + Hemelum tropaar-toon-4 → schets-`.mvsa`

Drie bestanden in [`schetsen/`](schetsen/); bron-`.vsa` ongemoeid.
Disclaimer uit
[`disclaimer-vsa-mvsa.sjabloon.txt`](../../disclaimer-vsa-mvsa.sjabloon.txt).

| Uitvoer                                                                                                          | Bron                                                        | Status                          |
| ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------- |
| [`schetsen/tropaar-profeet-elia-toon-4.schets.mvsa`](schetsen/tropaar-profeet-elia-toon-4.schets.mvsa)           | `T4-06-profeet-elia.vsa` (library)                          | OK — mapping + `mvsa validate`  |
| [`schetsen/tropaar-nikolaas-van-myra-toon-4.schets.mvsa`](schetsen/tropaar-nikolaas-van-myra-toon-4.schets.mvsa) | `T4-11-nicolaas-van-myra.vsa`                               | OK — mapping + `mvsa validate`  |
| [`schetsen/kondak-profeet-hosea-toon-4.schets.mvsa`](schetsen/kondak-profeet-hosea-toon-4.schets.mvsa)           | `kondak-profeet-hosea-toon-4.vsa` (hersteld uit commentaar) | OK — mapping + `mvsa validate`  |

Geslaagd: **3/3** (`mvsa validate` groen).

## Lessen voor `vsa mvsa` (emitter)

| Wel                                                         | Niet                                              |
| ----------------------------------------------------------- | ------------------------------------------------- |
| Unieke `@blok 1..n` + `@speelplan 1, 2, …`                  | Herhaalde `f1`/`f2` (MVSA-BLOK-DUP)               |
| Lege lyrics als `&`-melisma op vorige lettergreep (`li_&_`) | Losse `-_` / `__` (L-parser slaat die over)       |
| Formule-`\|: … :\|` alleen in mensformule, niet in schets   | `@speelplan \|: f1, f2 :\| laatste` in echte MVSA |
| Bron-`.vsa` niet overschrijven                              | Fase-A-script dat VSA-bestanden herschrijft       |

## Handcheck MuseScore

Export gelukt (lokaal, niet in git):

| Schets                         | MSCZ                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------- |
| Elia                           | `generated\formule-tekst\schetsen\tropaar-profeet-elia-toon-4.schets.mscz`      |
| Nicolaas                       | `generated\formule-tekst\schetsen\tropaar-nikolaas-van-myra-toon-4.schets.mscz` |
| Hosea (kondak)                 | `generated\formule-tekst\schetsen\kondak-profeet-hosea-toon-4.schets.mscz`      |

**Jij checkt in MuseScore** (mapping-OK ≠ partituur-OK):

- [ ] A/T/B klinken plausibel t.o.v. S
- [ ] Ankers / frasegrenzen oogt goed
- [ ] Recite-print / melisma niet “doorlopende slur”
- [ ] Slotcadens (re vs fa) klopt voor dat stuk

Opnieuw genereren:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
python examples\formule-tekst\scripts\steekproef_vsa_mvsa.py
mvsa validate examples\formule-tekst\tropaar-toon-4\instanties\schetsen
mvsa mscz examples\formule-tekst\tropaar-toon-4\instanties\schetsen\tropaar-profeet-elia-toon-4.schets.mvsa -o generated\formule-tekst\schetsen\tropaar-profeet-elia-toon-4.schets.mscz
mvsa mscz examples\formule-tekst\tropaar-toon-4\instanties\schetsen\tropaar-nikolaas-van-myra-toon-4.schets.mvsa -o generated\formule-tekst\schetsen\tropaar-nikolaas-van-myra-toon-4.schets.mscz
mvsa mscz examples\formule-tekst\tropaar-toon-4\instanties\schetsen\kondak-profeet-hosea-toon-4.schets.mvsa -o generated\formule-tekst\schetsen\kondak-profeet-hosea-toon-4.schets.mscz
```
