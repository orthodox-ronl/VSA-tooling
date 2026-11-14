# Configuratiereferentie

## `vsa.toml`

Projectdefaults worden vastgelegd in `vsa.toml`.

```toml
[rendering]
max-line-width = 800

[hugo]
assets-url-prefix = "/vsa"
output-mode = "img"

[audio]
format = "mp3"

[syllabificatie]
dictionary = "data/syllable_dictionary.nl.txt"

[validation.severity]
VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH = "warning"
```

Zonder expliciete `--config` zoekt `vsa` naar `vsa.toml` in de **werkmap**.

## Defaults

| Instelling                        | Default | Betekenis                                      |
| --------------------------------- | ------- | ---------------------------------------------- |
| `max-line-width`                  | `800`   | Maximale SVG-regelbreedte                      |
| `assets-url-prefix`               | `/vsa`  | URL-prefix voor SVG-assets                     |
| `output-mode`                     | `img`   | Markdown-uitvoer als `<img>`                   |
| `audio.format`                    | `mp3`   | Default voor `vsa audio`                       |
| `syllabificatie.dictionary`       | (geen)  | Pad naar canonieke syllable-dictionary (relatief t.o.v. de toml) |

## Voorrang

```text
CLI-optie (--syllable-dictionary, …)
  ↓
vsa.toml
  ↓
omgeving (VSA_SYLLABLE_DICTIONARY)
  ↓
auto-detect / default
```

## Severity-overrides

Gebruik severity-overrides om specifieke semantische meldingen tijdelijk als waarschuwing te behandelen.

```toml
[validation.severity]
VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH = "warning"
VSA-SYLLABIFY-MISSING-HYPHENS = "error"
```

| Waarde    | Betekenis                              |
| --------- | -------------------------------------- |
| `error`   | Validatie faalt                        |
| `warning` | Melding tonen, verwerking mag doorgaan |

`VSA-SYLLABIFY-MISSING-HYPHENS` is standaard **warning** (ontbrekende
zing-deling in platte tekst). Zet op `error` als de catalogus grotendeels
gesyllabificeerd is — zie [syllabificatie](../formats/syllabificatie.md).

## Commando-ondersteuning

| Commando               | Severity? | `[audio]`? | `[syllabificatie]`? |
| ---------------------- | --------- | ---------- | ------------------- |
| `vsa validate`         | Ja        | Nee        | Ja                  |
| `vsa syllabify`        | Nee       | Nee        | Ja                  |
| `vsa process`          | Ja        | Nee        | Ja (via validate)   |
| `vsa build-markdown`   | Ja        | Nee        | Ja (via validate)   |
| `vsa audio`            | Nee       | Ja         | Nee                 |
| `mvsa mp3`/`ogg`/`wav` | Nee       | Nee        | Nee                 |
| `vsa svg`              | Nee       | Nee        | Nee                 |
| `vsa blocks`           | Nee       | Nee        | Nee                 |
| `vsa parse`            | Nee       | Nee        | Nee                 |

## Hard blijvende fouten

Syntax-errors blijven altijd `error`.

Voorbeeld:

```text
{onafgesloten
```
