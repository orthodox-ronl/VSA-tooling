"""Tests voor @include-vsa expand (``id:`` op de bibliotheek-mappenstructuur)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.include_vsa import (
    IncludeVsaError,
    discover_content_root,
    prepare_vsa_body,
)
from vsa.validation_runner import validate_file

HEMELUM_VSA = "[:] {/Hei_}{/lig_} Door de Moeder Gods. [:]\n"
HEMELUM_ID = "antifoon-1-weekdagen/liturgikon-weekdagen/hemelum"


def _write_vsa(root: Path, catalogus_id: str, name: str, body: str) -> Path:
    """Schrijf ``content-source/catalogus/<id>/<name>.vsa`` (zoals in bibliotheek)."""
    folder = root / "catalogus" / catalogus_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.vsa"
    path.write_text(body, encoding="utf-8")
    return path


def test_discover_content_root_from_relative_name_in_nested_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "content-source"
    nested = content / "praktijk" / "samenstellingen"
    nested.mkdir(parents=True)
    (content / "catalogus").mkdir()
    (nested / "page.md").write_text("# x\n", encoding="utf-8")
    monkeypatch.chdir(nested)
    assert discover_content_root(Path("page.md")) == content.resolve()


def test_expand_id_partial_line(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(root, HEMELUM_ID, "antifoon-1-weekdagen-hemelum", HEMELUM_VSA)

    host = root / "host.vsa"
    host.write_text(f"refrein: @include-vsa id={HEMELUM_ID}\n", encoding="utf-8")

    expanded, warnings = prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert "@include-vsa" not in expanded
    assert expanded.startswith("refrein:")
    assert "{/Hei_}" in expanded
    assert warnings == []
    assert "refrein: refrein:" not in expanded


def test_expand_trims_included_body_blank_lines(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(root, "stuk-a/variant-a/uv-a", "a", "\n\n[:] tekst [//:]\n\n")

    host = root / "host.vsa"
    host.write_text("@include-vsa id=stuk-a/variant-a/uv-a\n", encoding="utf-8")

    expanded, _ = prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert expanded.strip() == "[:] tekst [//:]"


def test_expand_cycle_detection(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    vsa = _write_vsa(root, "a/b/c", "x", "@include-vsa id=a/b/c\n")

    with pytest.raises(IncludeVsaError, match="Cyclische"):
        prepare_vsa_body(vsa.read_text(encoding="utf-8"), vsa)


def test_zoek_is_niet_meer_ondersteund(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    (root / "catalogus").mkdir(parents=True)
    host = root / "host.vsa"
    host.write_text(
        '@include-vsa zoek="Cherubijnenhymne (Kastorski)"\n',
        encoding="utf-8",
    )

    with pytest.raises(IncludeVsaError, match="zoek= wordt niet meer ondersteund"):
        prepare_vsa_body(host.read_text(encoding="utf-8"), host)


def test_lokaal_is_niet_meer_ondersteund(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(root, HEMELUM_ID, "hemelum", HEMELUM_VSA)
    host = root / "host.vsa"
    host.write_text(f"@include-vsa lokaal={HEMELUM_ID}\n", encoding="utf-8")

    with pytest.raises(IncludeVsaError, match="lokaal= wordt niet meer ondersteund"):
        prepare_vsa_body(host.read_text(encoding="utf-8"), host)


def test_id_niet_gevonden(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    (root / "catalogus").mkdir(parents=True)
    host = root / "host.vsa"
    host.write_text("@include-vsa id=bestaat/niet/hier\n", encoding="utf-8")

    with pytest.raises(IncludeVsaError):
        prepare_vsa_body(host.read_text(encoding="utf-8"), host)


def test_id_niet_uniek(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(root, "stuk/variant/uv", "een", HEMELUM_VSA)
    _write_vsa(root, "stuk/variant/uv", "twee", HEMELUM_VSA)
    host = root / "host.vsa"
    host.write_text("@include-vsa id=stuk/variant/uv\n", encoding="utf-8")

    with pytest.raises(IncludeVsaError, match="niet uniek"):
        prepare_vsa_body(host.read_text(encoding="utf-8"), host)


def test_source_file_unchanged_after_expand(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(root, HEMELUM_ID, "hemelum", HEMELUM_VSA)
    host = root / "host.vsa"
    original = f"refrein: @include-vsa id={HEMELUM_ID}\n"
    host.write_text(original, encoding="utf-8")

    prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert host.read_text(encoding="utf-8") == original


def test_validate_expanded_antifoon(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_vsa(
        root,
        "troparion-geboorte-moeder-gods/obikhod/groningen",
        "groningen",
        "[:] re-frein me-lo-die [:]\n",
    )
    antifoon = _write_vsa(
        root,
        "antifoon-3-geboorte/liturgikon/groningen",
        "antifoon",
        "[:] Cou-plet een. [:]\n\n"
        "re-frein: @include-vsa id=troparion-geboorte-moeder-gods/obikhod/groningen\n\n"
        "[:] Cou-plet twee. [:]\n",
    )

    result = validate_file(antifoon)
    assert result.ok, [m.message_nl for m in result.messages if m.severity == "error"]

    expanded, _ = prepare_vsa_body(antifoon.read_text(encoding="utf-8"), antifoon)
    assert "re-frein me-lo-die" in expanded
    assert "@include-vsa" not in expanded
    assert expanded.index("re-frein:") < expanded.index("re-frein me-lo-die")
