"""Kuiser Q4 (syllabify) + Q5 (dictionary) — docs/formats/kuiser.md."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mvsa_syllabify import MvsaSyllabifyError, syllabify_mvsa_text
from .syllable_dict_check import (
    CODE_MISMATCH,
    CODE_UNKNOWN,
    apply_replacements_to_source,
    find_mvsa_dictionary_syllable_issues,
    is_interactive_stdin,
    prompt_dictionary_fixes,
)

if TYPE_CHECKING:
    from .mvsa_kuiser import KuiserWarning


def apply_q4_q5(
    text: str,
    *,
    align: bool = True,
    dict_interactive: bool | None = None,
    source_path: Path | str | None = None,
) -> tuple[str, list[KuiserWarning]]:
    """Q4: soft ``-`` op L; Q5: dictionary-check → waarschuwingen (+ TTY-fix).

    ``dict_interactive`` None → zelfde als ``is_interactive_stdin()``.
    Bij conflict: waarschuwen; op TTY eventueel corrigeren; geen stille
    verkeerde deling (dictionary wint al in syllabify waar bekend).
    """
    from .mvsa_kuiser import KuiserWarning, MvsaKuiserError

    try:
        result = syllabify_mvsa_text(text, unsyllabify=False, align=align)
    except MvsaSyllabifyError as exc:
        raise MvsaKuiserError(str(exc), line=exc.line or 0) from exc

    out = result.text
    interactive = (
        is_interactive_stdin()
        if dict_interactive is None
        else dict_interactive
    )

    findings = find_mvsa_dictionary_syllable_issues(out)
    actionable = [
        f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
    ]
    if interactive and actionable:
        from .input_paths import source_id_for_prompt

        sid = None
        if source_path is not None:
            sid = source_id_for_prompt(Path(source_path))
        session = prompt_dictionary_fixes(
            actionable, source_id=sid, source_path=source_path
        )
        if session.replacements:
            out = apply_replacements_to_source(out, session.replacements)
            try:
                out = syllabify_mvsa_text(
                    out, unsyllabify=False, align=align
                ).text
            except MvsaSyllabifyError as exc:
                raise MvsaKuiserError(str(exc), line=exc.line or 0) from exc
            findings = find_mvsa_dictionary_syllable_issues(out)
        if session.aborted:
            return out, [
                KuiserWarning(
                    1,
                    1,
                    "VSA-SYLLABLE-DICT-ABORTED: Interactieve "
                    "syllable-dictionary-check afgebroken (Esc).",
                )
            ]

    warnings: list[KuiserWarning] = []
    for finding in findings:
        if finding.code not in {CODE_MISMATCH, CODE_UNKNOWN}:
            continue
        warnings.append(
            KuiserWarning(
                finding.line,
                finding.column,
                f"{finding.code}: {finding.message_nl}",
            )
        )
    return out, warnings
