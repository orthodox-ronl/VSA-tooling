import pytest
from pathlib import Path

from vsa.markdown_include import IncludeError, _relative_static_vsa_href, resolve_includes


def test_passthrough_when_no_includes(tmp_path):
    source = tmp_path / "doc.md"
    source.write_text("# Titel\n\nGewone tekst.\n", encoding="utf-8")

    result = resolve_includes("# Titel\n\nGewone tekst.\n", source)

    assert result == "# Titel\n\nGewone tekst.\n"


def test_include_markdown(tmp_path):
    included = tmp_path / "fragment.md"
    included.write_text("Ingevoegde tekst.\n", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = "Voor.\n:::include fragment.md:::\nNa.\n"

    result = resolve_includes(text, source)

    assert "Ingevoegde tekst." in result
    assert ":::include" not in result
    assert "Voor." in result
    assert "Na." in result


def test_include_vsa_without_alt(tmp_path):
    vsa_file = tmp_path / "melodie.vsa"
    vsa_file.write_text("[:] {/Hei_} is de Heer. [//:]", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ":::include melodie.vsa:::\n"

    result = resolve_includes(text, source)

    assert "::: vsa-notatie" in result
    assert "{/Hei_}" in result
    assert "# alt:" not in result
    assert ":::include" not in result


def test_include_vsa_with_alt(tmp_path):
    vsa_file = tmp_path / "melodie.vsa"
    vsa_file.write_text("[:] {/Hei_} is de Heer. [//:]", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ':::include "melodie.vsa" alt="Tropaar, toon 1":::\n'

    result = resolve_includes(text, source)

    assert "::: vsa-notatie" in result
    assert '# alt: Tropaar, toon 1' in result
    assert "{/Hei_}" in result


def test_include_vsa_strips_yaml_frontmatter(tmp_path):
    vsa_file = tmp_path / "melodie.vsa"
    vsa_file.write_text(
        "---\n"
        "muziek:\n"
        "  do: G4\n"
        "  mode: minor\n"
        "identificatie:\n"
        "  title: Test\n"
        "---\n"
        "\n"
        "[:] {/Hei_} is de Heer. [//:]",
        encoding="utf-8",
    )

    source = tmp_path / "doc.md"
    result = resolve_includes(':::include "melodie.vsa":::\n', source)

    assert "identificatie:" not in result
    assert "---" not in result
    assert "# do: G4" in result
    assert "# identificatie.title: Test" in result
    assert "{/Hei_}" in result


def test_include_svg_relative_fallback(tmp_path):
    """Without svg_assets_dir, a relative src is emitted (test/non-Hugo context)."""
    svg_file = tmp_path / "afbeelding.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ":::include afbeelding.svg:::\n"

    result = resolve_includes(text, source)

    assert 'src="afbeelding.svg"' in result
    assert 'class="vsa-notation"' in result
    assert 'alt=""' in result
    assert ":::include" not in result


def test_include_svg_with_alt_relative_fallback(tmp_path):
    svg_file = tmp_path / "afbeelding.svg"
    svg_file.write_text("<svg></svg>", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ':::include afbeelding.svg alt="Mijn afbeelding":::\n'

    result = resolve_includes(text, source)

    assert 'alt="Mijn afbeelding"' in result
    assert 'src="afbeelding.svg"' in result


def test_include_svg_copies_to_assets_dir(tmp_path):
    """With svg_assets_dir, the SVG is copied and an absolute URL is emitted."""
    content_root = tmp_path / "content-source"
    content_root.mkdir()
    sub = content_root / "dienst"
    sub.mkdir()

    svg_file = sub / "melodie.svg"
    svg_file.write_text("<svg><text>noot</text></svg>", encoding="utf-8")

    assets_dir = tmp_path / "static" / "vsa"
    assets_dir.mkdir(parents=True)

    source = sub / "pagina.md"
    text = ":::include melodie.svg:::\n"

    result = resolve_includes(
        text,
        source,
        svg_assets_dir=assets_dir,
        svg_assets_url_prefix="/vsa",
        content_root=content_root,
    )

    assert '{{< vsa src="/vsa/dienst-melodie.svg"' in result
    assert (assets_dir / "dienst-melodie.svg").exists()
    assert (assets_dir / "dienst-melodie.svg").read_text(encoding="utf-8") == "<svg><text>noot</text></svg>"


def test_include_svg_outside_content_root_uses_stem(tmp_path):
    """SVG outside content_root falls back to stem-only filename."""
    content_root = tmp_path / "content-source"
    content_root.mkdir()
    external = tmp_path / "extern"
    external.mkdir()

    svg_file = external / "icoon.svg"
    svg_file.write_text("<svg/>", encoding="utf-8")

    assets_dir = tmp_path / "static" / "vsa"
    assets_dir.mkdir(parents=True)

    source = content_root / "pagina.md"
    text = ":::include ../extern/icoon.svg:::\n"

    result = resolve_includes(
        text,
        source,
        svg_assets_dir=assets_dir,
        svg_assets_url_prefix="/vsa",
        content_root=content_root,
    )

    assert '{{< vsa src="/vsa/icoon.svg"' in result
    assert (assets_dir / "icoon.svg").exists()


def test_include_raster_image_copies_to_assets_dir(tmp_path):
    """JPG/PNG are copied to assets_dir with an absolute URL."""
    content_root = tmp_path / "content-source"
    content_root.mkdir()
    sub = content_root / "praktijk"
    sub.mkdir()

    jpg_file = sub / "tropaarmelodie-toon-1.jpg"
    jpg_file.write_bytes(b"\xff\xd8\xff")  # minimal JPEG header

    assets_dir = tmp_path / "static" / "vsa"
    assets_dir.mkdir(parents=True)

    source = sub / "pagina.md"
    text = ':::include "tropaarmelodie-toon-1.jpg" alt="Tropaarmelodie (Toon 1)":::\n'

    result = resolve_includes(
        text,
        source,
        svg_assets_dir=assets_dir,
        svg_assets_url_prefix="/vsa",
        content_root=content_root,
    )

    assert '{{< vsa src="/vsa/praktijk-tropaarmelodie-toon-1.jpg"' in result
    assert 'alt="Tropaarmelodie (Toon 1)"' in result
    assert (assets_dir / "praktijk-tropaarmelodie-toon-1.jpg").exists()


def test_include_raster_without_assets_dir_relative_fallback(tmp_path):
    jpg_file = tmp_path / "foto.jpg"
    jpg_file.write_bytes(b"\xff\xd8\xff")

    source = tmp_path / "doc.md"
    text = ':::include "foto.jpg" alt="Foto":::\n'

    result = resolve_includes(text, source)

    assert 'src="foto.jpg"' in result
    assert 'alt="Foto"' in result


def test_include_scale_on_svg(tmp_path):
    svg_file = tmp_path / "noot.svg"
    svg_file.write_text('<svg width="100"></svg>', encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ':::include noot.svg scale="60%":::\n'

    result = resolve_includes(text, source)

    assert 'style="width: 60px; height: auto"' in result


def test_include_scale_on_svg_with_assets_dir_uses_shortcode(tmp_path):
    svg_file = tmp_path / "noot.svg"
    svg_file.write_text('<svg width="100"></svg>', encoding="utf-8")

    assets_dir = tmp_path / "static" / "vsa"
    assets_dir.mkdir(parents=True)

    source = tmp_path / "doc.md"
    text = ':::include noot.svg scale="60%":::\n'

    result = resolve_includes(
        text,
        source,
        svg_assets_dir=assets_dir,
        svg_assets_url_prefix="/vsa",
    )

    assert '{{< vsa src="/vsa/noot.svg"' in result
    assert 'scale="60px"' in result


def test_include_scale_on_vsa(tmp_path):
    vsa_file = tmp_path / "melodie.vsa"
    vsa_file.write_text("[:] {/Hei_} [//:]", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ':::include "melodie.vsa" scale="75%":::\n'

    result = resolve_includes(text, source)

    assert "# scale: 75%" in result


def test_include_alt_and_scale_together(tmp_path):
    jpg_file = tmp_path / "foto.jpg"
    jpg_file.write_bytes(b"\xff\xd8\xff")

    source = tmp_path / "doc.md"
    text = ':::include "foto.jpg" alt="Beschrijving" scale="80%":::\n'

    result = resolve_includes(text, source)

    assert 'src="foto.jpg"' in result
    assert 'alt="Beschrijving"' in result
    assert 'style="width: 80%; height: auto"' in result


def test_recursive_include(tmp_path):
    inner = tmp_path / "inner.md"
    inner.write_text("Binnenste tekst.\n", encoding="utf-8")

    outer = tmp_path / "outer.md"
    outer.write_text(":::include inner.md:::\n", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ":::include outer.md:::\n"

    result = resolve_includes(text, source)

    assert "Binnenste tekst." in result
    assert ":::include" not in result


def test_include_resolves_relative_to_including_file(tmp_path):
    sub = tmp_path / "hoofdstuk"
    sub.mkdir()

    melodie = sub / "melodie.md"
    melodie.write_text("Melodietekst.\n", encoding="utf-8")

    chapter = sub / "hoofdstuk.md"
    chapter.write_text(":::include melodie.md:::\n", encoding="utf-8")

    source = tmp_path / "boek.md"
    text = ":::include hoofdstuk/hoofdstuk.md:::\n"

    result = resolve_includes(text, source)

    assert "Melodietekst." in result


def test_multiple_includes_of_same_file(tmp_path):
    fragment = tmp_path / "fragment.md"
    fragment.write_text("Herhaalbaar.\n", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ":::include fragment.md:::\n:::include fragment.md:::\n"

    result = resolve_includes(text, source)

    assert result.count("Herhaalbaar.") == 2


def test_cycle_detection(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(":::include b.md:::\n", encoding="utf-8")
    b.write_text(":::include a.md:::\n", encoding="utf-8")

    with pytest.raises(IncludeError, match="Kringverwijzing"):
        resolve_includes(":::include a.md:::\n", tmp_path / "doc.md")


def test_file_not_found(tmp_path):
    source = tmp_path / "doc.md"
    text = ":::include ontbreekt.md:::\n"

    with pytest.raises(IncludeError, match="Bestand niet gevonden"):
        resolve_includes(text, source)


def test_unknown_extension(tmp_path):
    unknown = tmp_path / "data.csv"
    unknown.write_text("a,b,c", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ":::include data.csv:::\n"

    with pytest.raises(IncludeError, match="Onbekend bestandstype"):
        resolve_includes(text, source)


def test_include_path_with_spaces_quoted(tmp_path):
    """Paths with spaces must be quoted."""
    spaced = tmp_path / "mijn bestand.md"
    spaced.write_text("Tekst met spaties.\n", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = ':::include "mijn bestand.md":::\n'

    result = resolve_includes(text, source)

    assert "Tekst met spaties." in result
    assert ":::include" not in result


def test_include_path_with_spaces_unquoted_raises(tmp_path):
    """An unquoted path with spaces is parsed incorrectly (first token only),
    resulting in a 'Bestand niet gevonden' error. Use quotes instead."""
    source = tmp_path / "doc.md"
    text = ":::include mijn bestand.md:::\n"

    with pytest.raises(IncludeError, match="Bestand niet gevonden"):
        resolve_includes(text, source)


def test_include_inside_code_fence_is_ignored(tmp_path):
    fragment = tmp_path / "fragment.md"
    fragment.write_text("Mag niet verschijnen.\n", encoding="utf-8")

    source = tmp_path / "doc.md"
    text = "```\n:::include fragment.md:::\n```\n"

    result = resolve_includes(text, source)

    assert ":::include fragment.md:::" in result
    assert "Mag niet verschijnen." not in result


def test_include_svg_export_equivalent_to_plain_vsa(tmp_path):
    vsa_file = tmp_path / "melodie.vsa"
    vsa_file.write_text("[:] {/Hei_} is de Heer. [//:]", encoding="utf-8")
    source = tmp_path / "doc.md"

    plain = resolve_includes(':::include "melodie.vsa" alt="Test":::\n', source)
    explicit = resolve_includes(
        ':::include svg "melodie.vsa" alt="Test":::\n', source
    )
    assert plain == explicit


def test_include_coria_with_html_sibling(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    vsa = md_dir / "melodie.vsa"
    vsa.write_text("{/a_}", encoding="utf-8")
    vsa.with_name("melodie.coria.html").write_text("<html></html>", encoding="utf-8")
    md = md_dir / "page.md"
    md.write_text(':::include coria "melodie.vsa" label="Oefenen":::\n', encoding="utf-8")

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'coria-html src="/coria/praktijk/melodie.html"' in result
    assert 'label="Oefenen"' in result


def test_include_coria_falls_back_to_mxl(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    vsa = md_dir / "melodie.vsa"
    vsa.write_text("{/a_}", encoding="utf-8")
    md = md_dir / "page.md"
    md.write_text(':::include coria "melodie.vsa":::\n', encoding="utf-8")

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'coria src="/vsa/mxl/praktijk/melodie.mxl"' in result
    assert "coria-html" not in result


def test_include_mxl_download(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    vsa = md_dir / "melodie.vsa"
    vsa.write_text("{/a_}", encoding="utf-8")
    md = md_dir / "page.md"
    md.write_text(':::include mxl "melodie.vsa" label="MXL":::\n', encoding="utf-8")

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'mxl-download src="/vsa/mxl/praktijk/melodie.mxl"' in result
    assert 'label="MXL"' in result


def test_include_coria_native_mxl(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk" / "corpus"
    md_dir.mkdir(parents=True)
    mxl = md_dir / "T4-11-nicolaas-van-myra.mxl"
    mxl.write_bytes(b"PK\x03\x04")
    md = md_dir / "page.md"
    md.write_text(
        ':::include coria "T4-11-nicolaas-van-myra.mxl" label="Oefenen":::\n',
        encoding="utf-8",
    )

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert (
        'coria src="/mxl/praktijk/corpus/T4-11-nicolaas-van-myra.mxl"' in result
    )
    assert "coria-html" not in result
    assert "/vsa/mxl/" not in result


def test_include_mxl_native_musicxml_download(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    score = md_dir / "uitgebreid.musicxml"
    score.write_text("<score-partwise/>", encoding="utf-8")
    md = md_dir / "page.md"
    md.write_text(
        ':::include mxl "uitgebreid.musicxml" label="Download":::\n',
        encoding="utf-8",
    )

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'mxl-download src="/mxl/praktijk/uitgebreid.musicxml"' in result


def test_include_coria_native_mxl_html_sibling(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    mxl = md_dir / "melodie.mxl"
    mxl.write_bytes(b"PK\x03\x04")
    mxl.with_name("melodie.coria.html").write_text("<html></html>", encoding="utf-8")
    md = md_dir / "page.md"
    md.write_text(':::include coria "melodie.mxl":::\n', encoding="utf-8")

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'coria-html src="/coria/praktijk/melodie.html"' in result


def test_include_coria_vsa_and_native_mxl_distinct_urls(tmp_path):
    content = tmp_path / "content"
    md_dir = content / "praktijk"
    md_dir.mkdir(parents=True)
    (md_dir / "melodie.vsa").write_text("{/a_}", encoding="utf-8")
    (md_dir / "melodie.mxl").write_bytes(b"PK\x03\x04")
    md = md_dir / "page.md"
    md.write_text(
        ':::include coria "melodie.vsa":::\n:::include coria "melodie.mxl":::\n',
        encoding="utf-8",
    )

    result = resolve_includes(
        md.read_text(encoding="utf-8"),
        md,
        content_root=content,
    )

    assert 'coria src="/vsa/mxl/praktijk/melodie.mxl"' in result
    assert 'coria src="/mxl/praktijk/melodie.mxl"' in result


def test_plain_include_mxl_raises(tmp_path):
    mxl = tmp_path / "melodie.mxl"
    mxl.write_bytes(b"PK\x03\x04")
    source = tmp_path / "doc.md"
    with pytest.raises(IncludeError, match="Onbekend bestandstype"):
        resolve_includes(':::include "melodie.mxl":::\n', source)


def test_include_svg_with_mxl_raises(tmp_path):
    mxl = tmp_path / "melodie.mxl"
    mxl.write_bytes(b"PK\x03\x04")
    source = tmp_path / "doc.md"
    with pytest.raises(IncludeError, match="verwacht een .vsa-bron"):
        resolve_includes(':::include svg "melodie.mxl":::\n', source)


def test_include_unknown_exporttype_raises(tmp_path):
    source = tmp_path / "doc.md"
    with pytest.raises(IncludeError, match="Onbekend exporttype"):
        resolve_includes(':::include foo "melodie.vsa":::\n', source)


def test_include_exporttype_with_md_raises(tmp_path):
    included = tmp_path / "fragment.md"
    included.write_text("Tekst.\n", encoding="utf-8")
    source = tmp_path / "doc.md"
    with pytest.raises(IncludeError, match="verwacht een .vsa-bron"):
        resolve_includes(':::include svg "fragment.md":::\n', source)


def test_include_coria_requires_content_root(tmp_path):
    vsa = tmp_path / "melodie.vsa"
    vsa.write_text("{/a_}", encoding="utf-8")
    source = tmp_path / "doc.md"
    with pytest.raises(IncludeError, match="content_root"):
        resolve_includes(':::include coria "melodie.vsa":::\n', source)


def test_include_bron_pdf_logical_reference(tmp_path: Path):
    bron_root = tmp_path / "bron"
    zangstuk_dir = bron_root / "zangstukken" / "antifoon-1-zondag"
    scan = zangstuk_dir / "sources" / "scan" / "koormap-003.pdf"
    scan.parent.mkdir(parents=True)
    scan.write_bytes(b"%PDF-1.4 test")
    (zangstuk_dir / "zangstuk.yaml").write_text(
        "id: antifoon-1-zondag\n"
        "title: 1e antifoon (zondag)\n"
        "sources:\n"
        "  - id: groningen\n"
        "    file: sources/scan/koormap-003.pdf\n",
        encoding="utf-8",
    )
    content_root = tmp_path / "content-source"
    page_dir = content_root / "praktijk" / "zondagen"
    page_dir.mkdir(parents=True)
    source = page_dir / "demo.md"
    assets = tmp_path / "static" / "vsa"
    result = resolve_includes(
        ':::include bron:antifoon-1-zondag/groningen alt="scan":::\n',
        source,
        content_root=content_root,
        bron_root=bron_root,
        svg_assets_dir=assets,
    )
    assert 'class="scan-pdf"' in result
    assert (assets / "koormap-003.pdf").is_file()
    assert 'src="../../../vsa/koormap-003.pdf"' in result


def test_relative_static_vsa_href_with_relative_source_path(tmp_path: Path):
    content_root = tmp_path / "content-source"
    page_dir = content_root / "praktijk" / "zondagen"
    page_dir.mkdir(parents=True)
    source = page_dir / "demo.md"
    href = _relative_static_vsa_href(source, content_root, "koormap-003.pdf")
    assert href == "../../../vsa/koormap-003.pdf"


def test_relative_static_vsa_href_for_section_index(tmp_path: Path):
    content_root = tmp_path / "content-source"
    section = content_root / "praktijk" / "zondagen"
    section.mkdir(parents=True)
    source = section / "_index.md"
    href = _relative_static_vsa_href(source, content_root, "koormap-003.pdf")
    assert href == "../../vsa/koormap-003.pdf"
