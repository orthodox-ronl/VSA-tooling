"""vsa mp3|ogg|wav: uniforme path [-o]-vorm; straat-puur .vsa."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vsa.cli import main as vsa_main


def _fake_export_to_audio(path, out, *, format_name="mp3", **kwargs):
    out = Path(out)
    if out.suffix.lower() not in {".mp3", ".ogg", ".wav"}:
        out = out.with_suffix(f".{format_name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"fake-audio")
    return out


def test_vsa_mp3_sibling_default(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("{tekst}", encoding="utf-8")
    with patch(
        "vsa.audio_export.export_to_audio", side_effect=_fake_export_to_audio
    ):
        assert vsa_main(["mp3", str(bron)]) == 0
    assert (tmp_path / "lied.vsa.mp3").is_file()
    assert "Geschreven:" in capsys.readouterr().out


def test_vsa_audio_alias_is_mp3(tmp_path: Path) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("{tekst}", encoding="utf-8")
    out = tmp_path / "out.mp3"
    with patch(
        "vsa.audio_export.export_to_audio", side_effect=_fake_export_to_audio
    ):
        assert vsa_main(["audio", str(bron), "-o", str(out)]) == 0
    assert out.is_file()


def test_vsa_ogg_uses_ogg_suffix(tmp_path: Path) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("{tekst}", encoding="utf-8")
    with patch(
        "vsa.audio_export.export_to_audio", side_effect=_fake_export_to_audio
    ):
        assert vsa_main(["ogg", str(bron)]) == 0
    assert (tmp_path / "lied.vsa.ogg").is_file()


def test_vsa_mp3_rejects_mvsa_with_hint(capsys, tmp_path: Path) -> None:
    mvsa = tmp_path / "lied.mvsa"
    mvsa.write_text("@do=F4\n", encoding="utf-8")
    code = vsa_main(["mp3", str(mvsa)])
    err = capsys.readouterr().err
    assert code == 1
    assert "weigert .mvsa" in err
    assert "mvsa mp3" in err
