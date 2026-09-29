# `vsa audio` — exporteren naar audio (preview)

Exporteer playback-MusicXML (of ``.vsa`` / ``.mvsa`` / ``.mscz``) naar een
afspeelbaar audiobestand (``.mp3`` standaard) via MuseScore. Alleen het
**artefact** — geen speler en geen stemkeuze. De consumer-site maakt de
afspeelknop.

## Synopsis

```text
vsa audio [-h] [--config CONFIG] [--format {mp3,ogg,wav}]
          [--musescore PATH] [--section SECTION] [--keep-mxl PATH]
          input output
```

Alias voor ``.mvsa``-workflows: [`mvsa audio`](mvsa.md#vsa-mvsa-audio)
(``path`` + ``-o``).

## Beschrijving

`vsa audio` leest `input` en schrijft `output`:

| `input`-type              | Gedrag                                                                 |
| ------------------------- | ---------------------------------------------------------------------- |
| ``.mxl`` / ``.musicxml``  | Direct MuseScore → audio                                               |
| ``.vsa``                  | Eerst playback-MusicXML, dan MuseScore → audio                         |
| ``.mvsa``                 | Eerst playback-MusicXML (vier parts), dan MuseScore → audio            |
| ``.mscz``                 | Fallback: MuseScore → ``.mxl``, dan → audio                            |

Zonder expliciete extensie op `output` geldt ``--format`` (default ``mp3``,
of ``[audio].format`` in ``vsa.toml``).

Vereist **MuseScore 4** (of 3), zoals `mvsa pdf` / `mvsa mscz`.

## Argumenten en opties

| Naam                       | Verplicht | Betekenis                                                                 | Default                          |
| -------------------------- | --------- | ------------------------------------------------------------------------- | -------------------------------- |
| `input`                    | Ja        | Bronbestand (``.mxl`` / ``.musicxml`` / ``.vsa`` / ``.mvsa`` / ``.mscz``) | —                                |
| `output`                   | Ja        | Doelbestand (``.mp3`` / ``.ogg`` / ``.wav``)                              | —                                |
| `--format {mp3,ogg,wav}`   | Nee       | Formaat als `output` geen audio-extensie heeft                            | ``mp3`` of ``[audio].format``    |
| `--musescore PATH`         | Nee       | Pad naar MuseScore-executable                                             | Auto-detectie                    |
| `--section SECTION`        | Nee       | Alleen bij ``.mvsa``: deze ``@sectie``-id                                 | Alle secties                     |
| `--keep-mxl PATH`          | Nee       | Bewaar tussenliggende playback-``.mxl``                                   | — (tijdelijk bestand)            |
| `--config CONFIG`          | Nee       | Pad naar ``vsa.toml``                                                     | Auto-detectie                    |
| `-h`, `--help`             | Nee       | Toon hulp                                                                 | —                                |

## Output

- **stdout**: `Audio geschreven naar: <pad>` (en optioneel `MXL: …`)
- **bestand**: het audiobestand op `output`

## Exit status

| Exitcode | Betekenis                                      |
| -------- | ---------------------------------------------- |
| `0`      | Succes                                         |
| `1`      | Bron ontbreekt, MuseScore ontbreekt, of fout   |

## Voorbeelden

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
vsa audio examples\docs-walkthroughs\coria-oefenlink\oefenmelodie.vsa generated\oefenmelodie.mp3
vsa audio generated\lied.mxl generated\lied.mp3
vsa audio generated\lied.mxl generated\lied --format ogg
```

## Zie ook

- [Formaat `.mp3` / audio](../../formats/audio.md)
- [`mvsa audio`](mvsa.md#vsa-mvsa-audio)
- [`vsa musicxml`](musicxml.md) (playback-``.mxl``)
