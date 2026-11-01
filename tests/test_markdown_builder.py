from pathlib import Path

from vsa.markdown_builder import build_markdown_site


def test_build_markdown_site_rewrites_vsa_block(tmp_path: Path):
    input_dir = tmp_path / "content-source"
    output_dir = tmp_path / "content-generated"
    assets_dir = tmp_path / "static" / "vsa"

    input_dir.mkdir()

    (input_dir / "demo.md").write_text(
        """# Demo

Voor de notatie.

::: vsa-notatie
[:] {/Hei_}{/lig_} is de Heer. [//:]
:::

Na de notatie.
""",
        encoding="utf-8",
    )

    result = build_markdown_site(input_dir, output_dir, assets_dir)

    assert len(result.markdown_files) == 1
    assert len(result.svg_files) == 1

    rewritten = (output_dir / "demo.md").read_text(encoding="utf-8")

    assert "::: vsa-notatie" not in rewritten
    assert '<img class="vsa-notation"' in rewritten
    assert 'src="/vsa/demo-block-1.svg"' in rewritten
    assert "var(--vsa-size, 1.25)" in rewritten
    assert "height: auto" in rewritten

    svg = (assets_dir / "demo-block-1.svg").read_text(encoding="utf-8")

    assert "Hei" in svg


def test_build_markdown_block_size_overrides_em_factor(tmp_path: Path):
    input_dir = tmp_path / "content-source"
    output_dir = tmp_path / "content-generated"
    assets_dir = tmp_path / "static" / "vsa"
    input_dir.mkdir()

    (input_dir / "amen.md").write_text(
        """::: vsa-notatie
size="1.0"

K: [//:] A-men [//:]
:::
""",
        encoding="utf-8",
    )

    build_markdown_site(input_dir, output_dir, assets_dir)
    rewritten = (output_dir / "amen.md").read_text(encoding="utf-8")

    assert "var(--vsa-size" not in rewritten
    assert "* 1 * 1em)" in rewritten or "* 1.0 * 1em)" in rewritten


def test_build_markdown_block_scale_wins_over_em(tmp_path: Path):
    input_dir = tmp_path / "content-source"
    output_dir = tmp_path / "content-generated"
    assets_dir = tmp_path / "static" / "vsa"
    input_dir.mkdir()

    (input_dir / "amen.md").write_text(
        """::: vsa-notatie
scale="50%"

K: [//:] A-men [//:]
:::
""",
        encoding="utf-8",
    )

    build_markdown_site(input_dir, output_dir, assets_dir)
    rewritten = (output_dir / "amen.md").read_text(encoding="utf-8")

    assert "var(--vsa-size" not in rewritten
    assert "px; height: auto" in rewritten


def test_build_markdown_site_copies_content_assets(tmp_path: Path):
    input_dir = tmp_path / "content-source"
    output_dir = tmp_path / "content-generated"
    assets_dir = tmp_path / "static" / "vsa"

    page_dir = input_dir / "liturgikon-notatie"
    page_dir.mkdir(parents=True)

    (page_dir / "index.md").write_text("# Liturgikon\n", encoding="utf-8")
    (page_dir / "liturgikon-voorbeelden.jpg").write_bytes(b"fake-jpeg")

    result = build_markdown_site(input_dir, output_dir, assets_dir)

    assert len(result.static_files) == 1
    assert (output_dir / "liturgikon-notatie" / "liturgikon-voorbeelden.jpg").read_bytes() == b"fake-jpeg"


def test_build_markdown_site_removes_stale_output_files(tmp_path: Path):
    input_dir = tmp_path / "content-source"
    output_dir = tmp_path / "content-generated"
    assets_dir = tmp_path / "static" / "vsa"
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / "current.md").write_text("# Current", encoding="utf-8")
    (output_dir / "removed.md").write_text("# Stale", encoding="utf-8")

    build_markdown_site(input_dir, output_dir, assets_dir)

    assert (output_dir / "current.md").exists()
    assert not (output_dir / "removed.md").exists()
