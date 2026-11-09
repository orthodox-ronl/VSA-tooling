# Eigen partituur-SVG — voorbeelden

Geen standaardproduct. Het scherm op de site blijft OSMD.
Deze platen laten de drie beelden zien die `mvsa svg --engine eigen` tekent.

Open `index.html` in een browser. De plaat heeft de eigen breedte en
wordt alleen kleiner als het venster smaller is. Een andere regelbreedte
kies je met `--system-width` (default 760).

Opnieuw maken:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
mvsa svg examples\bug-cases\corib\alleluia-toon-8.mvsa --engine eigen --view vsa-notes -o examples\spikes\eigen-svg\alleluia-toon-8.vsa-notes.svg
```

`--view` is `notes`, `vsa-notes` of `vsa`. Zonder `-o` komt het bestand
naast de bron te staan, als `….mvsa.eigen-notes.svg`, en niet in de
plaats van het product `….mvsa.svg`.
