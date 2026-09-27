# Topics voor verdere MVSA (en andere) ontwikkelingen

## 1. .vsa bestanden

We zouden de `::: vsa-notatie` syntax moeten accepteren in .vsa bestanden:
- als die er niet is, dan is de inhoud van zo'n bestand 'kale vsa' (zoals nu)
- als die er wel is, dan is alles buiten deze syntax in principe kommentaar (we kunnen daar later - zo nodig - metadata dingen bij kunnen stoppen vergelijkbaar met de .mvsa)

## 2. `::: mvsa`

We zouden naast `::: vsa-notatie` ook `::: mvsa-notatie` willen kunnen gebruiken in markdown bestanden
En die zouden of afgekort moeten kunnen worden tot `::: vsa` resp. `::: mvsa`. Bij een `::: mvsa` geldt dat een maatstreep gevolgd door de `:::` het eind van een sectie aangeeft. Tekst tussen de laatste maatstreep voor de `:::` en de `:::` dient geen doel en is een warning/fout.