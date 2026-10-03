from .ast import (
    Document,
    TextNode,
    ScopeNode,
    PitchMarkerNode,
    HeightMarkerNode,
    PitchTransitionNode,
)
from .bracket_directive import split_pitch_transition_body
from .errors import VSASyntaxError
from .vsa_comments import semantic_offset_to_source, strip_vsa_html_comments_with_offset_map


BRACKET_DIRECTIVE_END = ":]"

BASE_EHM_VALUES = [
    "/////",
    "////",
    "///",
    "//",
    "/",
    "\\\\\\\\\\",
    "\\\\\\\\",
    "\\\\\\",
    "\\\\",
    "\\",
    "-",
    "~",
]

# Canonical form: '+' and '♯' are aliases for '#'; '♭' is alias for 'b'.
HALFTOON_PREFIXES = ["#", "♯", "+", "b", "♭"]

HALFTOON_CANONICAL: dict[str, str] = {
    "#": "#",
    "♯": "#",
    "+": "#",
    "b": "b",
    "♭": "b",
}

EHM_VALUES = sorted(
    BASE_EHM_VALUES + [p + b for p in HALFTOON_PREFIXES for b in BASE_EHM_VALUES],
    key=len,
    reverse=True,
)

ELM_VALUES = [
    "__",
    "..",
    "_.",
    "-.",
    "~.",
    "_",
    ".",
    "-",
    "~",
]

MODIFIER_CHARS = set("&~+-\\/_.")


class Parser:
    def __init__(self, text: str):
        # HTML comments inside VSA notation are source-only annotations.
        # They are ignored for parsing and all derived artifacts.
        stripped, offset_map = strip_vsa_html_comments_with_offset_map(text)
        self.text = stripped
        self._offset_map = offset_map
        self.pos = 0

    def _source_offset(self, stripped_pos: int) -> int:
        return semantic_offset_to_source(self._offset_map, stripped_pos)

    def parse(self) -> Document:
        nodes = []

        while self.pos < len(self.text):
            if self._starts_with("{"):
                nodes.append(self._parse_scope())
            elif self._starts_with("["):
                nodes.append(self._parse_bracket_directive())
            elif self._starts_with("}"):
                raise VSASyntaxError("Losse sluitaccolade", self.pos)
            else:
                nodes.append(self._parse_text())

        return Document(nodes=nodes)

    def _parse_text(self) -> TextNode:
        start = self.pos

        while self.pos < len(self.text):
            if self.text[self.pos] in "{[":
                break
            if self.text[self.pos] == "}":
                raise VSASyntaxError("Losse sluitaccolade", self.pos)
            self.pos += 1

        return TextNode(
            self.text[start:self.pos],
            start=self._source_offset(start),
            end=self._source_offset(self.pos),
        )

    def _parse_bracket_directive(self) -> PitchMarkerNode | PitchTransitionNode:
        start = self.pos
        close = self.text.find("]", self.pos + 1)

        if close == -1:
            raise VSASyntaxError(
                "Toonhoogte-markering mist afsluitende ']'",
                start,
            )

        inner = self.text[self.pos + 1 : close]

        if inner.endswith(":"):
            raw_modifier = inner[:-1]
            height_modifier = self._parse_pitch_marker_modifier(raw_modifier, start)
            self.pos = close + 1
            return HeightMarkerNode(
                height_modifier=height_modifier,
                start=self._source_offset(start),
                end=self._source_offset(self.pos),
            )

        split = split_pitch_transition_body(inner)
        if split is not None:
            old_raw, new_raw = split
            from_mod = self._parse_pitch_marker_modifier(old_raw, start)
            to_mod = self._parse_pitch_marker_modifier(new_raw, start)
            self.pos = close + 1
            return PitchTransitionNode(
                from_height_modifier=from_mod,
                to_height_modifier=to_mod,
                start=self._source_offset(start),
                end=self._source_offset(self.pos),
            )

        # Behoud herkenbare fout voor `[/]` e.d. (geen `:`-afsluiter van een markering).
        if BRACKET_DIRECTIVE_END not in self.text[self.pos : close + 1]:
            raise VSASyntaxError(
                "Toonhoogte-markering mist bracket-directive eindtoken ':]' "
                "of toonhoogte-overgang '[<EHM>:<EHM>]'",
                start,
            )

        raise VSASyntaxError(
            f"Ongeldige toonhoogte-overgang of -markering: [{inner}]",
            start,
        )

    def _parse_pitch_marker(self) -> PitchMarkerNode | PitchTransitionNode:
        """Backwards-compatible alias for bracket-directive parsing."""
        return self._parse_bracket_directive()

    def _parse_pitch_marker_modifier(self, raw_modifier: str, start: int) -> list[str]:
        if raw_modifier == "":
            return []

        if raw_modifier not in EHM_VALUES:
            raise VSASyntaxError(f"Ongeldige modifier: {raw_modifier}", start)

        return [raw_modifier]

    def _parse_scope(self) -> ScopeNode:
        start = self.pos
        end = self.text.find("}", self.pos)

        if end == -1:
            raise VSASyntaxError("Scope zonder afsluitende accolade", start)

        content = self.text[self.pos + 1:end]

        if content == "":
            raise VSASyntaxError("Scope zonder zangelement", start)

        if any(ch.isspace() for ch in content):
            raise VSASyntaxError("Whitespace binnen scope", start)

        height_modifier, element, length_modifier = self._split_scope_content(content, start)

        self.pos = end + 1

        return ScopeNode(
            height_modifier=height_modifier,
            text=element,
            length_modifier=length_modifier,
            start=self._source_offset(start),
            end=self._source_offset(self.pos),
        )

    def _split_scope_content(self, content: str, start: int):
        prefix_candidates = self._prefix_candidates(content, EHM_VALUES)
        suffix_candidates = self._suffix_candidates(content, ELM_VALUES)

        best = None

        for prefix_len, height_modifier in prefix_candidates:
            for suffix_start, length_modifier in suffix_candidates:
                if prefix_len > suffix_start:
                    continue

                element = content[prefix_len:suffix_start]

                if element == "":
                    continue

                if any(ch in MODIFIER_CHARS for ch in element):
                    continue

                score = prefix_len + (len(content) - suffix_start)

                if best is None or score > best[0]:
                    best = (score, height_modifier, element, length_modifier)

        if best is None:
            if any(ch in MODIFIER_CHARS for ch in content):
                raise VSASyntaxError("Modifierteken binnen zangelement", start)

            return [], content, []

        _, height_modifier, element, length_modifier = best

        return height_modifier, element, length_modifier

    def _prefix_candidates(self, content: str, allowed_values: list[str]):
        candidates = [(0, [])]

        def walk(index, parts):
            matched_any = False

            for value in allowed_values:
                if content.startswith(value, index):
                    next_index = index + len(value)
                    new_parts = parts + [value]
                    candidates.append((next_index, new_parts))
                    matched_any = True

                    if content.startswith("&", next_index):
                        walk(next_index + 1, new_parts)

            return matched_any

        walk(0, [])

        return candidates

    def _suffix_candidates(self, content: str, allowed_values: list[str]):
        candidates = [(len(content), [])]

        for index in range(len(content)):
            raw = content[index:]

            try:
                parts = self._split_modifier(raw, allowed_values)
            except VSASyntaxError:
                continue

            candidates.append((index, parts))

        return candidates

    def _split_modifier(self, modifier: str, allowed_values: list[str]) -> list[str]:
        if modifier == "":
            return []

        parts = modifier.split("&")

        if any(part == "" for part in parts):
            raise VSASyntaxError("Leeg modifierdeel", self.pos)

        for part in parts:
            if part not in allowed_values:
                raise VSASyntaxError(f"Ongeldige modifier: {part}", self.pos)

        return parts

    def _starts_with(self, value: str) -> bool:
        return self.text.startswith(value, self.pos)
