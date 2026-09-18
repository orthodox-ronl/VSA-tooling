from dataclasses import dataclass, field

from .diagnostics import DiagnosticCollection
from .height_markers import (
    height_marker_refs,
    height_marker_mismatch_detail,
    _degree_of_ehm_list,
    _marker_for_degree,
)

DOC_BASE = "docs/guides/validation.md"


@dataclass
class SemanticValidationResult:
    items: list

    @property
    def diagnostics(self):
        return self.items

    @property
    def ok(self):
        return not self.has_fatal_errors()

    def has_errors(self):
        return len(self.items) > 0

    def has_fatal_errors(self):
        return any(item.severity == "error" for item in self.items)

    def has_warnings(self):
        return any(item.severity == "warning" for item in self.items)


@dataclass
class SemanticValidationOptions:
    severity_overrides: dict[str, str] = field(default_factory=dict)


class SemanticValidator:
    def __init__(
        self,
        document,
        options: SemanticValidationOptions | None = None,
        source_text: str = "",
    ):
        self.document = document
        self.height_markers = height_marker_refs(document)
        self.options = options or SemanticValidationOptions()
        self.source_text = source_text

    def _line_column(self, offset: int | None) -> tuple[int, int]:
        """Zet een character-offset om naar (regel, kolom), of (1, 1) als onbekend."""
        if not self.source_text or offset is None:
            return 1, 1
        pos = max(0, min(offset, len(self.source_text)))
        before = self.source_text[:pos]
        line = before.count("\n") + 1
        last_nl = before.rfind("\n")
        col = (pos + 1) if last_nl == -1 else (pos - last_nl)
        return line, col

    def validate(self):
        diagnostics = DiagnosticCollection()

        self._validate_modifier_counts(diagnostics)
        self._validate_height_marker_sequence(diagnostics)

        return SemanticValidationResult(diagnostics.items)

    def _height_markers(self):
        return self.height_markers

    def _severity(self, code: str) -> str:
        return self.options.severity_overrides.get(code, "error")

    def _validate_modifier_counts(self, diagnostics):
        code = "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"

        for node in getattr(self.document, "nodes", []):
            if type(node).__name__ != "ScopeNode":
                continue

            height = len([
                value for value in getattr(node, "height_modifier", [])
                if value != "&"
            ])
            length = len([
                value for value in getattr(node, "length_modifier", [])
                if value != "&"
            ])

            if height > 0 and length > 0 and height != length:
                diagnostics.add(
                    code=code,
                    message_nl=(
                        "Hoogte- en lengte-modifier bevatten niet hetzelfde "
                        "aantal muzikale posities."
                    ),
                    line=1,
                    column=1,
                    severity=self._severity(code),
                    category="semantic",
                    hint_nl=(
                        "Controleer of hoogte- en lengtemodifiers evenveel "
                        "muzikale posities bevatten."
                    ),
                    doc_url=DOC_BASE,
                )

    def _validate_height_marker_sequence(self, diagnostics: DiagnosticCollection) -> None:
        """Controleert of elke lokale hoogte-markering overeenkomt met de berekende graad.

        De eerste markering geeft de begin-laddergraad. Elke volgende markering
        (rol 'local_height') wordt vergeleken met de cumulatieve diatonische
        cursor op basis van alle EHMs van de tussenliggende zangelementen.
        Accidens-prefixen (`#`/`+`/`b`) bewegen die cursor niet.

        Na elke markering — ook bij een mismatch — wordt de *gedeclareerde*
        graad als uitgangspunt voor het volgende segment genomen. Zo worden
        vervolgfouten die alleen voortkomen uit een eerdere foute markering
        niet apart gerapporteerd.
        """
        markers = self._height_markers()
        if len(markers) < 2:
            return

        code = "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        nodes = self.document.nodes
        current_degree: int = _degree_of_ehm_list(markers[0].ehm)
        prev_index: int = markers[0].index

        for ref in markers[1:]:
            computed_degree = current_degree
            for node in nodes[prev_index + 1 : ref.index]:
                if type(node).__name__ == "ScopeNode":
                    ehm = getattr(node, "height_modifier", [])
                    computed_degree += _degree_of_ehm_list(ehm)

            declared: int = _degree_of_ehm_list(ref.ehm)
            if declared != computed_degree:
                correct = _marker_for_degree(computed_degree)
                line, col = self._line_column(ref.node.start)
                diagnostics.add(
                    code=code,
                    message_nl=height_marker_mismatch_detail(declared, computed_degree),
                    line=line,
                    column=col,
                    severity=self._severity(code),
                    category="semantic",
                    hint_nl=f"Wijzig de markering naar `{correct}`.",
                    doc_url=DOC_BASE,
                )

            current_degree = declared
            prev_index = ref.index
