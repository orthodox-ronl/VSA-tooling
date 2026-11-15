"""Tests for shared bestand-of-map CLI helper."""

from pathlib import Path

import pytest

from vsa.input_paths import (
    InputPathError,
    catalogus_id_from_cli_token,
    catalogus_id_from_path,
    collect_cli_sources,
    collect_input_files,
    is_nested_derived_source,
    looks_like_catalogus_id,
    normalize_suffixes,
    reject_multi_with_output,
    resolve_catalogus_id,
    resolve_cli_path,
    source_id_for_prompt,
    strip_cli_location_suffix,
)


def test_normalize_suffixes():
    assert normalize_suffixes([".mvsa", "MSCZ"]) == frozenset({".mvsa", ".mscz"})
    with pytest.raises(InputPathError, match="extensie"):
        normalize_suffixes([])


def test_collect_single_file(tmp_path: Path):
    f = tmp_path / "lied.mvsa"
    f.write_text("@title x\n", encoding="utf-8")
    assert collect_input_files(f, suffixes=[".mvsa"]) == [f]


def test_collect_file_wrong_suffix(tmp_path: Path):
    f = tmp_path / "lied.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(InputPathError, match="Verwacht"):
        collect_input_files(f, suffixes=[".mvsa"])


def test_collect_missing_path(tmp_path: Path):
    with pytest.raises(InputPathError, match="niet gevonden"):
        collect_input_files(tmp_path / "geen", suffixes=[".mvsa"])


def test_collect_directory_recursive(tmp_path: Path):
    a = tmp_path / "a.mvsa"
    b = tmp_path / "sub" / "b.mvsa"
    skip = tmp_path / "sub" / "c.mscz"
    b.parent.mkdir()
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")
    skip.write_text("c", encoding="utf-8")
    got = collect_input_files(tmp_path, suffixes=[".mvsa", ".mscz"])
    assert got == [a, b, skip]


def test_collect_directory_non_recursive(tmp_path: Path):
    top = tmp_path / "top.mvsa"
    nested = tmp_path / "sub" / "nested.mvsa"
    nested.parent.mkdir()
    top.write_text("t", encoding="utf-8")
    nested.write_text("n", encoding="utf-8")
    assert collect_input_files(
        tmp_path, suffixes=[".mvsa"], recursive=False
    ) == [top]


def test_collect_directory_empty_ok(tmp_path: Path):
    assert collect_input_files(tmp_path, suffixes=[".mvsa"]) == []


def test_collect_cli_sources_empty_dir_raises(tmp_path: Path):
    with pytest.raises(InputPathError, match="Geen passende"):
        collect_cli_sources(tmp_path, suffixes=[".mvsa"])


def test_collect_cli_sources_finds_files(tmp_path: Path):
    a = tmp_path / "a.mvsa"
    a.write_text("@title t\n", encoding="utf-8")
    assert collect_cli_sources(tmp_path, suffixes=[".mvsa"]) == [a]


def test_is_nested_derived_source():
    assert is_nested_derived_source("lied.mvsa.mscz")
    assert is_nested_derived_source(Path("x.vsa.mscz"))
    assert is_nested_derived_source("lied.mscz.mscz")
    assert not is_nested_derived_source("lied.mscz")
    assert not is_nested_derived_source("lied.mvsa")


def test_collect_directory_skips_nested_derived(tmp_path: Path):
    """Batch: ``*.mvsa.mscz`` is geen losse mscz-bron; echte ``.mscz`` wel."""
    real = tmp_path / "bron.mscz"
    nested = tmp_path / "lied.mvsa.mscz"
    nested_svg_meta = tmp_path / "sub"
    nested_svg_meta.mkdir()
    deep = nested_svg_meta / "x.mvsa.mscz"
    real.write_bytes(b"PK")
    nested.write_bytes(b"PK")
    deep.write_bytes(b"PK")
    got = collect_input_files(tmp_path, suffixes=[".mscz"])
    assert got == [real]


def test_collect_explicit_nested_derived_allowed(tmp_path: Path):
    """Expliciet bestandspad: geneste afgeleide blijft toegestaan."""
    nested = tmp_path / "lied.mvsa.mscz"
    nested.write_bytes(b"PK")
    assert collect_input_files(nested, suffixes=[".mscz"]) == [nested]


def test_collect_cli_sources_only_nested_raises(tmp_path: Path):
    nested = tmp_path / "lied.mvsa.mscz"
    nested.write_bytes(b"PK")
    with pytest.raises(InputPathError, match="Geen passende"):
        collect_cli_sources(tmp_path, suffixes=[".mscz"])


def test_looks_like_catalogus_id():
    assert looks_like_catalogus_id("tropaar/transfiguratie-toon-7/hemelum")
    assert looks_like_catalogus_id("tropaar-transfiguratie-toon-7-hemelum")
    assert not looks_like_catalogus_id("lied.vsa")
    assert not looks_like_catalogus_id(r"C:\Git\orthodox-ronl\x")
    assert not looks_like_catalogus_id("../bibliotheek")


def test_catalogus_id_from_cli_token_strips_suffix():
    assert (
        catalogus_id_from_cli_token(
            "tropaar-transfiguratie-toon-7-hemelum.vsa",
            suffixes=[".vsa"],
        )
        == "tropaar-transfiguratie-toon-7-hemelum"
    )
    assert catalogus_id_from_cli_token(
        "map/lied.vsa", suffixes=[".vsa"]
    ) is None
    assert catalogus_id_from_cli_token(
        "lied.mvsa.mscz", suffixes=[".mscz"]
    ) is None


def test_collect_stem_with_extension_as_catalogus_id(tmp_path: Path):
    root = tmp_path / "content-source" / "catalogus"
    leaf = root / "communievers" / "kruisverheffing" / "hemelum"
    leaf.mkdir(parents=True)
    vsa = leaf / "communievers-kruisverheffing-hemelum.vsa"
    vsa.write_text("x\n", encoding="utf-8")
    got = collect_input_files(
        "communievers-kruisverheffing-hemelum.vsa",
        suffixes=[".vsa"],
        catalogus_roots=[root],
    )
    assert got == [vsa]


def test_catalogus_id_from_path_and_prompt_label(tmp_path: Path):
    leaf = (
        tmp_path
        / "content-source"
        / "catalogus"
        / "tropaar"
        / "transfiguratie-toon-7"
        / "hemelum"
    )
    leaf.mkdir(parents=True)
    vsa = leaf / "tropaar-transfiguratie-toon-7-hemelum.vsa"
    vsa.write_text("x\n", encoding="utf-8")
    assert (
        catalogus_id_from_path(vsa)
        == "tropaar/transfiguratie-toon-7/hemelum"
    )
    assert source_id_for_prompt(vsa) == "tropaar/transfiguratie-toon-7/hemelum"
    assert source_id_for_prompt(tmp_path / "los.vsa") == "los"


def test_resolve_catalogus_id_slash_and_stem(tmp_path: Path):
    root = tmp_path / "content-source" / "catalogus"
    leaf = root / "tropaar" / "transfiguratie-toon-7" / "hemelum"
    leaf.mkdir(parents=True)
    vsa = leaf / "tropaar-transfiguratie-toon-7-hemelum.vsa"
    mvsa = leaf / "tropaar-transfiguratie-toon-7-hemelum.mvsa"
    vsa.write_text("v\n", encoding="utf-8")
    mvsa.write_text("m\n", encoding="utf-8")

    by_slash = resolve_catalogus_id(
        "tropaar/transfiguratie-toon-7/hemelum",
        suffixes=[".vsa"],
        roots=[root],
    )
    assert by_slash == [vsa]

    by_stem = resolve_catalogus_id(
        "tropaar-transfiguratie-toon-7-hemelum",
        suffixes=[".mvsa"],
        roots=[root],
    )
    assert by_stem == [mvsa]

    via_collect = collect_input_files(
        "tropaar/transfiguratie-toon-7/hemelum",
        suffixes=[".vsa", ".mvsa"],
        catalogus_roots=[root],
    )
    assert via_collect == [mvsa, vsa]


def test_resolve_catalogus_id_missing(tmp_path: Path):
    root = tmp_path / "catalogus"
    root.mkdir()
    with pytest.raises(InputPathError, match="niet gevonden"):
        resolve_catalogus_id("tropaar/bestaat-niet/x", suffixes=[".vsa"], roots=[root])


def test_strip_cli_location_suffix():
    assert (
        strip_cli_location_suffix("catalogus/lied.vsa:29:28")
        == "catalogus/lied.vsa"
    )
    assert strip_cli_location_suffix("lied.vsa") == "lied.vsa"
    assert strip_cli_location_suffix('"lied.vsa:1:2"') == "lied.vsa"


def test_resolve_cli_path_short_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    cat = repo / "content-source" / "catalogus" / "alleluia" / "toon-1"
    cat.mkdir(parents=True)
    vsa = cat / "alleluia-toon-1-x.vsa"
    vsa.write_text("x\n", encoding="utf-8")
    (repo / "content-source" / "koormappen" / "hemelum").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert resolve_cli_path("alleluia", repo_root=repo) == (
        repo / "content-source" / "catalogus" / "alleluia"
    ).resolve()
    assert resolve_cli_path(
        "catalogus/alleluia/toon-1", repo_root=repo
    ) == cat.resolve()


def test_resolve_cli_path_missing(tmp_path: Path):
    with pytest.raises(InputPathError, match="niet gevonden"):
        resolve_cli_path("bestaat-niet", repo_root=tmp_path)


def test_resolve_catalogus_id_soort_map(tmp_path: Path):
    """``alleluia`` / ``communievers`` = map onder catalogus → alle bronnen."""
    root = tmp_path / "content-source" / "catalogus"
    a1 = root / "alleluia" / "toon-1"
    a2 = root / "alleluia" / "toon-2"
    c1 = root / "communievers" / "kruisverheffing" / "hemelum"
    a1.mkdir(parents=True)
    a2.mkdir(parents=True)
    c1.mkdir(parents=True)
    f1 = a1 / "alleluia-toon-1-x.vsa"
    f2 = a2 / "alleluia-toon-2-y.vsa"
    f3 = c1 / "communievers-kruisverheffing-hemelum.vsa"
    f1.write_text("a\n", encoding="utf-8")
    f2.write_text("b\n", encoding="utf-8")
    f3.write_text("c\n", encoding="utf-8")

    alleluia = resolve_catalogus_id("alleluia", suffixes=[".vsa"], roots=[root])
    assert alleluia == [f1, f2]

    communievers = resolve_catalogus_id(
        "communievers", suffixes=[".vsa"], roots=[root]
    )
    assert communievers == [f3]

    via_collect = collect_cli_sources(
        "alleluia", suffixes=[".vsa"], catalogus_roots=[root], repo_root=tmp_path
    )
    assert via_collect == [f1, f2]


def test_collect_soort_map_via_short_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = tmp_path / "bieb"
    leaf = repo / "content-source" / "catalogus" / "alleluia" / "toon-1"
    leaf.mkdir(parents=True)
    vsa = leaf / "alleluia-toon-1-x.vsa"
    vsa.write_text("x\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    got = collect_cli_sources("alleluia", suffixes=[".vsa"], repo_root=repo)
    assert got == [vsa]


def test_collect_leaf_slash_and_stam_vsa(tmp_path: Path):
    root = tmp_path / "content-source" / "catalogus"
    leaf = root / "communievers" / "kruisverheffing" / "hemelum"
    leaf.mkdir(parents=True)
    vsa = leaf / "communievers-kruisverheffing-hemelum.vsa"
    vsa.write_text("x\n", encoding="utf-8")

    by_slash = collect_cli_sources(
        "communievers/kruisverheffing/hemelum",
        suffixes=[".vsa"],
        catalogus_roots=[root],
    )
    assert by_slash == [vsa]

    by_stam = collect_cli_sources(
        "communievers-kruisverheffing-hemelum.vsa",
        suffixes=[".vsa"],
        catalogus_roots=[root],
    )
    assert by_stam == [vsa]


def test_collect_missing_still_raises(tmp_path: Path):
    with pytest.raises(InputPathError, match="niet gevonden"):
        collect_cli_sources(
            "bestaat-nergens",
            suffixes=[".vsa"],
            catalogus_roots=[tmp_path / "catalogus"],
            repo_root=tmp_path,
        )


def test_collect_strips_location_suffix(tmp_path: Path):
    root = tmp_path / "content-source" / "catalogus"
    leaf = root / "tropaar" / "x" / "hemelum"
    leaf.mkdir(parents=True)
    vsa = leaf / "tropaar-x-hemelum.vsa"
    vsa.write_text("x\n", encoding="utf-8")
    got = collect_cli_sources(
        "tropaar-x-hemelum.vsa:29:28",
        suffixes=[".vsa"],
        catalogus_roots=[root],
    )
    assert got == [vsa]


def test_reject_multi_with_output(tmp_path: Path):
    a = tmp_path / "a.vsa"
    b = tmp_path / "b.vsa"
    a.write_text("a\n", encoding="utf-8")
    b.write_text("b\n", encoding="utf-8")
    reject_multi_with_output([a], tmp_path / "out.vsa")
    with pytest.raises(InputPathError, match="-o"):
        reject_multi_with_output([a, b], tmp_path / "out.vsa")
