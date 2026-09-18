from vsa.block_parser import parse_markdown_blocks


def test_parse_single_block_without_metadata():
    markdown = """# Titel

::: vsa-notatie
[:] {tekst} [:]
:::
"""

    blocks = parse_markdown_blocks(markdown)

    assert len(blocks) == 1
    assert blocks[0].body == "[:] {tekst} [:]"
    assert blocks[0].effective_metadata()["do"] == "F4"


def test_parse_single_block_with_metadata():
    markdown = """::: vsa-notatie
do="C4"
mode="minor"

[:] {tekst} [:]
:::
"""

    blocks = parse_markdown_blocks(markdown)

    assert len(blocks) == 1
    assert blocks[0].metadata["do"] == "C4"
    assert blocks[0].metadata["mode"] == "minor"
    assert blocks[0].effective_metadata()["tempo"] == "120"


def test_parse_multiple_blocks():
    markdown = """::: vsa-notatie
{een}
:::

tekst

::: vsa-notatie
{twee}
:::
"""

    blocks = parse_markdown_blocks(markdown)

    assert len(blocks) == 2
    assert blocks[0].body == "{een}"
    assert blocks[1].body == "{twee}"


def test_parse_block_with_dotted_hash_metadata():
    markdown = """::: vsa-notatie
# identificatie.title: Tropaar
# do: G4

[\\:] {/tekst_}
:::
"""

    block = parse_markdown_blocks(markdown)[0]

    assert block.metadata["identificatie.title"] == "Tropaar"
    assert block.metadata["do"] == "G4"
    assert block.body.startswith("[\\:]")
    assert "identificatie.title" not in block.body
    markdown = """::: vsa-notatie
{/tekst_}
:::
"""

    block = parse_markdown_blocks(markdown)[0]
    ast = block.parse_body().to_dict()

    assert ast["nodes"][0]["type"] == "ScopeNode"
    assert ast["nodes"][0]["height_modifier"] == ["/"]
    assert ast["nodes"][0]["length_modifier"] == ["_"]
