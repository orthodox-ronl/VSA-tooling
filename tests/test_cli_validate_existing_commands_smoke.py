from pathlib import Path

from vsa.cli import main


def test_cli_version_smoke(capsys):
    exit_code = main(["--version"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.startswith("vsa ")


def test_cli_blocks_json_smoke(capsys, tmp_path: Path):
    path = tmp_path / "demo.md"

    path.write_text(
        """::: vsa-notatie
{tekst}
:::
""",
        encoding="utf-8",
    )

    exit_code = main(["blocks", str(path), "--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"body": "{tekst}"' in output


def test_cli_parse_ast_smoke(capsys, tmp_path: Path):
    path = tmp_path / "demo.vsa"
    path.write_text("{tekst}", encoding="utf-8")

    exit_code = main(["parse", str(path), "--ast"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"type": "Document"' in output


def test_cli_mxl_batch_smoke(capsys, tmp_path: Path):
    input_dir = tmp_path / "content-source"
    vsa_dir = input_dir / "demo"
    vsa_dir.mkdir(parents=True)
    a = vsa_dir / "a.vsa"
    b = vsa_dir / "b.vsa"
    a.write_text("{tekst}", encoding="utf-8")
    b.write_text("{tekst}", encoding="utf-8")

    exit_code = main(["mxl", str(input_dir)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "MXL-bestand(en) geschreven" in output
    assert (vsa_dir / "a.vsa.mxl").is_file()
    assert (vsa_dir / "b.vsa.mxl").is_file()


def test_cli_template_validate_library_smoke(capsys):
    library = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "specification-vsa-templates"
        / "library"
    )
    exit_code = main(["template", "validate", str(library)])
    output = capsys.readouterr()
    assert exit_code == 0
    assert "OK" in output.out
    assert "tropaar-toon-4-hemelum" in output.out
