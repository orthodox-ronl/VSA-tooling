# Corpus-geïnduceerde formule (tropaar toon 4) — ontwerpnotitie

Status: laag 2 (`laatste` `of:` re-close / fa-close) staat in
[`library/tropaar-toon-4/template.yaml`](../../../docs/specification-vsa-templates/library/tropaar-toon-4/template.yaml)
(Hemelum tropaar/kondak). Rest van deze notitie blijft ontwerpachtergrond.

Gerelateerd: handmatige VSA→MVSA (duur opsplitsen vs lange noot in andere
stem); Fase A/B VSA+template
([`../../vsa-bestanden/FASE-A-B-RAPPORT-VSA-TEMPLATE.md`](../../vsa-bestanden/FASE-A-B-RAPPORT-VSA-TEMPLATE.md));
bestaande `of:`-cadenspaden in
[`docs/specification-vsa-templates/mapping-vsa.md`](../../../docs/specification-vsa-templates/mapping-vsa.md).

---

## 1. Wat jij bedoelt (en waarom dat klopt)

Twee inzichten horen bij elkaar:

### A. Duur-raster ≠ melisma

Bij handmatige VSA→MVSA moet je soms **één logische zangpositie** in de
formule uitsplitsen tot **kortere tijdslots**, zodat één stem (of de tekst)
past. Andere stemmen houden dan **één lange noot** over die slots — dat is
**geen** melisma (melisma = meerdere toonhoogtes op één lettergreep), maar
**aanhouden / tie / langere ELM** op dezelfde toon.

Gevolg voor een goed model:

- er is een **gemeenschappelijk tijd-raster** (fijn genoeg voor de “drukste”
  stem of tekst);
- per stem: ofwel een nieuwe toon op een rasterpunt, ofwel **hold**;
- lyrics volgen het raster via L, niet via “elke korte noot = nieuwe
  lettergreep” in elke stem.

Dat is precies hoe MVSA al denkt (L bepaalt posities; S/A/T/B mogen `-`
aanhouden). De formule moet dat **niet tegenspreken** door elk bladnootje
als verplichte syllabe-slot te eisen.

### B. Formule uit het corpus, niet alleen uit één blad

Het toonboekblad is één (belangrijke) getuige. Jullie VSA’s zijn **veel
getuigen**. Als je die per frase-rol (`f1` / `f2` / `laatste`) naast elkaar
legt, zie je een **vaste kern** plus **weinig, herhaalde varianten** — geen
eindeloze chaos.

Dan kun je een template bouwen waarop **alle nette** toon-4-VSA’s passen,
door:

- de kern vast te zetten (recite-toon + typische cadens);
- varianten als **alternatieve paden** of **optionele slots** op te nemen;
- echte outliers (verkeerde familie / typfout) **buiten** de formule te
  houden.

Dat is creatiever dan “één blad = wet”, en strenger dan “alles mag”.

---

## 2. Wat de data nu al zeggen (deze map)

Pitch-runs: opeenvolgende dezelfde toon samengevouwen tot
`recite → cadens-reeks`.

| Rol         | Dominante vorm                         | Aandeel (approx.) | Betekenis                          |
| ----------- | -------------------------------------- | ----------------- | ---------------------------------- |
| **f1**      | recite **A4 (mi)** → **Bb4 A4**        | 42 / 53           | blad/template mi–fa–mi             |
| **f2**      | recite **Bb4 (fa)** → **A4**           | 40 / 49           | blad/template fa… → mi             |
| **laatste** | recite **A4** → **G4 A4**              | 9 / 19            | template nu: mi–**re**–mi          |
| **laatste** | recite **A4** → **Bb4 A4**             | 8 / 19            | Hemelum-achtig: mi–**fa**–mi       |

Conclusie in één zin: **f1/f2 zijn grotendeels één familie**; **`laatste`
heeft twee even serieuze cadensen**. Precies daarom faalde Nicolaas-Hemelum
op de oude template terwijl library-T4-11 wel paste.

Outliers (F4/G4 als recite, lange zwervende cadensen) zijn **schaars** —
die horen in een “niet deze formule”-bak, niet in eindeloze uitzonderingen.

---

## 3. Voorgestelde oplossing: “kern + waargenomen takken”

Noem het een **corpus-geïnduceerde formule** (CIF), met drie lagen.

### Laag 1 — Kern (bijna iedereen)

Per frase-rol:

- vaste **recite-toon** (f1/laatste: mi; f2: fa);
- vaste **richting** van de cadens (eindigt op mi in deze data);
- ankers `e.st.` / `l.st.` als **labels op slots**, niet als “laatste `_` in
  de tekst”.

Dit blijft dicht bij het toonboek én bij 80%+ van f1/f2.

### Laag 2 — Takken (`of:`) uit het corpus

Al voorzien in de mapping-spec: parallelle cadenspaden. Voor `laatste` meteen:

| Pad | Cadens (S)       | Bron in corpus      |
| --- | ---------------- | ------------------- |
| A   | mi – **re** – mi | ~9/19, libraryblad  |
| B   | mi – **fa** – mi | ~8/19, o.a. Hemelum |

De mapper kiest het pad waarvan de VSA-hoogtes kloppen (bestaand gedrag).
Geen tweede YAML-bestand, geen “uitvoeringsvorm” per cadens.

Optioneel later: korte extra takken alleen als ze **≥ N keer** voorkomen
(drempel, bv. 3), anders redactioneel oplossen.

### Laag 3 — Optionele micro-slots (superset, niet spaghetti)

Alleen daar waar sommige VSA’s **extra** toon/stap tonen die anderen
overslaan — analogie van de haakjesnoot op f2:

- leer kandidaten uit alignment (“hier heeft 30% een extra Bb4”);
- markeer `optional: true`;
- nooit een zeldzame typo tot verplichte slot promoveren.

Dit is de “superset”-gedachte, maar **lokaal en geteld**, niet “unie van alle
noten van alle stukken”.

### Duur: raster uit instance, niet uit blad-ELM

Bij VSA→MVSA / instance:

1. VSA levert **S-pitch + gewenste duur per lettergreep/melisma-slot**.
2. Template levert **welke A/T/B-graden** bij dat S-slot horen (pad +
   optionals).
3. Export naar MVSA: bouw een **raster** zo fijn als de fijnste stem/tekst
   nodig heeft; andere stemmen **houden aan** (`-` / langere ELM / tie) —
   jouw handmatige ervaring wordt regel, geen uitzondering.

Belangrijk: template-`duration` op het blad blijft **indicatie**; instance
wint met VSA-ELM (dat stond al in de oude mapping H5).

---

## 4. Hoe je de formule “uit alle VSA’s” maakt (werkwijze)

Geen black-box ML nodig. Wel secuur:

1. **Normaliseer** frasen (`*`), `do`/`mode`.
2. **Wijs rol toe** (cycle f1/f2 + laatste) — zelfde als nu.
3. **Compress** naar recite-run + cadens-run (toonreeksen).
4. **Cluster** cadensvormen; houd clusters boven drempel.
5. **Schrijf YAML** (of later formule-MVSA): kern + `of:` + optionals.
6. **Her-map** heel het corpus: streef % OK; bekijk elke residual.
7. Residuals → óf VSA-fix, óf bewuste nieuwe tak, óf “andere melodie /
   geen tropaar-toon-4-formule”.

Succescriterium (praktisch): **≥90%** van bewust tropaar-toon-4-VSA’s mapt
groen; de rest heeft een **menselijk** besluit, geen stille gok.

---

## 5. Alternatieven (en waarom CIF beter past)

| Idee                                       | Sterk                                                       | Zwak                                  | Oordeel                     |
| ------------------------------------------ | ----------------------------------------------------------- | ------------------------------------- | --------------------------- |
| Alleen toonboek-template                   | Eén bron, rustig                                            | Past niet op ~helft `laatste`         | Te strak als enige waarheid |
| Alleen ftxt+klemtoon                       | Dun typen                                                   | Ondergedetermineerd (Fase A)          | Niet als migratiebrug       |
| Per stuk vrije MVSA                        | Altijd mogelijk                                             | Geen hergebruik formule               | Vangnet, geen standaard     |
| Volledige unie van alle noten              | “Alles past”                                                | Combinatorische soep, blad onleesbaar | Vermijden                   |
| **CIF: kern + getelde takken + optionals** | Corpus+blad; harde fouten blijven; hergebruikt mapper/`of:` | Vereist clustering + drempels         | **Aanbevolen**              |
| Zachte “nearest path” zonder fout          | Altijd output                                               | Stille foute A/T/B                    | Niet doen                   |

---

## 6. Creatieve maar werkbare kernzin

> **De formule is geen enkele lijn op papier, maar een kleine familie van
> paden** (zelfde recite, paar cadensen, hier en daar een optionele schakel),
> **afgeleid uit blad + corpus**.  
> **De tijd** is een raster waarop stemmen mogen **aanhouden**; alleen
> toonwissels op één lettergreep zijn melisma.

Dat verbindt jouw duur-ervaring met de corpus-observatie over `laatste`
(re vs fa) zonder terug te vallen op eindeloze ad-hoc uitzonderingen.

---

## 7. Voorgestelde volgende stap (klein)

1. Breid `template.yaml` `laatste` uit met `of:`: mi–re–mi **en** mi–fa–mi
   (A/T/B voor fa-pad uit blad/Hemelum-steekproef, provisional).
2. Herdraai `fase_a_vsa_template.py` — verwacht sprong in OK-ratio
   (Nicolaas-varianten e.d.).
3. Als dat klopt: één pagina “hoe we clusters tellen” + drempel vastleggen;
   pas daarna optionele micro-slots of formule-MVSA-compiler.

Nog geen bulk-herschrijf van alle VSA’s tot ze op het oude enkele pad passen —
eerst de formule laten groeien waar het corpus **twee gelijke waarheden**
toont.
