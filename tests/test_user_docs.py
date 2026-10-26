from docs_contracts import GUIDES, doc, read_doc, read_docs, assert_terms


def test_user_facing_canonical_docs_exist():
    for name in (
        "quick_start_guide",
        "validation_guide",
        "cli_reference",
        "cli_spec",
        "config_reference",
        "outputs_reference",
        "diagnostics_reference",
    ):
        assert doc(name).exists()

    assert (GUIDES / "cli-taken.md").exists()


def test_user_guide_mentions_core_commands():
    text = read_doc("quick_start_guide") + (GUIDES / "cli-taken.md").read_text(
        encoding="utf-8"
    )

    assert_terms(
        text,
        (
            "vsa validate",
            "vsa svg",
            "vsa build-markdown",
            "md pdf",
            "vsa pdf",
            "vsa process",
            "vsa blocks",
            "vsa parse",
            "--ast",
        ),
    )


def test_cli_reference_mentions_core_commands():
    text = read_doc("cli_reference")

    assert_terms(
        text,
        (
            "vsa validate",
            "vsa svg",
            "vsa build-markdown",
            "md pdf",
            "vsa pdf",
            "vsa process",
            "vsa blocks",
            "vsa parse",
        ),
    )


def test_cli_reference_mentions_output_modes():
    text = read_docs("cli_reference", "config_reference")

    assert_terms(text, ("--output-mode img", "--output-mode shortcode"))


def test_user_guide_explains_validate_purpose_and_checks():
    text = read_docs("validation_guide", "validation_spec")

    assert_terms(
        text,
        (
            "Waarvoor gebruik je dit?",
            "Wat wordt gecontroleerd?",
            "scope is goed afgesloten",
            "scope is niet leeg",
            "geen whitespace binnen scope",
            "posities passen bij elkaar",
        ),
    )


def test_user_guide_explains_validate_success_and_failure():
    text = read_docs("validation_guide", "validation_spec", "cli_spec")

    assert_terms(
        text,
        ("Succesoutput", "Foutoutput", "OK", "Exitcode", "Diagnose bij problemen"),
    )


def test_user_guide_explains_parse_ast_output():
    text = read_doc("cli_spec") + doc("cli_spec").with_name("overview.md").read_text(
        encoding="utf-8"
    )

    assert_terms(
        text,
        ("Abstract Syntax Tree", "`--ast`", "JSON", "PitchMarkerNode", "ScopeNode", "TextNode"),
    )


def test_user_guide_explains_blocks_json_output():
    text = read_docs("cli_spec", "outputs_reference")

    assert_terms(
        text,
        ("VSA-blokken", "zonder `--json`", "--json", "start_line", "end_line", "metadata", "body", "ast"),
    )


def test_user_guide_explains_assets_dir_and_url_prefix():
    text = read_docs("cli_spec", "config_reference")

    assert_terms(text, ("<assets-dir>", "--assets-url-prefix", "URL-prefix", "/vsa"))
    assert "generated/static/vsa" in text or "generated\\static\\vsa" in text


def test_cli_reference_explains_assets_dir():
    text = read_docs("cli_reference", "cli_spec")

    assert "<assets-dir>" in text
    assert "doelmap voor gegenereerde svg" in text.lower()
    assert "generated/static/vsa" in text or "generated\\static\\vsa" in text


def test_cli_reference_explains_validate_outputs_and_errors():
    text = read_docs("cli_reference", "cli_spec", "diagnostics_reference")

    assert_terms(
        text,
        (
            "Succesoutput",
            "Foutoutput",
            "Veelvoorkomende foutcodes",
            "VSA-SYNTAX-EMPTY-SCOPE",
            "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH",
            "Wat doe je bij fouten?",
        ),
    )


def test_cli_reference_explains_defaults_and_precedence():
    text = read_docs("cli_reference", "config_reference")

    assert_terms(text, ("Defaults", "Voorrang", "max-line-width", "assets-url-prefix", "output-mode"))


def test_docs_explain_troubleshooting_or_diagnosis():
    user_text = read_docs("quick_start_guide", "validation_guide")
    cli_text = read_doc("cli_reference")

    assert "Diagnose bij problemen" in user_text
    assert "Diagnosevolgorde" in cli_text
    assert "scripts\\ci.cmd" in user_text
    assert "vsa validate" in cli_text


def test_user_guide_is_substantial():
    text = "\n".join(path.read_text(encoding="utf-8") for path in GUIDES.glob("*.md"))

    assert len(text.splitlines()) > 200


def test_cli_reference_is_substantial():
    text = read_docs("cli_reference", "config_reference", "cli_spec")

    assert len(text.splitlines()) > 200
