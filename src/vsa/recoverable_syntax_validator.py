from .bracket_directive import split_pitch_transition_body
from .vsa_comments import strip_vsa_html_comments
from .diagnostics import DiagnosticCollection


class RecoverableSyntaxValidator:
    def __init__(self, text: str):
        # HTML comments inside VSA notation are ignored for validation.
        self.text = strip_vsa_html_comments(text)
        self.diagnostics = DiagnosticCollection()

    def validate(self):
        self._validate_braces()
        self._validate_scopes()
        self._validate_pitch_markers()

        return self.diagnostics

    def _line_column(self, position: int):
        line = 1
        column = 1

        for index, ch in enumerate(self.text):
            if index == position:
                return line, column

            if ch == "\n":
                line += 1
                column = 1
            else:
                column += 1

        return line, column

    def _validate_braces(self):
        stack = []

        for position, ch in enumerate(self.text):
            line, column = self._line_column(position)

            if ch == "{":
                stack.append((position, line, column))

            elif ch == "}":
                if not stack:
                    self.diagnostics.add(
                        code="VSA-SYNTAX-UNEXPECTED-CLOSE-BRACE",
                        message_nl="Losse sluitaccolade.",
                        line=line,
                        column=column,
                    )
                else:
                    stack.pop()

        for _, line, column in stack:
            self.diagnostics.add(
                code="VSA-SYNTAX-UNCLOSED-SCOPE",
                message_nl="Scope zonder afsluitende accolade.",
                line=line,
                column=column,
            )

    def _validate_scopes(self):
        position = 0

        while position < len(self.text):
            start = self.text.find("{", position)

            if start == -1:
                break

            end = self.text.find("}", start + 1)

            if end == -1:
                position = start + 1
                continue

            content = self.text[start + 1:end]
            line, column = self._line_column(start)

            if content == "":
                self.diagnostics.add(
                    code="VSA-SYNTAX-EMPTY-SCOPE",
                    message_nl="Scope zonder zangelement.",
                    line=line,
                    column=column,
                )

            elif any(ch.isspace() for ch in content):
                self.diagnostics.add(
                    code="VSA-SYNTAX-WHITESPACE-IN-SCOPE",
                    message_nl="Whitespace binnen scope.",
                    line=line,
                    column=column,
                )

            position = end + 1

    def _validate_pitch_markers(self):
        position = 0

        while position < len(self.text):
            start = self.text.find("[", position)

            if start == -1:
                break

            end = self.text.find("]", start + 1)
            line, column = self._line_column(start)

            if end == -1:
                self.diagnostics.add(
                    code="VSA-SYNTAX-UNCLOSED-PITCH-MARKER",
                    message_nl="Toonhoogte-markering zonder afsluitende ']'.",
                    line=line,
                    column=column,
                )
                position = start + 1
                continue

            content = self.text[start + 1:end]

            if content.endswith(":"):
                pass
            elif split_pitch_transition_body(content) is not None:
                pass
            elif ":" in content:
                self.diagnostics.add(
                    code="VSA-SYNTAX-INVALID-PITCH-TRANSITION",
                    message_nl=(
                        "Ongeldige toonhoogte-overgang; "
                        "gebruik `[<oude-EHM>:<nieuwe-EHM>]` met geldige EHM-waarden."
                    ),
                    line=line,
                    column=column,
                )
            else:
                self.diagnostics.add(
                    code="VSA-SYNTAX-PITCH-MARKER-MISSING-COLON",
                    message_nl="Toonhoogte-markering mist ':'.",
                    line=line,
                    column=column,
                )

            position = end + 1
