from __future__ import annotations

from typing import Literal, NamedTuple

from vsa.bracket_directive import (
    BracketDirective,
    find_bracket_directives,
    is_pitch_marker_directive,
    is_pitch_transition_directive,
)


BracketTokenKind = Literal["text", "directive", "pitch_marker", "pitch_transition"]


class BracketToken(NamedTuple):
    kind: BracketTokenKind
    start: int
    end: int
    value: str


def bracket_token_stream(text: str) -> list[BracketToken]:
    tokens: list[BracketToken] = []
    cursor = 0

    for directive in find_bracket_directives(text):
        if directive.start > cursor:
            tokens.append(
                BracketToken(
                    kind="text",
                    start=cursor,
                    end=directive.start,
                    value=text[cursor:directive.start],
                )
            )

        tokens.append(token_for_directive(directive))
        cursor = directive.end

    if cursor < len(text):
        tokens.append(
            BracketToken(
                kind="text",
                start=cursor,
                end=len(text),
                value=text[cursor:],
            )
        )

    return tokens


def token_for_directive(directive: BracketDirective) -> BracketToken:
    if is_pitch_marker_directive(directive):
        return BracketToken(
            kind="pitch_marker",
            start=directive.start,
            end=directive.end,
            value=directive.body,
        )

    if is_pitch_transition_directive(directive):
        return BracketToken(
            kind="pitch_transition",
            start=directive.start,
            end=directive.end,
            value=directive.body,
        )

    return BracketToken(
        kind="directive",
        start=directive.start,
        end=directive.end,
        value=directive.body,
    )


def pitch_marker_tokens(text: str) -> list[BracketToken]:
    return [
        token
        for token in bracket_token_stream(text)
        if token.kind == "pitch_marker"
    ]
