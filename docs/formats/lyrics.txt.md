# `*.lyrics.txt` — platte gezongen tekst

Standaardproduct: sibling met doorlopende gezongen tekst (zonder soft `-`).
Diepte voor YAML-zoektekst *in* bronnen: [zoektekst](zoektekst.md). Start:
[contract-index](contract-index.md).

## Identiteit

| Veld     | Waarde                                              |
| -------- | --------------------------------------------------- |
| Extensie | `.lyrics.txt` (dubbele suffix: `{bron}.lyrics.txt`) |
| Rol      | Standaardproduct (meta-key `lyrics`)                |
| Sibling  | bijv. `lied.mscz.lyrics.txt`, `lied.vsa.lyrics.txt` |
| Wanneer  | Site-/indexzoeken naast elke notatiebron            |

## Canoniciteit

Canoniek = platte UTF-8-tekst van de gezongen woorden, **zonder** soft
zing-delingstreepjes; hard `=` → leesstreepje volgens exportregels. C1–C4:
[contract-index §C\*](contract-index.md#canoniciteit-en-conversiegates-c).

## Inhoud en metadata

| Onderwerp      | Regel                                                      |
| -------------- | ---------------------------------------------------------- |
| Frontmatter    | Geen                                                       |
| Encoding       | UTF-8                                                      |
| YAML-zoektekst | Blijft optioneel *in* `.vsa`/`.mvsa` — niet in dit product |

## Syllabificatie

**Strip** soft `-` (doorlopende woorden). Geen syllabic-bruggen. Hub:
[syllabificatie](syllabificatie.md).

## Melisma en binding

n.v.t. — geen noten.

## Transliteratie

n.v.t. in het standaard lyrics-product (één taal/laag zoals de bronexport).

## Stemmen en partijen

n.v.t. (samengevoegde gezongen tekst volgens `text`-export).

## Leesbaarheid

n.v.t. (platte tekst).

## Herkomst

Merge key `lyrics` in [products-meta](products-meta.md).

## Conversies

| Bron                       | CLI                                   |
| -------------------------- | ------------------------------------- |
| `.vsa` / `.mvsa` / `.mscz` | `{straat} text` / `{straat} products` |

Man-pagina: [`vsa text`](../reference/cli/text.md).

## Validatie

Vergelijk met bronlyrics na strip; CI `check_lyrics_products` (bibliotheek).

## Zie ook

- [zoektekst](zoektekst.md)
- [Formaten & CLI — overzicht](index.md)
