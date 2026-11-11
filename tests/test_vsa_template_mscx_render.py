"""MSCX renderer: clefs, recite-breve, cycle HBox/repeats, ankers."""

from __future__ import annotations

import math
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
    _staff, _sys, _frame = render._vertical_layout_gaps()
    assert f"<maxSystemDistance>{_sys}</maxSystemDistance>" in mscx
    assert f"<maxSystemSpread>{_sys}</maxSystemSpread>" in mscx
    assert f"<minSystemDistance>{_sys}</minSystemDistance>" in mscx
    assert f"<staffDistance>{_staff}</staffDistance>" in mscx
    assert f"<frameSystemDistance>{_frame}</frameSystemDistance>" in mscx
    assert f"<staffUpperBorder>{render.TEMPLATE_STAFF_UPPER_BORDER_SP:g}</staffUpperBorder>" in mscx
    assert "<longName></longName>" in mscx
    assert "S<br/>A" not in mscx
    assert "T<br/>B" not in mscx
    # tropaar: 3 frasen → break na 2e → één LayoutBreak.
    assert mscx.count("<LayoutBreak>") == 1
    assert render.FRASE_ID_Y == render.MAPPING_TEXT_Y
    assert f'y="{render.FRASE_ID_Y}"' in mscx
    assert "<enableIndentationOnFirstSystem>0</enableIndentationOnFirstSystem>" in mscx
    assert "<lastSystemFillLimit>1</lastSystemFillLimit>" in mscx
    assert f"<staffFontFace>{render.STAFF_FONT}</staffFontFace>" in mscx
    assert "Tropaarmelodie (Toon 4)" in mscx


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
    """Geen opgeblazen padding-rusten op tropaar (geen e.st. op eerste noot)."""
    mscx = _tropaar_mscx()
    assert "<Rest>" not in mscx
    assert 'len="20/4"' not in mscx


def test_mscx_phrase_lead_spacer_when_first_event_has_anchor() -> None:
    """Kondak: e.st. op eerste noot → onzichtbare spacer-noot, noten naar rechts."""
    doc = render.load_resolved(
        LIBRARY / "kondak-toon-1-groningen" / "template.yaml", LIBRARY
    )
    mscx = render.render_template_mscx(doc)
    assert "<Rest>" not in mscx
    spacers = re.findall(
        rf"<Chord><durationType>{re.escape(render.PHRASE_LEAD_SPACER_NTYPE)}"
        r"</durationType><noStem>1</noStem><Note><visible>0</visible><play>0</play>",
        mscx,
    )
    # Frases 2, laatste, 1a × 2 staven × 2 stemmen.
    assert len(spacers) == 12


def test_mscx_anchor_is_abbreviation_plus_arrow() -> None:
    mscx = _tropaar_mscx()
    assert "↓ l. st." not in mscx
    assert ">l. st.</text>" in mscx
    assert ">↓</text>" in mscx
    assert f'y="{render.MAPPING_TEXT_Y}"' in mscx
    assert f'y="{render.FRASE_ID_Y}"' in mscx
    assert f'y="{render.ANCHOR_ARROW_Y}"' in mscx
    assert render.ANCHOR_ARROW_Y == "-1.3"
    pair = re.search(
        r">l\. st\.</text></StaffText>\s*"
        rf'<StaffText>.*?y="{re.escape(render.ANCHOR_ARROW_Y)}".*?>↓</text></StaffText>',
        mscx,
        re.DOTALL,
    )
    assert pair, "anker-afkorting then arrow below"
    assert "<showMeasureNumber>0</showMeasureNumber>" in mscx
    n_sys = math.ceil(3 / render.TEMPLATE_PHRASES_PER_SYSTEM)
    _h = max(
        render._PAGE_HEIGHT_A4_IN,
        render._TEMPLATE_PAGE_TITLE_INCH
        + n_sys * render._TEMPLATE_PAGE_INCH_PER_SYSTEM,
    )
    assert f"<pageHeight>{_h:.2f}</pageHeight>" in mscx


def test_mscx_template_page_grows_with_extra_phrases() -> None:
    doc = render.load_resolved(
        LIBRARY / "kondak-toon-1-groningen" / "template.yaml", LIBRARY
    )
    mscx = render.render_template_mscx(doc)
    n_sys = math.ceil(4 / render.TEMPLATE_PHRASES_PER_SYSTEM)
    _h = max(
        render._PAGE_HEIGHT_A4_IN,
        render._TEMPLATE_PAGE_TITLE_INCH
        + n_sys * render._TEMPLATE_PAGE_INCH_PER_SYSTEM,
    )
    assert f"<pageHeight>{_h:.2f}</pageHeight>" in mscx
    # 4 frasen → break na 2e (niet na 4e = laatste).
    assert mscx.count("<LayoutBreak>") == 1
    assert "Kondakmelodie (Toon 1)" in mscx
    assert f'x="{render.FRASE_ID_X_BESIDE_ANCHOR}"' in mscx
    assert f'x="{render.ANCHOR_LABEL_X_BESIDE_FRASE}"' in mscx


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
