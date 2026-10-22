# Spike: Score-IR → OSMD (partituur in de browser)

Proef: kan **OpenSheetMusicDisplay** jullie partituur tekenen wanneer de
MusicXML uit **Score-IR** komt (niet rechtstreeks uit `.mvsa`)?

Geen CoriB-product — bewijs voor het schermpad
`.mvsa` → Score-IR → MusicXML → OSMD.

## Bestanden

| Bestand                  | Rol                                                         |
| ------------------------ | ----------------------------------------------------------- |
| `index.html`             | Viewer (OSMD via CDN; laadt IR-meta + MusicXML)             |
| `score.score-ir.json`    | Score-IR uit `1a-vredeslitanie.mvsa`                        |
| `score.musicxml`         | Partituur-MusicXML **uit** die Score-IR                     |
| `README.md`              | Deze uitleg                                                 |

## Regenereren

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa mvsa score-ir examples\mvsa\1a-vredeslitanie.mvsa -o examples\spikes\partituur-browser\score.score-ir.json --musicxml examples\spikes\partituur-browser\score.musicxml
```

## Lokaal openen

Browsers blokkeren vaak `file://` + `fetch`. Start een HTTP-servertje in
**deze map**:

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling\examples\spikes\partituur-browser
python -m http.server 8765
```

Open: <http://127.0.0.1:8765/>

## Wat we willen zien

1. Twee balken (SA / TB).
2. Lyrics tussen de balken.
3. `@tekst`-cues (o.a. “P: Gezegend…”).
4. Statusregel noemt Score-IR-titel/matental.

## Relatie tot product

| Pad                                                            | Rol                                              |
| -------------------------------------------------------------- | ------------------------------------------------ |
| [`mvsa svg`](../../../docs/reference/cli/mvsa.md#vsa-mvsa-svg) | Koormap-SVG via MuseScore (brug)                 |
| Score-IR + deze spike                                          | Schermketen zonder MuseScore (OSMD)              |
| CoriB                                                          | Later: speler op dezelfde Score-IR → tekenbrug   |

Contract: [partituur-ir.md](../../../docs/plans/partituur-ir.md).
Module: `vsa.score_ir_musicxml`.
