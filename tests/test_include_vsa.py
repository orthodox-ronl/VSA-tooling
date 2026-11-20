"""Tests voor @include-vsa expand."""

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
VARIANT_YAML = """\
zangstuk-id: antifoon-1-weekdagen
variant-id: liturgikon-weekdagen
title: "1e antifoon weekdagen"
"""

UV_YAML = """\
uitvoeringsvorm-id: hemelum
representaties:
  - representatie-id: hemelum
    file: repr/hemelum.vsa
"""


def _write_lokaal_tree(root: Path) -> None:
    base = root / "lokaal/antifoon-1-weekdagen/liturgikon-weekdagen"
    (base / "hemelum/repr").mkdir(parents=True)
    (base / "variant.yaml").write_text(VARIANT_YAML, encoding="utf-8")
    (base / "hemelum/uitvoeringsvorm.yaml").write_text(UV_YAML, encoding="utf-8")
    (base / "hemelum/repr/hemelum.vsa").write_text(HEMELUM_VSA, encoding="utf-8")


def test_discover_content_root_from_relative_name_in_nested_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "content-source"
    nested = content / "praktijk" / "samenstellingen"
    nested.mkdir(parents=True)
    (content / "lokaal").mkdir()
    (nested / "page.md").write_text("# x\n", encoding="utf-8")
    monkeypatch.chdir(nested)
    assert discover_content_root(Path("page.md")) == content.resolve()


TROPARION_BODY = "[:] refrein melodie [:]\n"


def test_expand_lokaal_partial_line(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_lokaal_tree(root)

    antifoon = root / "lokaal/antifoon-demo/antifoon.vsa"
    antifoon.parent.mkdir(parents=True)
    antifoon.write_text(
        "refrein: @include-vsa lokaal=antifoon-1-weekdagen/liturgikon-weekdagen/hemelum\n",
        encoding="utf-8",
    )

    expanded, warnings = prepare_vsa_body(antifoon.read_text(encoding="utf-8"), antifoon)

    assert "@include-vsa" not in expanded
    assert expanded.startswith("refrein:")
    assert "{/Hei_}" in expanded
    assert warnings == []
    assert "refrein: refrein:" not in expanded


def test_expand_id_parameter(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_lokaal_tree(root)

    host = root / "host.vsa"
    host.write_text(
        "@include-vsa id=antifoon-1-weekdagen/liturgikon-weekdagen/Hemelum\n",
        encoding="utf-8",
    )

    expanded, _ = prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert "@include-vsa" not in expanded
    assert "{/Hei_}" in expanded


def test_expand_trims_included_body_blank_lines(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    base = root / "lokaal/stuk-a/variant-a/uv-a/repr"
    base.mkdir(parents=True)
    (root / "lokaal/stuk-a/variant-a/variant.yaml").write_text(
        "zangstuk-id: stuk-a\nvariant-id: variant-a\n",
        encoding="utf-8",
    )
    (root / "lokaal/stuk-a/variant-a/uv-a/uitvoeringsvorm.yaml").write_text(
        "uitvoeringsvorm-id: uv-a\nrepresentaties:\n"
        "  - representatie-id: repr-a\n    file: repr/a.vsa\n",
        encoding="utf-8",
    )
    (base / "a.vsa").write_text("\n\n[:] tekst [//:]\n\n", encoding="utf-8")

    host = root / "host.vsa"
    host.write_text("@include-vsa lokaal=stuk-a/variant-a/uv-a\n", encoding="utf-8")

    expanded, _ = prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert expanded.strip() == "[:] tekst [//:]"


def test_expand_cycle_detection(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    lokaal = root / "lokaal/a/b/c/repr"
    lokaal.mkdir(parents=True)
    (root / "lokaal/a/b/variant.yaml").write_text(
        "zangstuk-id: a\nvariant-id: b\n",
        encoding="utf-8",
    )
    (root / "lokaal/a/b/c/uitvoeringsvorm.yaml").write_text(
        "uitvoeringsvorm-id: c\nrepresentaties:\n"
        "  - representatie-id: x\n    file: repr/x.vsa\n",
        encoding="utf-8",
    )
    vsa = lokaal / "x.vsa"
    vsa.write_text("@include-vsa lokaal=a/b/c\n", encoding="utf-8")

    with pytest.raises(IncludeVsaError, match="Cyclische"):
        prepare_vsa_body(vsa.read_text(encoding="utf-8"), vsa)


def test_zoek_is_niet_meer_ondersteund(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    (root / "lokaal").mkdir(parents=True)
    host = root / "host.vsa"
    host.write_text(
        '@include-vsa zoek="Cherubijnenhymne (Kastorski)"\n',
        encoding="utf-8",
    )

    with pytest.raises(IncludeVsaError, match="zoek= wordt niet meer ondersteund"):
        prepare_vsa_body(host.read_text(encoding="utf-8"), host)


def test_source_file_unchanged_after_expand(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_lokaal_tree(root)
    host = root / "host.vsa"
    original = "refrein: @include-vsa lokaal=antifoon-1-weekdagen/liturgikon-weekdagen/hemelum\n"
    host.write_text(original, encoding="utf-8")

    prepare_vsa_body(host.read_text(encoding="utf-8"), host)

    assert host.read_text(encoding="utf-8") == original


def test_validate_expanded_antifoon(tmp_path: Path) -> None:
    root = tmp_path / "content-source"
    _write_lokaal_tree(root)

    troparion_dir = root / "lokaal/troparion-geboorte-moeder-gods/obikhod/groningen/repr"
    troparion_dir.mkdir(parents=True)
    (root / "lokaal/troparion-geboorte-moeder-gods/obikhod/groningen/variant.yaml").write_text(
        "zangstuk-id: troparion-geboorte-moeder-gods\nvariant-id: obikhod\n",
        encoding="utf-8",
    )
    (root / "lokaal/troparion-geboorte-moeder-gods/obikhod/groningen/uitvoeringsvorm.yaml").write_text(
        "uitvoeringsvorm-id: groningen\nrepresentaties:\n"
        "  - representatie-id: groningen\n    file: repr/groningen.vsa\n",
        encoding="utf-8",
    )
    (troparion_dir / "groningen.vsa").write_text(TROPARION_BODY, encoding="utf-8")

    antifoon = root / "lokaal/antifoon-3-geboorte/liturgikon/groningen/repr/antifoon.vsa"
    antifoon.parent.mkdir(parents=True)
    (root / "lokaal/antifoon-3-geboorte/liturgikon/groningen/variant.yaml").write_text(
        "zangstuk-id: antifoon-3-geboorte\nvariant-id: liturgikon\n",
        encoding="utf-8",
    )
    (root / "lokaal/antifoon-3-geboorte/liturgikon/groningen/uitvoeringsvorm.yaml").write_text(
        "uitvoeringsvorm-id: groningen\nrepresentaties:\n"
        "  - representatie-id: groningen\n    file: repr/antifoon.vsa\n",
        encoding="utf-8",
    )
    antifoon.write_text(
        "[:] Couplet een. [:]\n\n"
        "refrein: @include-vsa lokaal=troparion-geboorte-moeder-gods/obikhod/groningen\n\n"
        "[:] Couplet twee. [:]\n",
        encoding="utf-8",
    )

    result = validate_file(antifoon)
    assert result.ok, [m.message_nl for m in result.messages if m.severity == "error"]

    expanded, _ = prepare_vsa_body(antifoon.read_text(encoding="utf-8"), antifoon)
    assert "refrein melodie" in expanded
    assert "@include-vsa" not in expanded
    assert expanded.index("refrein:") < expanded.index("refrein melodie")
