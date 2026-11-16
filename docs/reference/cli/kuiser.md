# `vsa kuiser` — canonieke authoring-vorm (V1–V8)

**Contract:** [kuiser.md — VSA](../../formats/kuiser.md#vsa-v).

Opkuisen van `.vsa`: frontmatter, zoektekst, syllabify + dictionary,
catalogus-strip, validate-gate. **Geen** body-layout — gebruik
[`vsa format`](format.md).

## Synopsis

```text
vsa kuiser [-h] [-o OUTPUT] [--check] [--werkbank] path [path …]
```

## Beschrijving

| Stap  | Inhoud                                                                 |
| ----- | ---------------------------------------------------------------------- |
| V5    | Strip lege/ongedocumenteerde FM (tenzij `--werkbank`); schetscomments  |
| V3/V4 | Soft `-` + dictionary-waarschuwingen (TTY-correctie zoals syllabify)   |
| V1/V2 | YAML: titel/taal/soort/toon/bron/zoektekst; tempo 131/181              |
| V7    | `vsa validate` zonder errors                                           |
| V8    | `--check` dry-run                                                      |

`do` / `mode` worden **niet** verzonnen; alleen behouden als ze al in de
FM staan. Tempo: ontbrekend of tool-default 130/180 → 131, of 181 bij
tropaar/kondak/stichier.

Default schrijft **in-place**.

## Argumenten

| Optie        | Verplicht | Beschrijving                                                     | Default  |
| ------------ | --------- | ---------------------------------------------------------------- | -------- |
| `path`       | Ja        | `.vsa`-bestand, map, of catalogus-id ([input-pad](input-pad.md)) | —        |
| `-o`         | Nee       | Uitvoer (alleen bij één bronbestand)                             | in-place |
| `--check`    | Nee       | Geen schrijven; exit 1 bij voorgenomen wijziging                 | uit      |
| `--werkbank` | Nee       | Behoud werkbank-FM / schetscomments (V5)                         | uit      |

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa kuiser examples\minimal\001_plain_text.vsa --check
vsa kuiser communievers/kruisverheffing/hemelum --check
vsa kuiser lied.vsa
vsa kuiser schets.vsa --werkbank
```

## Zie ook

- [kuiser.md](../../formats/kuiser.md#vsa-v) · [`vsa format`](format.md)
- [Invoer bestand/map/catalogus-id](input-pad.md)
- [`mvsa kuiser`](mvsa.md#mvsa-kuiser) · [`vsa syllabify`](syllabify.md)
- [`vsa zoektekst`](zoektekst.md)
