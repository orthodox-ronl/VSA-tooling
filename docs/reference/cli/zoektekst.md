# `vsa zoektekst` — platte tekst in YAML-frontmatter

Vult of controleert het veld **`zoektekst`** in canonieke `.vsa` / `.mvsa`
(YAML-frontmatter). Bedoeld voor editorzoeken (Ctrl+Shift+F). Contract:
[Zoektekst](../../formats/zoektekst.md).

## Synopsis

```text
vsa zoektekst [-h] [--check] [-o OUTPUT] path [path …]
```

## Gedrag

| Modus           | Betekenis                                                                                      |
| --------------- | ---------------------------------------------------------------------------------------------- |
| (default)       | Schrijft/update `zoektekst` in-place uit body-extractie (`vsa text`-logica, genormaliseerd).   |
| `--check`       | Geen schrijven; exit **1** als het veld ontbreekt (bij niet-lege tekst) of afwijkt.            |
| `-o OUTPUT`     | Schrijf naar dit pad i.p.v. in-place (alleen bij precies één bronbestand).                     |

Tweede run zonder wijziging aan de body: **geen** herschrijven (geen
YAML-opmaak-churn). Overige frontmatter-sleutels blijven; bij de eerste write
kan PyYAML de opmaak van die sleutels wel normaliseren.

## Argumenten

| Naam       | Betekenis                                      |
| ---------- | ---------------------------------------------- |
| `path`     | `.vsa` / `.mvsa`-bestand of map (recursief).   |
| `--check`  | Alleen controleren.                            |
| `-o`       | Optioneel uitvoerpad (één bronbestand).        |

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa zoektekst examples\mvsa\alleluia-toon-1.mvsa
vsa zoektekst examples\mvsa --check
vsa zoektekst examples\minimal\050_svg_demo.vsa -o generated\demo.zoektekst.vsa
```

Catalogus-CI (later): `vsa zoektekst content-source\catalogus --check`, of
`vsa mvsa validate … --require-zoektekst` voor alleen `.mvsa`.

## Zie ook

- [Zoektekst (contract)](../../formats/zoektekst.md)
- [`vsa text`](text.md) — extractie zonder frontmatter-veld
- [`mvsa validate --require-zoektekst`](mvsa.md)
