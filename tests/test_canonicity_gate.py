"""C3/C4 canoniciteitsgates."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from vsa.canonicity_gate import (
    NonCanonicalSourceError,
    NonCanonicalTargetError,
    check_canonical_mxl_target,
    check_canonical_source,
    playback_profile_for_bron,
    require_canonical_mxl_target,
    require_canonical_source,
)
from vsa.street_products import products_vsa_one


def test_check_canonical_valid_vsa(tmp_path: Path) -> None:
    # Monosyllabische demo zonder dictionary-UNKNOWN.
    dest = tmp_path / "ok.vsa"
    dest.write_text("do\n", encoding="utf-8")
    assert check_canonical_source(dest) == []


def test_require_blocks_broken_vsa(tmp_path: Path) -> None:
    dest = tmp_path / "broken.vsa"
    dest.write_text("{/broken\n", encoding="utf-8")
    with pytest.raises(NonCanonicalSourceError) as excinfo:
        require_canonical_source(dest)
    assert excinfo.value.issues
    assert excinfo.value.path == dest


def test_allow_noncanonical_skips(tmp_path: Path) -> None:
    dest = tmp_path / "broken.vsa"
    dest.write_text("{/broken\n", encoding="utf-8")
    require_canonical_source(dest, allow_noncanonical=True)


def test_c3_never_opens_dictionary_tty_prompt(
    tmp_path: Path, monkeypatch
) -> None:
    """products/C3 mag geen streepjes-prompt tonen (ook op TTY)."""
    from vsa import syllable_dict_check
    from vsa.syllable_dict_check import DictSyllableFinding

    dest = tmp_path / "lied.vsa"
    dest.write_text("Va-der\n", encoding="utf-8")

    def boom(*_a, **_k):
        raise AssertionError("prompt_dictionary_fixes mag niet bij C3")

    monkeypatch.setattr(
        syllable_dict_check, "prompt_dictionary_fixes", boom
    )
    monkeypatch.setattr(
        syllable_dict_check,
        "find_dictionary_syllable_issues",
        lambda *_a, **_k: [
            DictSyllableFinding(
                code="VSA-SYLLABLE-DICT-MISMATCH",
                surface="Va-der",
                expected="va-der",
                line=1,
                column=1,
                message_nl="test mismatch",
                hint_nl="",
            )
        ],
    )
    # Simuleer TTY: zonder force-flag zou validate prompten.
    monkeypatch.setattr(
        syllable_dict_check,
        "is_interactive_stdin",
        lambda stdin=None: (
            False
            if syllable_dict_check._force_noninteractive
            else True
        ),
    )
    issues = check_canonical_source(dest)
    assert any(i.code == "VSA-SYLLABLE-DICT-MISMATCH" for i in issues)


def test_products_batch_stops_on_dictionary_abort(monkeypatch) -> None:
    """Esc (rc=2) stopt de hele products-batch — geen volgend bestand."""
    from vsa import street_products
    from vsa.syllable_dict_check import DICT_PROMPT_ABORT_RC

    calls: list[Path] = []

    def fake_one(bron, **_kwargs):
        calls.append(bron)
        return DICT_PROMPT_ABORT_RC

    monkeypatch.setattr(street_products, "products_vsa_one", fake_one)
    monkeypatch.setattr(
        street_products,
        "collect_cli_sources",
        lambda *_a, **_k: [Path("a.vsa"), Path("b.vsa")],
    )
    rc = street_products.run_street_products("vsa", "catalogus")
    assert rc == DICT_PROMPT_ABORT_RC
    assert calls == [Path("a.vsa")]


def test_import_passes_dict_interactive_false(monkeypatch) -> None:
    """Import-kuiser (products score-ir-brug) zet dict_interactive=False."""
    from vsa import mvsa_import, musicxml_satb_layout
    from vsa.mvsa_kuiser import KuiserResult

    seen: dict[str, object] = {}

    def fake_kuiser(text, **kwargs):
        seen.update(kwargs)
        return KuiserResult(text=text, warnings=[])

    monkeypatch.setattr(mvsa_import, "kuiser_mvsa_text", fake_kuiser)
    monkeypatch.setattr(
        mvsa_import,
        "score_to_mvsa",
        lambda *_a, **_k: "@do C4\nL: Va-der ||\nS: do re ||\n",
    )
    monkeypatch.setattr(
        mvsa_import,
        "parse_musicxml_satb",
        lambda *_a, **_k: object(),
    )
    monkeypatch.setattr(
        mvsa_import,
        "read_musicxml_file",
        lambda *_a, **_k: "<score/>",
    )
    monkeypatch.setattr(
        musicxml_satb_layout,
        "ensure_playback_musicxml",
        lambda xml: xml,
    )

    text = mvsa_import.import_score_to_mvsa(Path("dummy.mxl"), align=True)
    assert "Va-der" in text
    assert seen.get("dict_interactive") is False


def test_prompt_dictionary_fixes_respects_force_noninteractive() -> None:
    """Hard refuse: force-flag → geen TTY ook bij isatty-stdin."""
    from vsa import syllable_dict_check
    from vsa.syllable_dict_check import (
        DictSyllableFinding,
        prompt_dictionary_fixes,
    )

    class _Tty:
        def isatty(self) -> bool:
            return True

        def read(self, *_a, **_k):
            raise AssertionError("geen stdin-read bij force_noninteractive")

    finding = DictSyllableFinding(
        code="VSA-SYLLABLE-DICT-MISMATCH",
        surface="Va-der",
        expected="va-der",
        line=1,
        column=1,
        message_nl="test",
        hint_nl="",
    )
    syllable_dict_check._force_noninteractive = True
    try:
        result = prompt_dictionary_fixes([finding], stdin=_Tty())
    finally:
        syllable_dict_check._force_noninteractive = False
    assert not result.replacements
    assert not result.aborted


def _write_minimal_mscz(path: Path, *, mscx: str | None = None) -> None:
    import zipfile

    body = mscx or (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<museScore version="4.00"><Score/></museScore>\n'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("score.mscx", body)


def test_mscz_rejects_garbage_zip(tmp_path: Path) -> None:
    p = tmp_path / "x.mscz"
    p.write_bytes(b"PK\x03\x04not-a-real-mscz")
    issues = check_canonical_source(p)
    assert issues and issues[0].code == "MSCZ-ZIP"


def test_mscz_rejects_zip_without_mscx(tmp_path: Path) -> None:
    import zipfile

    p = tmp_path / "empty.mscz"
    with zipfile.ZipFile(p, "w") as archive:
        archive.writestr("readme.txt", "geen score")
    issues = check_canonical_source(p)
    assert issues and issues[0].code == "MSCZ-MSCX"


def test_mscz_accepts_minimal_zip(tmp_path: Path) -> None:
    p = tmp_path / "ok.mscz"
    _write_minimal_mscz(p)
    assert check_canonical_source(p) == []


def test_products_mscz_refuses_noncanonical(tmp_path: Path) -> None:
    from vsa.street_products import products_mscz_one

    dest = tmp_path / "broken.mscz"
    dest.write_bytes(b"not-a-zip")
    assert products_mscz_one(dest, force=True, dry_run=True) == 1
    assert (
        products_mscz_one(
            dest, force=True, dry_run=True, allow_noncanonical=True
        )
        == 0
    )


def test_products_vsa_refuses_noncanonical(tmp_path: Path) -> None:
    dest = tmp_path / "broken.vsa"
    dest.write_text("{/broken\n", encoding="utf-8")
    assert products_vsa_one(dest, force=True, dry_run=True) == 1


def test_products_vsa_allow_noncanonical_dry_run(tmp_path: Path) -> None:
    dest = tmp_path / "broken.vsa"
    dest.write_text("{/broken\n", encoding="utf-8")
    # dry-run na C3: zonder allow faalt; met allow gaat planning door
    assert (
        products_vsa_one(
            dest, force=True, dry_run=True, allow_noncanonical=True
        )
        == 0
    )


def test_playback_profile_for_bron() -> None:
    assert playback_profile_for_bron(Path("lied.vsa")) == "mono"
    assert playback_profile_for_bron(Path("lied.mvsa")) == "satb"
    assert playback_profile_for_bron(Path("lied.mscz")) == "satb"


def test_c4_audio_ok_and_bad(tmp_path: Path) -> None:
    from vsa.canonicity_gate import (
        check_canonical_audio_target,
        require_canonical_audio_target,
    )

    mp3 = tmp_path / "ok.mp3"
    mp3.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00")
    assert check_canonical_audio_target(mp3) == []
    require_canonical_audio_target(mp3)

    ogg = tmp_path / "ok.ogg"
    ogg.write_bytes(b"OggS\x00\x02")
    assert check_canonical_audio_target(ogg) == []

    wav = tmp_path / "ok.wav"
    wav.write_bytes(b"RIFF....WAVE")
    assert check_canonical_audio_target(wav) == []

    bad = tmp_path / "bad.mp3"
    bad.write_bytes(b"not audio")
    issues = check_canonical_audio_target(bad)
    assert issues and issues[0].code == "AUDIO-HEADER"
    with pytest.raises(NonCanonicalTargetError):
        require_canonical_audio_target(bad)
    require_canonical_audio_target(bad, allow_noncanonical=True)


def test_c4_pdf_ok_and_bad(tmp_path: Path) -> None:
    from vsa.canonicity_gate import (
        check_canonical_pdf_target,
        require_canonical_pdf_target,
    )

    ok = tmp_path / "ok.pdf"
    ok.write_bytes(b"%PDF-1.4\n% tail")
    assert check_canonical_pdf_target(ok) == []
    require_canonical_pdf_target(ok)

    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    issues = check_canonical_pdf_target(bad)
    assert issues and issues[0].code == "PDF-HEADER"
    with pytest.raises(NonCanonicalTargetError):
        require_canonical_pdf_target(bad)
    require_canonical_pdf_target(bad, allow_noncanonical=True)


def test_c4_score_ir_ok_and_bad(tmp_path: Path) -> None:
    import json

    from vsa.canonicity_gate import (
        check_canonical_score_ir_target,
        require_canonical_score_ir_target,
    )
    from vsa.score_ir import SCORE_IR_FORMAT, SCORE_IR_PROFILE

    ok = tmp_path / "ok.score-ir.json"
    ok.write_text(
        json.dumps(
            {
                "format": SCORE_IR_FORMAT,
                "profile": SCORE_IR_PROFILE,
                "measures": [],
                "meta": {"title": "t"},
            }
        ),
        encoding="utf-8",
    )
    assert check_canonical_score_ir_target(ok) == []
    require_canonical_score_ir_target(ok)

    bad = tmp_path / "bad.score-ir.json"
    bad.write_text('{"format":"nope","profile":"partituur","measures":[]}', encoding="utf-8")
    issues = check_canonical_score_ir_target(bad)
    assert issues and issues[0].code == "SCORE-IR-FORMAT"
    with pytest.raises(NonCanonicalTargetError):
        require_canonical_score_ir_target(bad)
    require_canonical_score_ir_target(bad, allow_noncanonical=True)


def test_c4_require_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "x.mxl"
    out.write_bytes(b"PK")
    bron = tmp_path / "x.vsa"
    bron.write_text("do\n", encoding="utf-8")

    def _fake_validate(path, *, profile="satb"):  # noqa: ARG001
        assert profile == "mono"
        return [SimpleNamespace(code="M2", message="geen vier parts")]

    monkeypatch.setattr(
        "vsa.musicxml_playback_checklist.validate_playback_mxl_path",
        _fake_validate,
    )
    issues = check_canonical_mxl_target(out, bron=bron)
    assert issues and issues[0].code == "M2"
    with pytest.raises(NonCanonicalTargetError) as excinfo:
        require_canonical_mxl_target(out, bron=bron)
    assert excinfo.value.path == out
    require_canonical_mxl_target(out, bron=bron, allow_noncanonical=True)
