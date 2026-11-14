from dataclasses import dataclass, field
from pathlib import Path
import re

from .block_parser import parse_markdown_blocks
from .config import VSAConfig
from .parser import HALFTOON_CANONICAL, Parser
from .semantic_validator import SemanticValidationOptions, SemanticValidator
from .recoverable_syntax_validator import RecoverableSyntaxValidator
from .errors import VSAError
from .include_vsa import IncludeVsaError, IncludeVsaWarning, prepare_markdown_block_body, prepare_vsa_body
from .vsa_comments import (
    semantic_offset_to_source,
    strip_vsa_html_comments_with_offset_map,
)
from .yaml_frontmatter import strip_yaml_frontmatter


# Characters that form the base of an EHM (direction or same-tone).
_BASE_MODIFIER_CHARS: frozenset[str] = frozenset("/\\-~")

# Characters that can be a halftoon prefix — only valid when immediately
# followed by a _BASE_MODIFIER_CHARS character.
_HALFTOON_PREFIX_CHARS: frozenset[str] = frozenset(HALFTOON_CANONICAL)

# Halftoon glyphs that are never valid as sung text. If they appear after a
# base-EHM run, the author almost certainly put the prefix on the wrong side.
# Plain ASCII ``b`` is excluded: it is a valid zangelement character.
_HALFTOON_POSTFIX_ERROR_CHARS: frozenset[str] = frozenset("#♯+♭")


@dataclass
class ValidationMessage:
    source: str
    code: str
    message_nl: str
    line: int = 1
    column: int = 1
    severity: str = "error"
    category: str = "general"
    hint_nl: str = ""
    doc_url: str = ""


@dataclass
class ValidationResult:
    ok: bool = True
    messages: list[ValidationMessage] = field(default_factory=list)

    def add_error(self, source, code, message_nl, line=1, column=1,
                  category="general", hint_nl="", doc_url=""):
        self.add_message(source, code, message_nl, line, column, "error",
                         category, hint_nl, doc_url)

    def add_warning(self, source, code, message_nl, line=1, column=1,
                    category="general", hint_nl="", doc_url=""):
        self.add_message(source, code, message_nl, line, column, "warning",
                         category, hint_nl, doc_url)

    def add_message(self, source, code, message_nl, line=1, column=1,
                    severity="error", category="general", hint_nl="", doc_url=""):
        if severity == "error":
            self.ok = False

        self.messages.append(
            ValidationMessage(
                source=source,
                code=code,
                message_nl=message_nl,
                line=line,
                column=column,
                severity=severity,
                category=category,
                hint_nl=hint_nl,
                doc_url=doc_url,
            )
        )

    def extend(self, other):
        if not other.ok:
            self.ok = False
        self.messages.extend(other.messages)

    def has_errors(self):
        return any(message.severity == "error" for message in self.messages)

    def has_warnings(self):
        return any(message.severity == "warning" for message in self.messages)


def validate_path(path: str | Path, config: VSAConfig | None = None) -> ValidationResult:
    from .input_paths import InputPathError, collect_input_files, looks_like_catalogus_id

    raw = Path(path)

    if raw.is_file():
        return validate_file(raw, config=config)

    if raw.is_dir():
        result = ValidationResult()
        files = sorted(
            list(raw.rglob("*.md"))
            + list(raw.rglob("*.markdown"))
            + list(raw.rglob("*.vsa"))
        )
        for file in files:
            result.extend(validate_file(file, config=config))
        return result

    # Catalogus-id (bestand/map bestaat niet): alleen .vsa onder die leaf.
    if looks_like_catalogus_id(path):
        try:
            files = collect_input_files(path, suffixes=(".vsa",))
        except InputPathError as exc:
            result = ValidationResult()
            result.add_error(
                source=str(path),
                code="VSA-PATH-NOT-FOUND",
                message_nl=str(exc),
                category="path",
                hint_nl=(
                    "Gebruik een bestaand pad of een catalogus-id onder "
                    "content-source/catalogus (zie docs/reference/cli/input-pad.md)."
                ),
            )
            return result
        result = ValidationResult()
        for file in files:
            result.extend(validate_file(file, config=config))
        if not files:
            result.add_error(
                source=str(path),
                code="VSA-PATH-NOT-FOUND",
                message_nl="Geen .vsa-bestanden voor deze catalogus-id.",
                category="path",
                hint_nl="Controleer de id of geef een pad naar de leaf-map.",
            )
        return result

    result = ValidationResult()
    result.add_error(
        source=str(path),
        code="VSA-PATH-NOT-FOUND",
        message_nl="Pad niet gevonden.",
        category="path",
        hint_nl=(
            "Controleer of het pad bestaat, of geef een catalogus-id "
            "(docs/reference/cli/input-pad.md)."
        ),
    )
    return result


_VSA_VALIDATE_SUFFIXES = frozenset({".vsa", ".md", ".markdown"})


def validate_file(path: str | Path, config: VSAConfig | None = None) -> ValidationResult:
    path = Path(path)
    result = ValidationResult()
    suffix = path.suffix.lower()
    if suffix not in _VSA_VALIDATE_SUFFIXES:
        hint = (
            f"Voor .mvsa: mvsa validate {path}."
            if suffix == ".mvsa"
            else "Gebruik de CLI die bij het brontype hoort (vsa / mvsa / mxl / …)."
        )
        result.add_error(
            source=str(path),
            code="VSA-WRONG-FILE-TYPE",
            message_nl=(
                f"vsa validate verwacht .vsa of Markdown "
                f"(.md/.markdown); kreeg {suffix or '(geen extensie)'}."
            ),
            category="path",
            hint_nl=hint,
        )
        return result
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.add_error(
            source=str(path),
            code="VSA-ENCODING-ERROR",
            message_nl=(
                f"Bestand is geen geldige UTF-8-tekst "
                f"(byte {exc.object[exc.start]:#04x} op positie {exc.start})."
            ),
            category="encoding",
            hint_nl=(
                "Sla het bestand opnieuw op als UTF-8 "
                "(bijv. in Cursor/VS Code rechtsonder de encoding kiezen)."
            ),
        )
        return result

    if path.suffix.lower() in [".md", ".markdown"]:
        _validate_markdown(path, text, result, config=config)
    else:
        # Body-regels zijn 1-gebaseerd ná frontmatter; line_base telt alle
        # regels vóór de body (YAML-kop, lege regels) mee in het bronbestand.
        text = _auto_repair_vsa_soft_hyphens(path, text, result)
        _meta, _body, line_base = strip_yaml_frontmatter(text)
        try:
            expanded, warnings = prepare_vsa_body(text, path)
        except IncludeVsaError as exc:
            result.add_error(
                source=str(path),
                code="VSA-INCLUDE-VSA-ERROR",
                message_nl=exc.message_nl,
                line=line_base + max(exc.line, 1),
                category="include",
                hint_nl="Controleer @include-vsa id=, lokaal= of zoek= en catalogus-registratie.",
            )
            return result
        for warning in warnings:
            _add_include_vsa_warning(
                result,
                str(path),
                IncludeVsaWarning(
                    code=warning.code,
                    message_nl=warning.message_nl,
                    line=line_base + max(warning.line, 1),
                ),
            )
        _validate_vsa_text(
            str(path),
            expanded,
            result,
            config=config,
            source_line_offset=line_base,
        )

    return result


def _validate_markdown(path: Path, text: str, result: ValidationResult,
                       config: VSAConfig | None = None):
    try:
        blocks = parse_markdown_blocks(text)
    except VSAError as exc:
        result.add_error(
            source=str(path),
            code="VSA-BLOCK-PARSE-ERROR",
            message_nl=str(exc),
            category="syntax",
            hint_nl="Controleer de VSA-/mvsa-blokmarkeringen in het Markdownbestand.",
        )
        return

    for block in blocks:
        if block.kind == "mvsa":
            _validate_mvsa_block(path, block, result)
            continue
        try:
            expanded, warnings = prepare_markdown_block_body(
                block.body,
                markdown_path=path,
                markdown_text=text,
            )
        except IncludeVsaError as exc:
            result.add_error(
                source=str(path),
                code="VSA-INCLUDE-VSA-ERROR",
                message_nl=exc.message_nl,
                line=block.start_line + exc.line - 1,
                category="include",
                hint_nl="Controleer @include-vsa id=, lokaal= of zoek= en catalogus-registratie.",
            )
            continue
        for warning in warnings:
            _add_include_vsa_warning(
                result,
                str(path),
                IncludeVsaWarning(
                    code=warning.code,
                    message_nl=warning.message_nl,
                    line=block.start_line + warning.line - 1,
                ),
            )
        _validate_vsa_text(
            source=str(path),
            text=expanded,
            result=result,
            config=config,
            source_line_offset=block.start_line,
        )


def _validate_mvsa_block(path: Path, block, result: ValidationResult) -> None:
    from .mvsa_validate import validate_mvsa_text

    for diag in validate_mvsa_text(block.body, source=str(path)):
        line = block.start_line + max(diag.line, 1) - 1
        if diag.severity == "error":
            result.add_error(
                source=str(path),
                code=diag.code,
                message_nl=diag.message,
                line=line,
                category="mvsa",
                hint_nl="Controleer de mvsa-syntax in dit Markdown-blok.",
            )
        else:
            result.add_warning(
                source=str(path),
                code=diag.code,
                message_nl=diag.message,
                line=line,
                category="mvsa",
                hint_nl="Controleer de mvsa-syntax in dit Markdown-blok.",
            )


def _add_include_vsa_warning(
    result: ValidationResult,
    source: str,
    warning: IncludeVsaWarning,
) -> None:
    result.add_warning(
        source=source,
        code=warning.code,
        message_nl=warning.message_nl,
        line=warning.line,
        category="include",
    )


def _auto_repair_vsa_soft_hyphens(
    path: Path, text: str, result: ValidationResult
) -> str:
    """Vul ontbrekende soft ``-`` in de body (zoals ``vsa syllabify``).

    Alleen wanneer dictionary-MISMATCH/UNKNOWN of ontbrekende streepjes
    verdwijnen na syllabify. YAML-``zoektekst`` blijft onaangeroerd.
    Schrijft het bestand terug als er iets wijzigt.
    """
    from .parser import Parser
    from .syllabify import syllabify_vsa_source
    from .syllable_dict_check import (
        CODE_MISMATCH,
        CODE_UNKNOWN,
        find_dictionary_syllable_issues,
    )
    from .syllabify_validate import find_missing_syllable_hyphens
    from .vsa_comments import strip_vsa_html_comments_with_offset_map

    def _hard_issues(source: str) -> tuple[int, int]:
        _fm, body, _ = strip_yaml_frontmatter(source)
        body, _ = strip_vsa_html_comments_with_offset_map(body)
        try:
            document = Parser(body).parse()
        except Exception:
            return 0, 0
        dict_n = sum(
            1
            for f in find_dictionary_syllable_issues(document, source_text=body)
            if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
        )
        miss_n = len(find_missing_syllable_hyphens(document, source_text=body))
        return dict_n, miss_n

    before_dict, before_miss = _hard_issues(text)
    if before_dict == 0 and before_miss == 0:
        return text

    repaired = syllabify_vsa_source(text)
    if not repaired.changed:
        return text

    after_dict, after_miss = _hard_issues(repaired.text)
    if after_dict > before_dict or (
        after_dict == before_dict and after_miss >= before_miss
    ):
        # Geen verbetering → niet stil herschrijven.
        return text

    path.write_text(repaired.text, encoding="utf-8", newline="\n")
    result.add_warning(
        source=str(path),
        code="VSA-SYLLABIFY-APPLIED",
        message_nl=(
            f"Ontbrekende lettergreepstreepjes aangevuld "
            f"({repaired.replacements} wijziging(en); zelfde als "
            f"`vsa syllabify`). Bestand bijgewerkt."
        ),
        category="syllabify",
        hint_nl=(
            "Controleer de diff; soft `-` horen in de body, niet in "
            "`zoektekst`. Norm: docs/formats/syllabificatie.md."
        ),
        doc_url="docs/formats/syllabificatie.md",
    )
    return repaired.text


def _validate_vsa_text(source: str, text: str, result: ValidationResult,
                       config: VSAConfig | None = None, source_line_offset: int = 0):
    semantic_text, offset_map = strip_vsa_html_comments_with_offset_map(text)
    syntax_diagnostics = RecoverableSyntaxValidator(semantic_text).validate()

    for diagnostic in syntax_diagnostics.items:
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            diagnostic.line,
            diagnostic.column,
            source_line_offset,
        )
        result.add_error(
            source=source,
            code=diagnostic.code,
            message_nl=diagnostic.message_nl,
            line=line,
            column=column,
            category=getattr(diagnostic, "category", "syntax"),
            hint_nl=getattr(diagnostic, "hint_nl", ""),
            doc_url=getattr(diagnostic, "doc_url", ""),
        )

    if syntax_diagnostics.has_errors():
        return

    scope_issue = _first_scope_issue(semantic_text)
    if scope_issue is not None:
        line, column, code, message_nl, hint_nl = scope_issue
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            line,
            column,
            source_line_offset,
        )
        result.add_error(
            source=source,
            code=code,
            message_nl=message_nl,
            line=line,
            column=column,
            category="syntax",
            hint_nl=hint_nl,
        )
        return

    try:
        document = Parser(semantic_text).parse()
    except VSAError as exc:
        line, column = _line_column_from_exception(semantic_text, exc)
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            line,
            column,
            source_line_offset,
        )
        result.add_error(
            source=source,
            code="VSA-PARSE-ERROR",
            message_nl=str(exc),
            line=line,
            column=column,
            category="syntax",
            hint_nl="Controleer de VSA-syntax rond deze positie.",
        )
        return

    semantic_options = _semantic_options_from_config(config)
    diagnostics = SemanticValidator(document, semantic_options, source_text=semantic_text).validate()

    for diagnostic in diagnostics.items:
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            diagnostic.line,
            diagnostic.column,
            source_line_offset,
        )

        if diagnostic.severity == "error":
            result.add_error(
                source=source,
                code=diagnostic.code,
                message_nl=diagnostic.message_nl,
                line=line,
                column=column,
                category=diagnostic.category,
                hint_nl=diagnostic.hint_nl,
                doc_url=diagnostic.doc_url,
            )
        else:
            result.add_warning(
                source=source,
                code=diagnostic.code,
                message_nl=diagnostic.message_nl,
                line=line,
                column=column,
                category=diagnostic.category,
                hint_nl=diagnostic.hint_nl,
                doc_url=diagnostic.doc_url,
            )

    _add_syllabify_findings(
        source=source,
        document=document,
        semantic_text=semantic_text,
        text=text,
        offset_map=offset_map,
        source_line_offset=source_line_offset,
        result=result,
        config=config,
    )
    _add_syllable_dictionary_findings(
        source=source,
        document=document,
        semantic_text=semantic_text,
        text=text,
        offset_map=offset_map,
        source_line_offset=source_line_offset,
        result=result,
        config=config,
    )


def _semantic_options_from_config(config: VSAConfig | None):
    if config is None:
        return SemanticValidationOptions()
    return SemanticValidationOptions(severity_overrides=dict(config.validation.severity))


def _add_syllabify_findings(
    *,
    source: str,
    document,
    semantic_text: str,
    text: str,
    offset_map,
    source_line_offset: int,
    result: ValidationResult,
    config: VSAConfig | None,
) -> None:
    from .syllabify_validate import (
        CODE as SYLLABIFY_CODE,
        DEFAULT_SEVERITY as SYLLABIFY_DEFAULT_SEVERITY,
        DOC_URL as SYLLABIFY_DOC_URL,
        find_missing_syllable_hyphens,
        format_missing_hyphen_message,
    )

    severity = SYLLABIFY_DEFAULT_SEVERITY
    if config is not None:
        severity = config.validation.severity.get(SYLLABIFY_CODE, severity)
    if severity not in {"error", "warning"}:
        severity = SYLLABIFY_DEFAULT_SEVERITY

    for finding in find_missing_syllable_hyphens(document, source_text=semantic_text):
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            finding.line,
            finding.column,
            source_line_offset,
        )
        message_nl, hint_nl = format_missing_hyphen_message(finding)
        result.add_message(
            source=source,
            code=SYLLABIFY_CODE,
            message_nl=message_nl,
            line=line,
            column=column,
            severity=severity,
            category="syllabify",
            hint_nl=hint_nl,
            doc_url=SYLLABIFY_DOC_URL,
        )


def _add_syllable_dictionary_findings(
    *,
    source: str,
    document,
    semantic_text: str,
    text: str,
    offset_map,
    source_line_offset: int,
    result: ValidationResult,
    config: VSAConfig | None,
) -> None:
    from pathlib import Path

    from .parser import Parser
    from .syllable_dict_check import (
        CODE_MISMATCH,
        CODE_UNKNOWN,
        DOC_URL,
        apply_replacements_to_text,
        find_dictionary_syllable_issues,
        is_interactive_stdin,
        prompt_dictionary_fixes,
    )

    findings = find_dictionary_syllable_issues(
        document, source_text=semantic_text
    )
    if is_interactive_stdin():
        actionable = [
            f
            for f in findings
            if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
        ]
        if actionable:
            from .input_paths import source_id_for_prompt

            path = Path(source)
            session = prompt_dictionary_fixes(
                actionable, source_id=source_id_for_prompt(path)
            )
            if session.replacements:
                from .syllable_dict_check import apply_replacements_to_source
                from .syllabify import syllabify_vsa_source

                # Bestand: syllabify (scopes) + body-only lemma-vervangingen.
                if path.suffix.lower() == ".vsa" and path.is_file():
                    raw = path.read_text(encoding="utf-8")
                    raw = syllabify_vsa_source(raw).text
                    raw = apply_replacements_to_source(
                        raw, session.replacements
                    )
                    path.write_text(raw, encoding="utf-8", newline="\n")
                    _fm, body, _ = strip_yaml_frontmatter(raw)
                    semantic_text, _ = strip_vsa_html_comments_with_offset_map(
                        body
                    )
                else:
                    semantic_text = apply_replacements_to_text(
                        semantic_text, session.replacements
                    )
                try:
                    document = Parser(semantic_text).parse()
                except Exception:
                    pass
            findings = find_dictionary_syllable_issues(
                document, source_text=semantic_text
            )

    for finding in findings:
        severity = "error"
        if config is not None:
            severity = config.validation.severity.get(finding.code, severity)
        if severity not in {"error", "warning"}:
            severity = "error"
        # Onbekend op TTY na prompt: als nog unknown, blijft error.
        line, column = _source_line_column(
            text,
            semantic_text,
            offset_map,
            finding.line,
            finding.column,
            source_line_offset,
        )
        result.add_message(
            source=source,
            code=finding.code,
            message_nl=finding.message_nl,
            line=line,
            column=column,
            severity=severity,
            category="syllabify",
            hint_nl=finding.hint_nl,
            doc_url=DOC_URL,
        )


def _first_scope_issue(text: str):
    for start, end, content in _iter_scopes(text):
        stripped = content.strip()

        if stripped == "":
            line, column = _line_column_from_position(text, start)
            return (
                line, column,
                "VSA-SYNTAX-EMPTY-SCOPE",
                "Leeg zangelement.",
                "Vul tekst in tussen { en }, of verwijder het lege zangelement.",
            )

        parsed = _split_scope_prefix_and_text(stripped)
        if parsed is None:
            line, column = _line_column_from_position(text, start)
            return (
                line, column,
                "VSA-SYNTAX-INVALID-SCOPE",
                "Zangelement heeft geen herkenbare opbouw.",
                "Controleer de modifiers en de gezongen tekst binnen { en }.",
            )

        prefix, sung_text = parsed

        if prefix.startswith("&"):
            offset = start + 1 + content.index("&")
            line, column = _line_column_from_position(text, offset)
            return (
                line, column,
                "VSA-SYNTAX-INVALID-ALIGNMENT-MARKER",
                "`&` staat op een positie waar geen twee modifiers worden verbonden.",
                "Gebruik `&` alleen tussen twee opeenvolgende hoogte- of lengtemodifiers.",
            )

        if prefix and sung_text.strip() == "":
            line, column = _line_column_from_position(text, start)
            return (
                line, column,
                "VSA-SYNTAX-EMPTY-SUNG-TEXT",
                "Zangelement bevat wel modifiers maar geen tekst.",
                "Voeg tekst toe na de modifiers, of verwijder het zangelement.",
            )

        if (
            prefix
            and any(ch in _BASE_MODIFIER_CHARS for ch in prefix)
            and sung_text
            and sung_text[0] in _HALFTOON_POSTFIX_ERROR_CHARS
        ):
            bad_char = sung_text[0]
            strip_offset = content.find(stripped)
            if strip_offset < 0:
                strip_offset = 0
            absolute = start + 1 + strip_offset + len(prefix)
            line, column = _line_column_from_position(text, absolute)
            return (
                line, column,
                "VSA-SYNTAX-HALFTOON-PREFIX-AFTER-BASE",
                (
                    f"`{bad_char}` moet vóór het rijtje `/`, `\\`, `-` of `~` "
                    "komen te staan."
                ),
                "Schrijf de halftoon-prefix direct vóór de basisbeweging, "
                r"bijvoorbeeld `{+\tekst}` in plaats van `{\+tekst}`.",
            )

        invalid_position = _modifier_inside_sung_text_position(sung_text)
        if invalid_position is not None:
            prefix_start = content.find(sung_text)
            absolute = start + 1 + prefix_start + invalid_position
            line, column = _line_column_from_position(text, absolute)
            return (
                line, column,
                "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT",
                "Modifierteken staat binnen de gezongen tekst van een zangelement.",
                "Zet modifiers vóór de tekst in het zangelement.",
            )

    return None


def _split_scope_prefix_and_text(content: str):
    index = 0
    n = len(content)
    while index < n:
        ch = content[index]
        if ch in _BASE_MODIFIER_CHARS or ch == "&":
            index += 1
        elif (
            ch in _HALFTOON_PREFIX_CHARS
            and index + 1 < n
            and content[index + 1] in _BASE_MODIFIER_CHARS
        ):
            index += 2  # consume prefix + base char as one unit
        else:
            break
    return content[:index], content[index:]


def _modifier_inside_sung_text_position(sung_text: str):
    for index, char in enumerate(sung_text):
        if char in "/\\":
            return index
    return None


def _iter_scopes(text: str):
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start < 0:
            return
        end = text.find("}", start + 1)
        if end < 0:
            return
        yield start, end, text[start + 1:end]
        index = end + 1


def _line_column_from_exception(text: str, exc: Exception):
    position = _position_from_exception(exc)
    if position is None:
        return 1, _best_effort_error_column(text)

    line, column = _line_column_from_position(text, position)
    if column <= 1:
        lines = text.splitlines()
        line_text = lines[line - 1] if 0 <= line - 1 < len(lines) else text
        column = _best_effort_error_column(line_text)
    return line, column


def _position_from_exception(exc: Exception):
    if hasattr(exc, "position"):
        value = getattr(exc, "position")
        if isinstance(value, int):
            return value

    match = re.search(r"position\s+(\d+)", str(exc))
    if match:
        return int(match.group(1))

    return None


def _line_column_from_position(text: str, position: int):
    position = max(0, min(position, len(text)))
    before = text[:position]
    line = before.count("\n") + 1
    last_newline = before.rfind("\n")
    if last_newline == -1:
        column = position + 1
    else:
        column = position - last_newline
    return line, column


def _offset_from_line_column(text: str, line: int, column: int) -> int:
    if line <= 1:
        return max(0, column - 1)

    current_line = 1
    index = 0
    while index < len(text) and current_line < line:
        if text[index] == "\n":
            current_line += 1
        index += 1

    return min(len(text), index + max(0, column - 1))


def _source_line_column(
    text: str,
    semantic_text: str,
    offset_map: list[int],
    semantic_line: int,
    semantic_column: int,
    source_line_offset: int,
) -> tuple[int, int]:
    semantic_offset = _offset_from_line_column(semantic_text, semantic_line, semantic_column)
    source_offset = semantic_offset_to_source(offset_map, semantic_offset)
    line, column = _line_column_from_position(text, source_offset)
    return source_line_offset + line, column


def _best_effort_error_column(text: str):
    candidates = ["{/", r"{\\", r"{\}", "/}", r"\}", "{&"]
    for candidate in candidates:
        index = text.find(candidate)
        if index >= 0:
            return index + 2

    for index, char in enumerate(text):
        if char not in " \t":
            return index + 1

    return 1
