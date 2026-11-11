from pathlib import Path

from vsa.validation_runner import validate_file
from vsa.vsa_comments import (
    semantic_offset_to_source,
    strip_vsa_html_comments,
    strip_vsa_html_comments_with_offset_map,
)


def test_strip_vsa_html_comments_with_offset_map_matches_strip():
    source = "eerste\n<!-- broncommentaar -->\ntweede <!-- inline --> derde"

    stripped, offset_map = strip_vsa_html_comments_with_offset_map(source)

    assert stripped == strip_vsa_html_comments(source)
    assert len(offset_map) == len(stripped)


def test_offset_map_maps_stripped_characters_back_to_source():
    source = "eerste\n<!-- broncommentaar -->\ntweede"

    stripped, offset_map = strip_vsa_html_comments_with_offset_map(source)

    assert stripped == "eerste\ntweede"
    tweede_index = stripped.index("t")
    assert source[semantic_offset_to_source(offset_map, tweede_index)] == "t"


def test_validation_line_mapping_accounts_for_html_comments(tmp_path: Path):
    path = tmp_path / "demo.md"
    path.write_text(
        r"""::: vsa-notatie
<!-- bron -->
{fout/}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok
    assert result.messages[0].code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    assert result.messages[0].line == 3


def test_validation_line_mapping_accounts_for_frontmatter_and_comments(
    tmp_path: Path,
):
    """Regelnummers zijn bestand-absoluut: YAML-kop + commentaarregels tellen mee."""
    path = tmp_path / "demo.vsa"
    path.write_text(
        "---\n"
        "title: demo\n"
        "---\n"
        "\n"
        "<!-- broncommentaar -->\n"
        "{fout/}\n",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok
    assert result.messages[0].code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    # 1=--- 2=title 3=--- 4=leeg 5=comment 6={fout/}
    assert result.messages[0].line == 6
    assert result.messages[0].column == 6


def test_validation_line_mapping_accounts_for_hash_comments(tmp_path: Path):
    path = tmp_path / "demo.vsa"
    path.write_text(
        "---\n"
        "title: demo\n"
        "---\n"
        "# uitleg voor de beheerder\n"
        "{fout/}\n",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok
    assert result.messages[0].code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    # 1=--- 2=title 3=--- 4=#-comment 5={fout/}
    assert result.messages[0].line == 5


def test_testm_height_marker_positions():
    path = Path("testm.md")
    if not path.is_file():
        return

    result = validate_file(path)
    mismatches = [
        message
        for message in result.messages
        if message.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
    ]

    assert len(mismatches) == 2
    assert any(message.line == 19 and message.column == 69 for message in mismatches)
    assert any(message.line == 25 and message.column == 58 for message in mismatches)
