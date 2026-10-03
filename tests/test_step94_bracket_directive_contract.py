from docs_contracts import ARCHITECTURE, PARSER_STEPS, SPECIFICATION, read, assert_terms


HISTORICAL_CONTRACT = PARSER_STEPS / "parser-stap-94-bracket-directive-contract.md"
DIRECTIVE_DOCS = (
    SPECIFICATION / "directives.md",
    ARCHITECTURE / "directives.md",
)


def test_step94_historical_bracket_directive_decision_is_preserved():
    text = read(HISTORICAL_CONTRACT)

    assert_terms(
        text,
        (
            "[<EHM>:]",
            "één eindtoken",
            "Geen overstap naar `{<EHM>:}`",
            '"[" + <EHM> + ":]"',
        ),
    )


def test_current_directive_docs_define_bracket_dispatch_contract():
    text = "\n".join(read(path) for path in DIRECTIVE_DOCS)

    assert_terms(
        text,
        (
            "bracket-token ::=",
            'height-marker ::= "[" [ EHM ] ":]"',
            'pitch-transition ::= "[" [ EHM ] ":" EHM "]"',
            "Bracket-directives zijn tokens tussen `[` en `]`",
            "De parser moet eerst bepalen welk type bracket-token is aangetroffen",
        ),
    )
