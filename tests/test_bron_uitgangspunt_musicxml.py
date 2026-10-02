"""bron.uitgangspunt → MusicXML identification/source."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from vsa.ast import Document
from vsa.musicxml_renderer import MusicXMLRenderer
from vsa.yaml_frontmatter import (
    bron_uitgangspunt_from_frontmatter,
    frontmatter_to_block_metadata,
    parse_vsa_frontmatter,
)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def test_frontmatter_promotes_playback_and_bron() -> None:
    text = """---
do: F4
mode: major
tempo: 120
partituur:
  title: Test
  composer: Traditioneel
bron:
  uitgangspunt: Liturgikon, p.58
  bewerking: streepjes anders
---
[//:] a [//:]
"""
    fm, body = parse_vsa_frontmatter(text)
    assert bron_uitgangspunt_from_frontmatter(fm) == "Liturgikon, p.58"
    meta = frontmatter_to_block_metadata(fm)
    assert meta["do"] == "F4"
    assert meta["bron.uitgangspunt"] == "Liturgikon, p.58"
    assert meta["partituur.title"] == "Test"
    assert "[//:]" in body


def test_musicxml_emits_source_from_bron_uitgangspunt() -> None:
    meta = frontmatter_to_block_metadata(
        {
            "do": "F4",
            "mode": "major",
            "tempo": 120,
            "bron": {"uitgangspunt": "Meneon I, p.12-13"},
            "partituur": {"title": "Voorbeeld", "composer": "Traditioneel"},
        }
    )
    # Minimal empty-ish document: renderer needs a Document
    from vsa.parser import Parser

    document = Parser("[//:] test [//:]").parse()
    assert isinstance(document, Document)
    xml = MusicXMLRenderer(meta).render(document)
    root = ET.fromstring(xml)
    sources = [
        c
        for ident in root
        if _local(ident.tag) == "identification"
        for c in ident
        if _local(c.tag) == "source"
    ]
    assert len(sources) == 1
    assert sources[0].text == "Meneon I, p.12-13"
    titles = [
        wt
        for work in root
        if _local(work.tag) == "work"
        for wt in work
        if _local(wt.tag) == "work-title"
    ]
    assert titles and titles[0].text == "Voorbeeld"
