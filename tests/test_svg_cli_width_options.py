from pathlib import Path

from vsa.svg_export import export_svg
from vsa.markdown_processor import process_markdown_file
from vsa.markdown_builder import build_markdown_site


def _height(svg: str):
    import re
    match = re.search(r'height="([0-9]+)"', svg)
    assert match
    return int(match.group(1))


def test_export_svg_max_line_width_affects_height(tmp_path: Path):
    input_file = tmp_path / "input.vsa"
    wide_svg = tmp_path / "wide.svg"
    narrow_svg = tmp_path / "narrow.svg"

    input_file.write_text(" ".join(["{tekst}"] * 40), encoding="utf-8")

    export_svg(input_file, wide_svg, max_line_width=1000)
    export_svg(input_file, narrow_svg, max_line_width=250)

    assert _height(narrow_svg.read_text(encoding="utf-8")) > _height(wide_svg.read_text(encoding="utf-8"))


def test_process_markdown_file_accepts_max_line_width(tmp_path: Path):
    input_file = tmp_path / "input.md"
    output_dir = tmp_path / "out"

    input_file.write_text(
        """::: vsa-notatie
[:] a-men a-men a-men a-men a-men a-men [:]
:::
""",
        encoding="utf-8",
    )

    result = process_markdown_file(input_file, output_dir, max_line_width=150)

    assert len(result.blocks) == 1


def test_build_markdown_site_accepts_max_line_width(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assets_dir = tmp_path / "assets"

    input_dir.mkdir()

    (input_dir / "demo.md").write_text(
        """::: vsa-notatie
[:] a-men a-men a-men a-men a-men a-men [:]
:::
""",
        encoding="utf-8",
    )

    result = build_markdown_site(
        input_dir,
        output_dir,
        assets_dir,
        max_line_width=150,
    )

    assert len(result.svg_files) == 1
