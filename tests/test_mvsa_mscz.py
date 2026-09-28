"""Tests for mvsa → MSCZ (via MuseScore CLI)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.musescore_cli import (
    MuseScoreNotFoundError,
    find_musescore,
    require_musescore,
)
from vsa.mvsa_mscz import MvsaMsczError, export_mvsa_to_mscz

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
# Schets-secties (schets3-oct-doremi, …) staan in het test-fixture.
ALLELUIA = EXAMPLES / "test-alleluia-toon-8.mvsa"
MUSESCORE = find_musescore()


def test_require_musescore_override_missing(tmp_path: Path):
    with pytest.raises(MuseScoreNotFoundError):
        require_musescore(override=tmp_path / "nope.exe")


def test_export_mscz_without_musescore_raises(tmp_path: Path):
    out = tmp_path / "out.mscz"
    with patch("vsa.mvsa_mscz.require_musescore", side_effect=MuseScoreNotFoundError("x")):
        with pytest.raises(MvsaMsczError, match="x"):
            export_mvsa_to_mscz(ALLELUIA, out, section_id="schets3-oct-doremi")


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_alleluia_section_to_mscz(tmp_path: Path):
    out = tmp_path / "alleluia.mscz"
    keep = tmp_path / "alleluia.mxl"
    export_mvsa_to_mscz(
        ALLELUIA,
        out,
        section_id="schets3-oct-doremi",
        keep_mxl=keep,
    )
    assert out.is_file()
    assert out.stat().st_size > 500
    assert keep.is_file()
    from vsa.mvsa_import import read_musicxml_file

    mxl_text = read_musicxml_file(keep)
    assert mxl_text.count('<part id="') == 2
    assert "Soprano" not in mxl_text
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
        mscx_name = next(n for n in names if n.endswith(".mscx"))
        mscx = archive.read(mscx_name).decode("utf-8")
    assert mscx.count("<Part id=") == 2 or mscx.count('<Part id="') == 2
    assert "Soprano" not in mscx
    assert "Alto" not in mscx
    compact = mscx.replace(" ", "")
    assert "firstSystemInstNameVisibility>0<" in compact
    assert "subsSystemInstNameVisibility>0<" in compact
    assert "pageWidth>8.26772<" in compact
    assert "minSystemDistance>8<" in compact
    assert "lastSystemFillLimit>0<" in compact


def test_apply_partituur_style_on_minimal_mscz(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style>"
        "<pageWidth>1</pageWidth>"
        "</Style>"
        "<Part><longName>Soprano</longName>"
        "<Instrument><longName>Soprano</longName>"
        "<shortName>S</shortName><trackName>Soprano</trackName>"
        "</Instrument></Part>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(path)
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "<longName></longName>" in out
    assert "<pageWidth>8.26772</pageWidth>" in out
    assert "<minSystemDistance>8</minSystemDistance>" in out
    assert "<lyricsOddFontFace>Source Sans 3</lyricsOddFontFace>" in out


def test_promote_tekst_staff_text_to_system_text(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        "<StaffText><text>P: Gezegend … der eeuwen</text></StaffText>"
        "<StaffText><text>andere tekst</text></StaffText>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(
        path, system_texts=["P: Gezegend … der eeuwen"]
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "<SystemText><text>P: Gezegend … der eeuwen</text></SystemText>" in out
    assert "<StaffText><text>andere tekst</text></StaffText>" in out


def test_promote_tekst_matches_br_ellipsis(tmp_path: Path):
    """MuseScore zet ``\\n`` om naar ``<br/>``; promote moet dat matchen."""
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice>"
        "<StaffText><text>P: Gezegend<br/>... der eeuwen</text></StaffText>"
        "</Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(
        path, system_texts=["P: Gezegend ... der eeuwen"]
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "<SystemText>" in out
    assert "<StaffText>" not in out
    assert "Gezegend" in out


def test_gap_cue_spacer_rests_marks_short_rest_only_measure(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Rest><durationType>16th</durationType></Rest>"
        "</voice><len>1/16</len></Measure>"
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice><len>1/1</len></Measure>"
        "<Measure><voice>"
        "<Rest><durationType>measure</durationType></Rest>"
        "</voice><len>1/1</len></Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(path)
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    # Korte rust-only maat → weg (geen mid-systeem-HBox/accolade).
    assert "<HBox>" not in out
    assert "1/16" not in out
    # Hele-noot-rust en maat met Chord onaangeraakt.
    assert out.count("<Chord>") == 1
    assert "<len>1/1</len>" in out
    # Default-colofon aanwezig.
    assert "Colofon" in out
    assert "Bibliotheek-id:" not in out


def test_hbox_before_tekst_and_strip_trailing(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice></Measure>"
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice>"
        "<SystemText><text>P: Laat ons de Heer</text></SystemText>"
        "</Measure>"
        "<HBox><width>1.5</width><boxAutoSize>0</boxAutoSize></HBox>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(
        path,
        system_texts=["P: Laat ons de Heer"],
        hbox_before_texts=["P: Laat ons de Heer"],
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    # Geen mid-systeem-HBox vóór cue; trailing HBox aan staff-eind is weg.
    assert "<HBox>" not in out
    assert "P: Laat ons de Heer" in out


def test_recite_print_conventions_breve_head_and_mute_spacers(tmp_path: Path):
    """S8/R3: ||O|| via headType; spacers visible=0 + play=0; geen breve-lengte."""
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        '<Measure len="11/4">'
        "<voice>"
        "<Chord><durationType>quarter</durationType>"
        "<Note><pitch>70</pitch></Note></Chord>"
        "<Chord><durationType>breve</durationType><noStem>1</noStem>"
        "<Note><pitch>70</pitch></Note></Chord>"
        "<Chord><durationType>quarter</durationType><noStem>1</noStem>"
        "<Note><visible>0</visible><pitch>70</pitch></Note></Chord>"
        "<Chord><durationType>quarter</durationType>"
        "<Note><pitch>70</pitch></Note></Chord>"
        "</voice>"
        "</Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(path)
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "<durationType>breve</durationType>" not in out
    assert "<headType>breve</headType>" in out
    assert "<play>0</play>" in out
    assert 'len="1/1"' in out or 'len="4/4"' in out


def test_mscz_non_stemless_breve_becomes_whole(tmp_path: Path):
    """Melisma-artifact durationType=breve (mét stok) → whole, niet laten staan."""
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        '<Measure len="3/1">'
        "<voice>"
        "<Chord><durationType>whole</durationType>"
        "<Note><pitch>60</pitch></Note></Chord>"
        "<Chord><durationType>breve</durationType>"
        "<Note><pitch>60</pitch></Note></Chord>"
        "</voice>"
        "</Measure>"
        "</Staff>"
        '<Staff id="2">'
        '<Measure len="2/1">'
        "<voice>"
        "<Chord><durationType>whole</durationType>"
        "<Note><pitch>48</pitch></Note></Chord>"
        "<Chord><durationType>whole</durationType>"
        "<Note><pitch>48</pitch></Note></Chord>"
        "</voice>"
        "</Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(path)
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "<durationType>breve</durationType>" not in out
    # Beide staves dezelfde maat-len (max van de voices).
    lens = re.findall(r'\blen="([^"]+)"', out)
    assert len(lens) >= 2
    assert lens[0] == lens[1]


def test_colophon_uses_copyright_and_bibliotheek_id(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice><len>1/1</len></Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(
        path,
        copyright="Testnotice lang genoeg",
        bibliotheek_id="1a-vredeslitanie",
        title="(1a) Vredeslitanie",
        composer="Archimandriet Feofan",
        bron="Liturgikon, p.147-149",
        ondertitel="Litanie",
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert "Colofon" in out
    assert "Testnotice" in out
    assert "Bibliotheek-id: 1a-vredeslitanie" in out
    assert '<metaTag name="workTitle">(1a) Vredeslitanie</metaTag>' in out
    assert "<style>title</style>" in out
    assert "<text>(1a) Vredeslitanie</text>" in out
    assert '<metaTag name="composer">Archimandriet Feofan</metaTag>' in out
    assert '<metaTag name="source">Liturgikon, p.147-149</metaTag>' in out
    assert '<metaTag name="subtitle">Litanie</metaTag>' in out
    assert "oddFooterC>" in out


def test_bron_without_tekstdichter_appears_as_lyricist_on_sheet(tmp_path: Path):
    """``@bron`` alleen → zichtbaar op blad als lyricist ``bron: …``."""
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice><len>1/1</len></Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "bron.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("bron.mscx", mscx)
    apply_partituur_mscz_conventions(
        path,
        title="Demo",
        bron="koormap Hemelum",
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("bron.mscx").decode("utf-8")
    assert '<metaTag name="source">koormap Hemelum</metaTag>' in out
    assert '<metaTag name="lyricist">bron: koormap Hemelum</metaTag>' in out
    assert "<style>lyricist</style>" in out
    assert "<text>bron: koormap Hemelum</text>" in out


def test_tekstdichter_wins_over_bron_for_sheet_lyricist(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice><len>1/1</len></Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "both.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("both.mscx", mscx)
    apply_partituur_mscz_conventions(
        path,
        title="Demo",
        bron="koormap Hemelum",
        tekstdichter="bron: koormap Hemelum",
    )
    with zipfile.ZipFile(path) as zf:
        out = zf.read("both.mscx").decode("utf-8")
    assert '<metaTag name="source">koormap Hemelum</metaTag>' in out
    assert '<metaTag name="lyricist">bron: koormap Hemelum</metaTag>' in out
    assert out.count("bron: koormap Hemelum") >= 2


def test_ensure_score_title_fills_empty_title_text(tmp_path: Path):
    from vsa.mscz_partituur import apply_partituur_mscz_conventions

    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style></Style>"
        '<Staff id="1">'
        "<VBox><height>10</height>"
        "<Text><style>title</style><text></text></Text>"
        "<Text><style>subtitle</style><text>ondertitel</text></Text>"
        "</VBox>"
        "<Measure><voice>"
        "<Chord><durationType>whole</durationType></Chord>"
        "</voice><len>1/1</len></Measure>"
        "</Staff>"
        "</Score></museScore>"
    )
    path = tmp_path / "t.mscz"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("t.mscx", mscx)
    apply_partituur_mscz_conventions(path, title="(1a) Vredeslitanie")
    with zipfile.ZipFile(path) as zf:
        out = zf.read("t.mscx").decode("utf-8")
    assert '<metaTag name="workTitle">(1a) Vredeslitanie</metaTag>' in out
    assert "<style>title</style><text>(1a) Vredeslitanie</text>" in out.replace("\n", "")
    assert "ondertitel" in out


def test_bibliotheek_id_from_path():
    from pathlib import Path
    from vsa.bibliotheek_id import bibliotheek_id_from_path

    p = Path("x/bibliotheek/7-kleine-intocht/zondag/hemelum/score.mscz")
    assert bibliotheek_id_from_path(p) == "7-kleine-intocht/zondag/hemelum"
    assert bibliotheek_id_from_path(Path("examples/mvsa/foo.mvsa")) is None
