from pathlib import Path

from vsa.parser import Parser
from vsa.semantic_validator import SemanticValidator
from vsa.validation_runner import validate_file


def test_modifier_count_mismatch_points_to_scope_location(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
[:] Scharen
jubelen en zich ver{\blij_&~&~}{\den_},
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok

    message = result.messages[0]

    assert message.code == "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"
    assert message.line == 3
    assert message.column > 15


def test_modifier_count_mismatch_points_to_ampersand_compound_scope(tmp_path: Path):
    """Twee hoogtes + één lengte (`{-&\\dre_}`) moet op die scope wijzen, niet op blokstart."""
    path = tmp_path / "andreas.md"
    path.write_text(
        "::: vsa\n"
        "<!-- comment -->\n"
        "[//:] In de bergen hebt gij uzelf door onthouding {krach_}{/tig_}. *\n"
        "{/daar}om zijt gij door {God_.} ge{\\kroond_}, **\n"
        "eerbiedwaardige martelaar An{-&\\dre_}{/as_}. [//:]\n"
        ":::\n",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok
    message = result.messages[0]
    assert message.code == "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"
    assert message.line == 5
    # Kolom van '{' in An{-&\dre_}
    assert message.column == len("eerbiedwaardige martelaar An") + 1


def test_semantic_validator_sets_line_column_from_node_start():
    text = "prefix An{-&\\dre_}{/as_}."
    doc = Parser(text).parse()
    result = SemanticValidator(doc, source_text=text).validate()

    assert result.has_errors()
    item = result.items[0]
    assert item.code == "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"
    assert item.line == 1
    assert item.column == len("prefix An") + 1
