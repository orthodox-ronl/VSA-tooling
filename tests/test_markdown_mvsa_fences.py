"""Markdown fences: ::: vsa / ::: mvsa(-notatie) in parse, validate, build."""

from __future__ import annotations

from pathlib import Path

from vsa.block_parser import parse_markdown_blocks
from vsa.markdown_builder import build_markdown_site
from vsa.markdown_include import resolve_includes
from vsa.validation_runner import validate_file

_MINIMAL_MVSA = """\
@do F4
@mode major
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""


def test_parse_vsa_alias_fence():
    markdown = """::: vsa
[:] {tekst} [:]
:::
"""
    blocks = parse_markdown_blocks(markdown)
    assert len(blocks) == 1
    assert blocks[0].kind == "vsa"
    assert blocks[0].info_string == "vsa"
    assert blocks[0].body == "[:] {tekst} [:]"


def test_parse_mvsa_notatie_and_alias():
    for fence in ("mvsa-notatie", "mvsa"):
        markdown = f"::: {fence}\n{_MINIMAL_MVSA}:::\n"
        blocks = parse_markdown_blocks(markdown)
        assert len(blocks) == 1
        assert blocks[0].kind == "mvsa"
        assert blocks[0].info_string == fence
        assert "@do F4" in blocks[0].body
        assert "# Alleluia" not in blocks[0].body or True


def test_mvsa_block_keeps_hash_comments():
    markdown = """::: mvsa
# commentaarregel
@do F4
@mode major
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
:::
"""
    blocks = parse_markdown_blocks(markdown)
    assert blocks[0].kind == "mvsa"
    assert "# commentaarregel" in blocks[0].body
    assert blocks[0].metadata == {}


def test_mvsa_block_assignment_metadata_only():
    markdown = """::: mvsa-notatie
alt="Proef"
label="Coria"
@do F4
@mode major
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
:::
"""
    blocks = parse_markdown_blocks(markdown)
    assert blocks[0].metadata["alt"] == "Proef"
    assert blocks[0].metadata["label"] == "Coria"
    assert "@do F4" in blocks[0].body


def test_validate_vsa_alias_and_mvsa_block(tmp_path: Path):
    md = tmp_path / "mix.md"
    md.write_text(
        f"""# Mix

::: vsa
[:] {{tekst}} [:]
:::

::: mvsa
{_MINIMAL_MVSA}:::
""",
        encoding="utf-8",
    )
    result = validate_file(md)
    assert result.ok, [m.message_nl for m in result.messages]


def test_validate_mvsa_block_reports_errors(tmp_path: Path):
    md = tmp_path / "bad.md"
    md.write_text(
        """::: mvsa
@do NOT-A-PITCH
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
:::
""",
        encoding="utf-8",
    )
    result = validate_file(md)
    assert not result.ok
    assert any(m.code.startswith("MVSA-") for m in result.messages)


def test_build_markdown_rewrites_mvsa_to_shortcodes(tmp_path: Path):
    input_dir = tmp_path / "content"
    input_dir.mkdir()
    (input_dir / "lied.md").write_text(
        f"""# Lied

::: mvsa-notatie
{_MINIMAL_MVSA}:::
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"
    assets_dir = tmp_path / "assets"
    result = build_markdown_site(input_dir, output_dir, assets_dir)
    rewritten = (output_dir / "lied.md").read_text(encoding="utf-8")
    assert "::: mvsa" not in rewritten
    assert "{{< coria " in rewritten
    assert "{{< mxl-download " in rewritten
    mxl_files = list(assets_dir.glob("*.mxl"))
    assert len(mxl_files) == 1
    assert str(mxl_files[0]) in result.svg_files


def test_build_markdown_vsa_alias_still_svg(tmp_path: Path):
    input_dir = tmp_path / "content"
    input_dir.mkdir()
    (input_dir / "v.md").write_text(
        """::: vsa
[:] {tekst} [:]
:::
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"
    assets_dir = tmp_path / "assets"
    build_markdown_site(input_dir, output_dir, assets_dir)
    rewritten = (output_dir / "v.md").read_text(encoding="utf-8")
    assert "::: vsa" not in rewritten
    assert '<img class="vsa-notation"' in rewritten
    assert list(assets_dir.glob("*.svg"))


def test_include_mvsa_wraps_as_fence(tmp_path: Path):
    mvsa = tmp_path / "lied.mvsa"
    mvsa.write_text(_MINIMAL_MVSA, encoding="utf-8")
    source = tmp_path / "doc.md"
    result = resolve_includes(':::include lied.mvsa alt="Alleluia":::\n', source)
    assert "::: mvsa-notatie" in result
    assert 'alt="Alleluia"' in result
    assert "@do F4" in result
    assert ":::include" not in result
