"""Regression: ``….translit.svg`` mag ``….translit-nls/ksl.svg`` niet wissen."""

from __future__ import annotations

from pathlib import Path

from vsa.musescore_cli import list_musescore_svg_pages


def test_translit_beide_page_glob_skips_nls_ksl(tmp_path: Path) -> None:
    dest = tmp_path / "lied.mvsa.translit.svg"
    dest.write_text("<svg/>", encoding="utf-8")
    page = tmp_path / "lied.mvsa.translit-1.svg"
    page.write_text("<svg>1</svg>", encoding="utf-8")
    (tmp_path / "lied.mvsa.translit-nls.svg").write_text("<svg>n</svg>", encoding="utf-8")
    (tmp_path / "lied.mvsa.translit-ksl.svg").write_text("<svg>k</svg>", encoding="utf-8")
    pages = list_musescore_svg_pages(dest)
    assert [p.name for p in pages] == ["lied.mvsa.translit-1.svg"]
