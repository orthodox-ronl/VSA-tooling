"""Tests for MusicXML reciting-tone and hyphen syllable splitting."""

import xml.etree.ElementTree as ET

from vsa.musicxml_renderer import (
    MUSICXML_PROFILE_ENGRAVING,
    MusicXMLRenderer,
    RECITING_MODE_WHOLE,
    _syllables_from_token,
    _syllables_from_tokens,
)
from vsa.parser import Parser
from vsa.svg_renderer import SVGRenderer


def _lyrics(xml: str) -> list[tuple[str, str]]:
    root = ET.fromstring(xml.split("dtd\">", 1)[-1])
    result = []
    for note in root.iter("note"):
        lyric = note.find("lyric")
        if lyric is None:
            continue
        text = lyric.findtext("text") or ""
        syllabic = lyric.findtext("syllabic") or ""
        if text or syllabic:
            result.append((text, syllabic))
    return result


def _lyric_texts(xml: str) -> list[str]:
    return [text for text, _ in _lyrics(xml)]


def test_syllables_from_token_hyphen():
    assert _syllables_from_token("mel-se") == [("mel-", "begin"), ("se", "end")]
    assert _syllables_from_token("a-b-c") == [
        ("a-", "begin"),
        ("b-", "middle"),
        ("c", "end"),
    ]
    assert _syllables_from_token("woord") == [("woord", "single")]


def test_syllables_from_tokens_multiple_words():
    assert _syllables_from_tokens(["mel-se", "en"]) == [
        ("mel-", "begin"),
        ("se", "end"),
        ("en", "single"),
    ]


def test_reciting_quarters_default_one_note_per_word():
    doc = Parser("[:] {/do_} jubelen en zich ver {/eind_}").parse()
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    lyrics = _lyrics(xml)
    assert ("jubelen", "single") in lyrics
    assert ("en", "single") in lyrics
    assert ("zich", "single") in lyrics
    assert ("ver", "single") in lyrics
    assert not any("jubelen en zich ver" in t for t, _ in lyrics)


def test_reciting_hyphen_in_plain_text():
    doc = Parser("[:] {//he}mel-se {/eind_}").parse()
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    lyrics = _lyrics(xml)
    assert ("mel-", "begin") in lyrics
    assert ("se", "end") in lyrics


def test_reciting_whole_mode_long_sequence():
    doc = Parser("[:] {/a_} een twee drie vier {/b_}").parse()
    xml = MusicXMLRenderer(
        metadata={"do": "F4", "mode": "major", "reciting-mode": RECITING_MODE_WHOLE},
    ).render(doc)
    lyrics = _lyrics(xml)
    assert any(t == "een twee drie vier" for t, _ in lyrics)


def test_playback_skips_blad_aanwijzing_outside_sung_segments():
    """Strofenummer and refreincue must not become Coria lyrics/notes."""
    doc = Parser("2. [:] {/Heer} [:] Door ...").parse()
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    texts = _lyric_texts(xml)
    assert texts == ["Heer"]
    assert not any("2" in t for t in texts)
    assert not any("Door" in t for t in texts)


def test_playback_debug_height_markers_do_not_drop_sung_material():
    """Extra hoogte-markeringen are checkpoints, not sung/cue brackets."""
    doc = Parser("[:] {/a} [/:] {/b} [:]").parse()
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    assert _lyric_texts(xml) == ["a", "b"]


def test_playback_recite_word_inside_sung_segment_kept():
    doc = Parser("[:] Juich {/voor} [:]").parse()
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    assert _lyric_texts(xml) == ["Juich", "voor"]


def test_html_comment_absent_from_svg_and_musicxml():
    doc = Parser("[:] {/Heer} <!-- Liturgikon, 270 --> [:]").parse()
    svg = SVGRenderer().render_document(doc)
    xml = MusicXMLRenderer(metadata={"do": "F4", "mode": "major"}).render(doc)
    for artifact in (svg, xml):
        assert "Liturgikon" not in artifact
        assert "270" not in artifact
    assert _lyric_texts(xml) == ["Heer"]


def test_engraving_still_recites_scopeless_segment_text():
    """Graveerprofiel blijft ongescopte blad-tekst als reciteertoon exporteren."""
    doc = Parser("2. [:] {/Heer} [:] Door").parse()
    xml = MusicXMLRenderer(
        metadata={
            "do": "F4",
            "mode": "major",
            "musicxml-profile": MUSICXML_PROFILE_ENGRAVING,
        },
    ).render(doc)
    texts = _lyric_texts(xml)
    assert "Heer" in texts
    assert any("2" in t for t in texts)
    assert "Door" in texts
