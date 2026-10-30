from pathlib import Path

from vsa.markdown_builder import build_markdown_site


def test_build_markdown_default_generates_img_output(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assets_dir = tmp_path / "assets"

    input_dir.mkdir()

    (input_dir / "demo.md").write_text(
        """# Demo

::: vsa-notatie
{tekst}
:::
""",
        encoding="utf-8",
    )

    build_markdown_site(input_dir, output_dir, assets_dir)

    content = (output_dir / "demo.md").read_text(encoding="utf-8")

    assert '<img class="vsa-notation"' in content
    assert 'src="/vsa/demo-block-1.svg"' in content


def test_build_markdown_generates_shortcode_output_when_requested(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assets_dir = tmp_path / "assets"

    input_dir.mkdir()

    (input_dir / "demo.md").write_text(
        """# Demo

::: vsa-notatie
{tekst}
:::
""",
        encoding="utf-8",
    )

    build_markdown_site(
        input_dir,
        output_dir,
        assets_dir,
        output_mode="shortcode",
    )

    content = (output_dir / "demo.md").read_text(encoding="utf-8")

    assert '{{< vsa src="/vsa/demo-block-1.svg" alt="VSA notatie"' in content
    assert "var(--vsa-size, 1.25)" in content


def test_build_markdown_generates_img_output_when_requested(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assets_dir = tmp_path / "assets"

    input_dir.mkdir()

    (input_dir / "demo.md").write_text(
        """::: vsa-notatie
{tekst}
:::
""",
        encoding="utf-8",
    )

    build_markdown_site(
        input_dir,
        output_dir,
        assets_dir,
        output_mode="img",
    )

    content = (output_dir / "demo.md").read_text(encoding="utf-8")

    assert "<img" in content
