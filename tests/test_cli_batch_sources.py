"""CLI batch: map → meerdere bronnen; -o alleen bij één bestand."""

from pathlib import Path

from vsa.cli import main
from vsa.cli_mscz import main as mscz_main
from vsa.cli_mxl import main as mxl_main

_MINIMAL_MUSICXML = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration>
        <type>whole</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def _minimal_mvsa(path: Path, title: str) -> None:
    path.write_text(
        f'@title "{title}"\n'
        "@do F4\n"
        "@mode major\n"
        "@sectie a\n"
        "L: a_ |\n"
        "S: do |\n"
        "A: do |\n"
        "T: do |\n"
        "B: do |\n",
        encoding="utf-8",
        newline="\n",
    )


def _minimal_musicxml(path: Path) -> None:
    path.write_text(_MINIMAL_MUSICXML, encoding="utf-8", newline="\n")



def test_mvsa_normalize_directory(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_mvsa(d / "one.mvsa", "One")
    _minimal_mvsa(d / "two.mvsa", "Two")
    rc = main(["mvsa", "normalize", str(d)])
    assert rc == 0
    assert (d / "one.normalized.mvsa").is_file()
    assert (d / "two.normalized.mvsa").is_file()
    out = capsys.readouterr().out
    assert "Geschreven:" in out


def test_mvsa_normalize_dir_rejects_output_flag(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_mvsa(d / "one.mvsa", "One")
    _minimal_mvsa(d / "two.mvsa", "Two")
    rc = main(["mvsa", "normalize", str(d), "-o", str(tmp_path / "out.mvsa")])
    assert rc == 1
    err = capsys.readouterr().err
    assert "-o/--output" in err


def test_mvsa_svg_dir_rejected_wrong_empty(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "empty"
    d.mkdir()
    rc = main(["mvsa", "svg", str(d)])
    assert rc == 1
    assert "Geen passende" in capsys.readouterr().err


def test_mxl_validate_empty_dir(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "empty"
    d.mkdir()
    rc = mxl_main(["validate", str(d)])
    assert rc == 1
    assert "Geen passende" in capsys.readouterr().err


def test_mxl_normalize_directory(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_musicxml(d / "one.musicxml")
    _minimal_musicxml(d / "two.musicxml")
    rc = mxl_main(["normalize", str(d)])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("Geschreven:") == 2


def test_mxl_normalize_dir_rejects_output_flag(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_musicxml(d / "one.musicxml")
    _minimal_musicxml(d / "two.musicxml")
    rc = mxl_main(["normalize", str(d), "-o", str(tmp_path / "out.mxl")])
    assert rc == 1
    assert "-o/--output" in capsys.readouterr().err


def test_mscz_mxl_empty_dir(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "empty"
    d.mkdir()
    rc = mscz_main(["mxl", str(d)])
    assert rc == 1
    assert "Geen passende" in capsys.readouterr().err


def _minimal_vsa(path: Path, words: str) -> None:
    path.write_text(
        "---\ntitle: t\n---\n\n"
        f"{words}\n"
        "do re mi\n",
        encoding="utf-8",
        newline="\n",
    )


def test_vsa_text_directory(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_vsa(d / "one.vsa", "Amen")
    _minimal_vsa(d / "two.vsa", "Heer")
    rc = main(["text", str(d)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== " in out
    assert "one.vsa" in out
    assert "two.vsa" in out


def test_vsa_text_dir_rejects_output_flag(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_vsa(d / "one.vsa", "Amen")
    _minimal_vsa(d / "two.vsa", "Heer")
    rc = main(["text", str(d), "-o", str(tmp_path / "out.txt")])
    assert rc == 1
    assert "-o/--output" in capsys.readouterr().err


def test_vsa_audio_empty_dir(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "empty"
    d.mkdir()
    rc = main(["audio", str(d), str(tmp_path / "out")])
    assert rc == 1
    assert "Geen passende" in capsys.readouterr().err


def test_vsa_audio_dir_rejects_keep_mxl(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_vsa(d / "one.vsa", "Amen")
    _minimal_vsa(d / "two.vsa", "Heer")
    rc = main(
        [
            "audio",
            str(d),
            str(tmp_path / "out"),
            "--keep-mxl",
            str(tmp_path / "keep.mxl"),
        ]
    )
    assert rc == 1
    assert "--keep-mxl" in capsys.readouterr().err


def test_vsa_svg_directory(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "batch"
    d.mkdir()
    _minimal_vsa(d / "one.vsa", "Amen")
    _minimal_vsa(d / "two.vsa", "Heer")
    out_dir = tmp_path / "svg-out"
    rc = main(["svg", str(d), str(out_dir)])
    assert rc == 0
    assert (out_dir / "one.vsa.svg").is_file()
    assert (out_dir / "two.vsa.svg").is_file()
    out = capsys.readouterr().out
    assert out.count("SVG geschreven naar:") == 2


def test_vsa_svg_empty_dir(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "empty"
    d.mkdir()
    rc = main(["svg", str(d), str(tmp_path / "out")])
    assert rc == 1
    assert "Geen passende" in capsys.readouterr().err
