"""MSCX renderer: clefs, recite-breve, cycle HBox/repeats, ankers."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_vsa_template_musicxml as render  # noqa: E402

LIBRARY = ROOT / "docs" / "specification-vsa-templates" / "library"
YAML_PATH = LIBRARY / "tropaar-toon-4-hemelum" / "template.yaml"


def _tropaar_mscx() -> str:
    doc = render.load_resolved(YAML_PATH, LIBRARY)
    return render.render_template_mscx(doc)


def test_mscx_tb_uses_f_clef_defaults_not_measure_clef() -> None:
    mscx = _tropaar_mscx()
    assert "<clef>F</clef>" in mscx
    assert "<defaultConcertClef>F</defaultConcertClef>" in mscx
    assert "<defaultTransposingClef>F</defaultTransposingClef>" in mscx
    assert "<Clef>" not in mscx
    assert "concertClefType" not in mscx


def test_mscx_cycle_in_hbox_with_spacer() -> None:
    mscx = _tropaar_mscx()
    assert f"<HBox><width>{render.CYCLE_SPACER_HBOX_WIDTH}</width></HBox>" in mscx
    assert f"<width>{render.CYCLE_TEXT_HBOX_WIDTH}</width>" in mscx
    assert "||: 1, 2 :|| laatste" in mscx
    spacer_at = mscx.index(f"<width>{render.CYCLE_SPACER_HBOX_WIDTH}</width>")
    text_at = mscx.index("||: 1, 2 :|| laatste")
    assert spacer_at < text_at


def test_mscx_cycle_repeat_barlines() -> None:
    mscx = _tropaar_mscx()
    assert "<startRepeat/>" in mscx
    assert "<endRepeat>2</endRepeat>" in mscx
    start_at = mscx.index("<startRepeat/>")
    end_at = mscx.index("<endRepeat>2</endRepeat>")
    assert start_at < end_at


def test_mscx_has_style_block() -> None:
    mscx = _tropaar_mscx()
    assert "<Style>" in mscx
    assert "<enableVerticalSpread>0</enableVerticalSpread>" in mscx
    assert "<maxPageFillSpread>0</maxPageFillSpread>" in mscx
    assert "<maxSystemDistance>9.64</maxSystemDistance>" in mscx
    assert "<maxSystemSpread>9.64</maxSystemSpread>" in mscx
    assert "<minSystemDistance>9.64</minSystemDistance>" in mscx
    assert "<staffDistance>5</staffDistance>" in mscx or "<staffDistance>5.0</staffDistance>" in mscx
    assert "<frameSystemDistance>4</frameSystemDistance>" in mscx or "<frameSystemDistance>4.0</frameSystemDistance>" in mscx
    assert "<enableIndentationOnFirstSystem>0</enableIndentationOnFirstSystem>" in mscx
    assert "<lastSystemFillLimit>1</lastSystemFillLimit>" in mscx
    assert f"<staffFontFace>{render.STAFF_FONT}</staffFontFace>" in mscx


def test_mscx_recite_is_stemless_breve_half_note() -> None:
    mscx = _tropaar_mscx()
    assert "<headType>breve</headType>" in mscx
    assert "<Fermata>" not in mscx
    assert "<Stem><visible>0</visible></Stem>" not in mscx
    recite_chords = re.findall(
        r"<Chord><durationType>half</durationType><noStem>1</noStem>"
        r"<Note>.*?<headType>breve</headType>",
        mscx,
        re.DOTALL,
    )
    assert len(recite_chords) == 12  # 3 frases × 2 staven × 2 stemmen


def test_mscx_has_no_invisible_padding_rests() -> None:
    mscx = _tropaar_mscx()
    assert "<Rest>" not in mscx
    assert 'len="20/4"' not in mscx


def test_mscx_anchor_is_abbreviation_plus_arrow() -> None:
    mscx = _tropaar_mscx()
    assert "↓ l. st." not in mscx
    assert ">l. st.</text>" in mscx
    assert ">↓</text>" in mscx
    assert f'y="{render.MAPPING_TEXT_Y}"' in mscx
    assert f'y="{render.ANCHOR_ARROW_Y}"' in mscx
    assert render.ANCHOR_ARROW_Y == "-1.3"
    pair = re.search(
        r">l\. st\.</text></StaffText>\s*"
        r'<StaffText>.*?y="-1\.3".*?>↓</text></StaffText>',
        mscx,
        re.DOTALL,
    )
    assert pair, "anker-afkorting then arrow below"


def test_mscx_frase_ids_keep_rectangle() -> None:
    mscx = _tropaar_mscx()
    assert mscx.count("<frameType>1</frameType>") == 3
    assert ">1</text>" in mscx
    assert ">2</text>" in mscx
    assert ">laatste</text>" in mscx


def test_library_templates_never_anchor_on_recite_event() -> None:
    """Frase-anker pijl wijst nooit naar een recite-event (anker en recite zijn apart)."""
    for yaml_path in sorted(LIBRARY.glob("*/template.yaml")):
        doc = render.load_resolved(yaml_path, LIBRARY)
        for phrase in doc.get("phrases", []):
            for event in phrase.get("events", []):
                if event.get("anchor"):
                    assert event.get("role") != "recite", (
                        f"{yaml_path}: anchor on recite in phrase {phrase['id']}"
                    )
