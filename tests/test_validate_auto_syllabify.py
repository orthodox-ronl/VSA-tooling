"""Validate vult ontbrekende soft ``-`` automatisch (vsa/mvsa syllabify)."""

from __future__ import annotations

from pathlib import Path

from vsa.mvsa_validate import validate_mvsa_path
from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    set_syllable_dictionary_path,
)
from vsa.validation_runner import validate_path


def test_validate_auto_repairs_soft_hyphens_in_scoped_plain_text(
    tmp_path: Path, monkeypatch
) -> None:
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("recht-vaar-di-ge\neeu-wi-ge\n", encoding="utf-8")
    set_syllable_dictionary_path(dict_file)
    clear_syllable_dictionary_cache()

    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(check_mod, "is_interactive_stdin", lambda stdin=None: False)

    vsa_path = tmp_path / "lied.vsa"
    vsa_path.write_text(
        "---\n"
        "zoektekst: |-\n"
        "  de rechtvaardige\n"
        "---\n"
        "\n"
        "{\\recht}{\\vaar_}dige eeuwi{\\ge}\n",
        encoding="utf-8",
        newline="\n",
    )

    result = validate_path(vsa_path)
    text = vsa_path.read_text(encoding="utf-8")
    assert "di-ge" in text
    assert "eeu-wi" in text
    # zoektekst blijft zonder soft -
    fm = text.split("---\n", 2)[1]
    assert "rechtvaardige" in fm
    assert "recht-vaar" not in fm
    assert not any(
        m.code in {"VSA-SYLLABLE-DICT-MISMATCH", "VSA-SYLLABLE-DICT-UNKNOWN"}
        and m.severity == "error"
        for m in result.messages
    )
    assert any(m.code == "VSA-SYLLABIFY-APPLIED" for m in result.messages)
    clear_syllable_dictionary_cache()
    set_syllable_dictionary_path(None)


def test_mvsa_validate_auto_repairs_recite_soft_hyphens(
    tmp_path: Path, monkeypatch
) -> None:
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("leer-lin-gen\ntoon-de\n", encoding="utf-8")
    set_syllable_dictionary_path(dict_file)
    clear_syllable_dictionary_cache()

    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(check_mod, "is_interactive_stdin", lambda stdin=None: False)

    mvsa_path = tmp_path / "lied.mvsa"
    mvsa_path.write_text(
        "---\n"
        "zoektekst: |-\n"
        "  Leerlingen toonde\n"
        "---\n"
        "\n"
        "@title \"t\"\n"
        "@do F4\n"
        "@mode major\n"
        "@oct S=0\n"
        "\n"
        "@sectie demo\n"
        "L: (Leerlingen toonde) heer_ |\n"
        "S: a4                   -    |\n",
        encoding="utf-8",
        newline="\n",
    )

    diags = validate_mvsa_path(mvsa_path)
    text = mvsa_path.read_text(encoding="utf-8")
    assert "(Leer-lin-gen toon-de)" in text
    fm = text.split("---\n", 2)[1]
    assert "Leerlingen toonde" in fm
    assert "Leer-lin-gen" not in fm
    assert any(d.code == "MVSA-SYLLABIFY-APPLIED" for d in diags)
    assert not any(
        d.code in {"VSA-SYLLABLE-DICT-MISMATCH", "VSA-SYLLABLE-DICT-UNKNOWN"}
        and d.severity == "error"
        for d in diags
    )
    clear_syllable_dictionary_cache()
    set_syllable_dictionary_path(None)
