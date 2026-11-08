"""Frasescheiders `*`/`**`/`/`/`//` en ingesprongen print-wraps."""

from __future__ import annotations

from vsa.corpus_vsa import count_stanzas
from vsa.vsa_stanzas import (
    ensure_stanza_stars,
    extract_stanza_notes,
    fold_indent_continuations,
    music_phrase_lines,
)


def test_fold_indent_continuations_joins_wrap() -> None:
    lines = [
        "{/Want} de onvruchtbaarheid van uw moeder en de stomheid",
        "    van uw vader werd opgeheven",
        "door uw Geboorte.",
    ]
    folded = fold_indent_continuations(lines)
    assert len(folded) == 2
    assert "stomheid van uw vader" in folded[0]
    assert folded[1].startswith("door")


def test_ensure_stanza_stars_respects_indent_wrap() -> None:
    body = (
        "<!-- x -->\n"
        "[//:] Eerste frase hier,\n"
        "{/tweede} frase op eigen regel\n"
        "{/Want} lange regel die doorloopt\n"
        "    op de volgende regel ingesprongen\n"
        "laatste frase inhoud\n"
    )
    norm, notes = ensure_stanza_stars(body)
    assert notes and "ingesprongen" in notes[0]
    # 4 logische frasen — sterren op alle behalve laatste (mag op wrap-eindregel)
    assert norm.count(" *") == 3
    assert "stomheid *" not in norm  # geen premature * vóór de indent-wrap
    assert "ingesprongen *" in norm
    stanzas = extract_stanza_notes("---\ndo: F4\nmode: major\n---\n" + norm)
    assert len(stanzas) == 4


def test_extract_splits_on_star_and_double_star() -> None:
    text = (
        "---\ndo: F4\nmode: major\n---\n"
        "een twee *\n"
        "drie vier **\n"
        "// vijf zes\n"
    )
    stanzas = extract_stanza_notes(text)
    assert len(stanzas) == 3
    lyrics = [" ".join(n.lyric for n in s if n.lyric) for s in stanzas]
    assert lyrics[0].startswith("een")
    assert "drie" in lyrics[1]
    # Leidende // op laatste frase is EHM, geen extra split.
    assert "vijf" in lyrics[2]


def test_leading_slash_slash_does_not_block_line_ensure() -> None:
    """K5-stijl: geen `*`, wel leidende `//` op laatste regel → toch per-regel `*`."""
    body = (
        "eerste regel hier\n"
        "tweede regel daar\n"
        "// laatste regel\n"
    )
    norm, notes = ensure_stanza_stars(body)
    assert notes  # ensure draaide (// leidend telt niet als bron-scheiding)
    assert norm.count(" *") == 2
    stanzas = extract_stanza_notes("---\ndo: F4\nmode: major\n---\n" + norm)
    assert len(stanzas) == 3


def test_count_stanzas_with_indent_wrap() -> None:
    body = (
        "alfa bravo *\n"
        "charlie\n"
        "    delta echo *\n"
        "foxtrot\n"
    )
    assert count_stanzas(body) == 3


def test_music_phrase_lines_skips_html_and_hash() -> None:
    body = (
        "<!-- multi\n"
        "line comment -->\n"
        "# diagnose regel\n"
        "echte frase\n"
        "    wrap\n"
    )
    lines = music_phrase_lines(body)
    assert len(lines) == 1
    assert "echte frase wrap" == " ".join(lines[0].split())
