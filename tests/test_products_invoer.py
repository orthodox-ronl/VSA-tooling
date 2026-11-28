"""Versheid-vingerafdruk (migratie stap 6): bron, woorden, template, recept."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vsa import products_invoer
from vsa.products_invoer import bereken_invoer
from vsa.products_meta import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_LEGACY,
    build_meta,
    freshness,
    meta_path_for,
    sha256_file,
    upgrade_meta,
    write_meta,
)
from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    set_syllable_dictionary_path,
)

_MVSA = """\
@do F4
@mode major
@sectie a
L: (Gij werd ver-heer-lijkt) |
S: g                        |
"""

_LIJST = "ver-heer-lijkt\ngij\nwerd\nberg\n"


@pytest.fixture
def lied(tmp_path: Path) -> Path:
    lijst = tmp_path / "lijst.txt"
    lijst.write_text(_LIJST, encoding="utf-8")
    set_syllable_dictionary_path(lijst)
    clear_syllable_dictionary_cache()
    bron = tmp_path / "lied.mvsa"
    bron.write_text(_MVSA, encoding="utf-8")
    return bron


def _lijst_wijzigen(bron: Path, tekst: str) -> None:
    (bron.parent / "lijst.txt").write_text(tekst, encoding="utf-8")
    clear_syllable_dictionary_cache()


def _schrijf(bron: Path) -> None:
    mxl = bron.parent / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl})


def test_vingerafdruk_is_stabiel_en_heeft_vier_delen(lied: Path) -> None:
    a, b = bereken_invoer(lied), bereken_invoer(lied)
    assert a == b
    assert set(a) == {"bron", "woorden", "template", "recept", "sha256"}
    assert a["woorden"] and a["template"] == "" and a["recept"] == 1


def test_ander_woord_in_lijst_verandert_niets(lied: Path) -> None:
    voor = bereken_invoer(lied)["sha256"]
    _lijst_wijzigen(lied, _LIJST + "bijzonder\n")
    assert bereken_invoer(lied)["sha256"] == voor


def test_gebruikt_woord_in_lijst_verandert_wel(lied: Path) -> None:
    voor = bereken_invoer(lied)
    _lijst_wijzigen(lied, _LIJST.replace("werd", "werd\n+wer-d"))
    na = bereken_invoer(lied)
    assert na["woorden"] != voor["woorden"]
    assert na["bron"] == voor["bron"]


def test_recept_ophogen_verandert_vingerafdruk(
    lied: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    voor = bereken_invoer(lied)["sha256"]
    monkeypatch.setitem(products_invoer.RECEPT_VERSIE, "mvsa", 2)
    assert bereken_invoer(lied)["sha256"] != voor


def test_taal_zonder_lijst_telt_niet_mee(lied: Path) -> None:
    anders = lied.with_name("anders.mvsa")
    anders.write_text(
        _MVSA.replace("L: (Gij werd ver-heer-lijkt) |", "@taal ro\nL: (Gij werd ver-heer-lijkt) |"),
        encoding="utf-8",
    )
    assert bereken_invoer(anders)["woorden"] == ""


def test_freshness_ok_en_redenen(lied: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _schrijf(lied)
    assert freshness(lied, invoer="streng") == ("ok", "meta en producten in orde")

    monkeypatch.setitem(products_invoer.RECEPT_VERSIE, "mvsa", 2)
    status, reden = freshness(lied, invoer="streng")
    assert status == "stale" and "recept 1 -> 2" in reden
    assert freshness(lied)[0] == "ok"  # los: alleen de bron telt
    monkeypatch.undo()

    _lijst_wijzigen(lied, _LIJST.replace("werd", "werd\n+wer-d"))
    status, reden = freshness(lied, invoer="streng")
    assert status == "stale" and "woordenlijst" in reden
    assert freshness(lied)[0] == "ok"


def _oud_schema(bron: Path) -> None:
    """Schrijf schema-2-meta zoals bestaande bronnen die nu hebben."""
    mxl = bron.parent / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    meta = build_meta(bron, {"mxl": mxl})
    meta["schema"] = SCHEMA_VERSION_LEGACY
    del meta["invoer"]
    meta_path_for(bron).write_text(json.dumps(meta), encoding="utf-8")


def test_oud_schema_los_en_streng(lied: Path) -> None:
    _oud_schema(lied)
    status, reden = freshness(lied)
    assert status == "ok" and "oud schema" in reden
    status, reden = freshness(lied, invoer="streng")
    assert status == "stale" and "oud schema" in reden


def test_upgrade_zet_schema_3_alleen_als_ok(lied: Path) -> None:
    _oud_schema(lied)
    assert upgrade_meta(lied, dry_run=True) is True
    assert json.loads(meta_path_for(lied).read_text())["schema"] == 2
    assert upgrade_meta(lied) is True
    meta = json.loads(meta_path_for(lied).read_text())
    assert meta["schema"] == SCHEMA_VERSION and meta["invoer"]["sha256"]
    assert freshness(lied, invoer="streng")[0] == "ok"

    _oud_schema(lied)
    lied.write_text(_MVSA + "% extra\n", encoding="utf-8")
    assert upgrade_meta(lied) is False


def test_merge_laat_oude_keys_vallen_als_invoer_veranderde(lied: Path) -> None:
    mxl = lied.parent / "lied.mvsa.mxl"
    mp3 = lied.parent / "lied.mvsa.mp3"
    mxl.write_text("<score/>", encoding="utf-8")
    mp3.write_bytes(b"mp3")
    write_meta(lied, {"mxl": mxl})
    _lijst_wijzigen(lied, _LIJST.replace("werd", "werd\n+wer-d"))
    write_meta(lied, {"mp3": mp3}, merge=True)
    assert set(json.loads(meta_path_for(lied).read_text())["products"]) == {"mp3"}


def test_bron_hash_blijft_in_meta(lied: Path) -> None:
    _schrijf(lied)
    meta = json.loads(meta_path_for(lied).read_text())
    assert meta["bron_sha256"] == sha256_file(lied) == meta["invoer"]["bron"]


def test_merge_behoudt_keys_van_schema2_sidecar(tmp_path):
    """Regressie: merge op een oude (schema 2) sidecar mag keys niet weggooien."""
    import json

    from vsa.products_meta import meta_path_for, write_meta

    bron = tmp_path / "lied.vsa"
    bron.write_text("@taal nl\n\nL: a\n", encoding="utf-8")
    mxl = tmp_path / "lied.vsa.mxl"
    mxl.write_bytes(b"x")
    mp3 = tmp_path / "lied.vsa.mp3"
    mp3.write_bytes(b"y")
    write_meta(bron, {"mxl": mxl, "mp3": mp3})
    pad = meta_path_for(bron)
    data = json.loads(pad.read_text(encoding="utf-8"))
    data["schema"] = 2
    data.pop("invoer", None)
    pad.write_text(json.dumps(data), encoding="utf-8")
    write_meta(bron, {"mp3": mp3}, merge=True)
    nieuw = json.loads(pad.read_text(encoding="utf-8"))
    assert set(nieuw["products"]) == {"mxl", "mp3"}
