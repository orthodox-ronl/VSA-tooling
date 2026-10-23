"""Default output naming: stem.brontype.doeltype."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.derived_path import derived_output_path


@pytest.mark.parametrize(
    ("source", "doel", "expected"),
    [
        ("lied.mvsa", ".mscz", "lied.mvsa.mscz"),
        ("lied.mvsa", "mxl", "lied.mvsa.mxl"),
        ("lied.mscz", ".mxl", "lied.mscz.mxl"),
        ("lied.mxl", ".mscz", "lied.mxl.mscz"),
        ("lied.mvsa", ".pdf", "lied.mvsa.pdf"),
        ("lied.mvsa", ".mp3", "lied.mvsa.mp3"),
        ("dir/lied.mvsa", ".mscz", "dir/lied.mvsa.mscz"),
        ("lied.mscz.mxl", ".mp3", "lied.mscz.mxl.mp3"),
    ],
)
def test_derived_output_path(source: str, doel: str, expected: str) -> None:
    assert derived_output_path(Path(source), doel) == Path(expected)


def test_mvsa_mscz_default_out_appends_brontype(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text("@title \"t\"\n\n@sectie a\nL a\nS do\n", encoding="utf-8")
    captured: dict[str, Path] = {}

    def fake_export(path, out, **kwargs):  # noqa: ANN001
        captured["out"] = out
        out.write_bytes(b"PK")

    monkeypatch.setattr("vsa.mvsa_mscz.export_mvsa_to_mscz", fake_export)
    assert mvsa_main(["mscz", str(src)]) == 0
    assert captured["out"] == tmp_path / "lied.mvsa.mscz"
    assert captured["out"].is_file()


def test_mvsa_mxl_default_out_appends_brontype(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text("@title \"t\"\n\n@sectie a\nL a\nS do\n", encoding="utf-8")
    captured: dict[str, Path] = {}

    def fake_export(path, out, **kwargs):  # noqa: ANN001
        captured["out"] = out
        out.write_text("<score-partwise/>", encoding="utf-8")

    monkeypatch.setattr("vsa.mvsa_musicxml.export_mvsa_path", fake_export)
    assert mvsa_main(["mxl", str(src)]) == 0
    assert captured["out"] == tmp_path / "lied.mvsa.mxl"


def test_mscz_mxl_default_out_appends_brontype(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vsa.cli_mscz import main as mscz_main

    src = tmp_path / "lied.mscz"
    src.write_bytes(b"PK")
    captured: dict[str, Path] = {}

    def fake_export(path, out, **kwargs):  # noqa: ANN001
        captured["out"] = out
        out.write_text("<score-partwise/>", encoding="utf-8")

    monkeypatch.setattr(
        "vsa.musicxml_playback_normalize.export_mscz_to_playback_mxl",
        fake_export,
    )
    assert mscz_main(["mxl", str(src)]) == 0
    assert captured["out"] == tmp_path / "lied.mscz.mxl"


def test_mxl_mvsa_default_out_appends_brontype(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vsa.cli_mxl import main as mxl_main

    src = tmp_path / "lied.mxl"
    src.write_text(
        '<?xml version="1.0"?><score-partwise version="3.1"/>',
        encoding="utf-8",
    )
    captured: dict[str, Path] = {}

    def fake_import(path, out, **kwargs):  # noqa: ANN001
        captured["out"] = out
        out.write_text("@title \"t\"\n\n@sectie schets\nL a\nS do\n", encoding="utf-8")

    monkeypatch.setattr("vsa.mvsa_import.import_score_path", fake_import)
    assert mxl_main(["mvsa", str(src)]) == 0
    assert captured["out"] == tmp_path / "lied.mxl.mvsa"


@pytest.mark.parametrize("fmt", ["mp3", "ogg", "wav"])
def test_mvsa_audio_subcommand_sets_format(
    fmt: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text("@title \"t\"\n\n@sectie a\nL a\nS do\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_export(path, out, **kwargs):  # noqa: ANN001
        captured["out"] = out
        captured["format_name"] = kwargs.get("format_name")
        out.write_bytes(b"ID3")
        return out

    monkeypatch.setattr("vsa.audio_export.export_to_audio", fake_export)
    assert mvsa_main([fmt, str(src)]) == 0
    assert captured["format_name"] == fmt
    assert captured["out"] == tmp_path / f"lied.mvsa.{fmt}"


def test_mxl_mscz_default_out_appends_brontype(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vsa.cli_mxl import main as mxl_main

    src = tmp_path / "lied.mxl"
    src.write_text(
        '<?xml version="1.0"?><score-partwise version="3.1"/>',
        encoding="utf-8",
    )
    captured: dict[str, Path] = {}

    monkeypatch.setattr(
        "vsa.mvsa_import.read_musicxml_file",
        lambda p: MagicMock(),
    )
    monkeypatch.setattr(
        "vsa.musicxml_satb_layout.ensure_partituur_musicxml",
        lambda root: root,
    )
    monkeypatch.setattr(
        "vsa.musicxml_package.write_musicxml_output",
        lambda root, path: path,
    )

    def fake_convert(src_path, out, musescore=None, **_kwargs):  # noqa: ANN001
        captured["out"] = out
        out.write_bytes(b"PK")

    monkeypatch.setattr(
        "vsa.musescore_cli.convert_with_musescore",
        fake_convert,
    )
    monkeypatch.setattr(
        "vsa.mscz_partituur.apply_partituur_mscz_conventions",
        lambda path: None,
    )
    assert mxl_main(["mscz", str(src)]) == 0
    assert captured["out"] == tmp_path / "lied.mxl.mscz"
