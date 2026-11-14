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
