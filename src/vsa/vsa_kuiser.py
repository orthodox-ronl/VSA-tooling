"""``vsa kuiser`` — V1–V8 (docs/formats/kuiser.md#vsa-v)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .mvsa_kuiser_q23 import (
    kuiser_tempo_for_soort,
    should_replace_tempo,
)
from .mvsa_kuiser_q67 import apply_q6
from .mvsa_vsa import _soort_toon_from_source_name
from .syllabify import syllabify_vsa_source
from .syllable_dict_check import (
    CODE_MISMATCH,
    CODE_UNKNOWN,
    apply_replacements_to_source,
    find_dictionary_syllable_issues,
    is_interactive_stdin,
    prompt_dictionary_fixes,
)
from .validation_runner import validate_file
from .yaml_frontmatter import strip_yaml_frontmatter
from .zoektekst import (
    LiteralZoektekst,
    _ZoektekstDumper,
    expected_zoektekst,
)

# Gedocumenteerde top-level sleutels (bibliotheek vsa-frontmatter + gangbaar).
_DOCUMENTED_KEYS = frozenset(
    {
        "titel",
        "title",
        "taal",
        "soort",
        "toon",
        "formule",
        "template",
        "template_opgegeven",
        "partituur",
        "bron",
        "gelegenheid",
        "gelegenheden",
        "zoektekst",
        "do",
        "mode",
        "tempo",
        "afspelen",
        "corpus_id",
        "gebruikt-in",
    }
)

_KEY_ORDER = (
    "titel",
    "taal",
    "soort",
    "toon",
    "formule",
    "template",
    "template_opgegeven",
    "partituur",
    "bron",
    "gelegenheid",
    "gelegenheden",
    "zoektekst",
    "do",
    "mode",
    "tempo",
    "afspelen",
    "corpus_id",
    "gebruikt-in",
)


class VsaKuiserError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


@dataclass(frozen=True)
class VsaKuiserWarning:
    line: int
    column: int
    message: str

    def format(self, path: Path | None = None) -> str:
        loc = f"{path}:" if path else ""
        return f"{loc}{self.line}:{self.column}: WARNING: {self.message}"


@dataclass
class VsaKuiserResult:
    text: str
    warnings: list[VsaKuiserWarning]


def kuiser_vsa_text(
    text: str,
    *,
    source_path: Path | str | None = None,
    werkbank: bool = False,
    dict_interactive: bool | None = None,
) -> VsaKuiserResult:
    """V5 → V3/V4 → V1/V2 → V7 (validate). Geen ``vsa format``."""
    warnings: list[VsaKuiserWarning] = []

    # V5: banners (zelfde strip als MVSA Q6) + lege/ongedocumenteerde FM.
    prepared = apply_q6(text, werkbank=werkbank)
    prepared = _apply_v5_frontmatter(prepared, werkbank=werkbank)

    # V3 + V4
    prepared, dict_warns = _apply_v3_v4(
        prepared,
        dict_interactive=dict_interactive,
        source_path=source_path,
    )
    warnings.extend(dict_warns)

    # V1 + V2
    prepared = _apply_v1_v2(prepared, source_path=source_path)

    _assert_v7_valid_text(prepared, source_path=source_path)
    return VsaKuiserResult(text=prepared, warnings=warnings)


def kuiser_vsa_path(
    path: Path,
    out: Path | None = None,
    *,
    check: bool = False,
    werkbank: bool = False,
    dict_interactive: bool | None = None,
) -> tuple[bool, list[VsaKuiserWarning]]:
    """Kuis ``path``. Returns ``(changed, warnings)``."""
    text = path.read_text(encoding="utf-8-sig")
    result = kuiser_vsa_text(
        text,
        source_path=path,
        werkbank=werkbank,
        dict_interactive=dict_interactive,
    )
    changed = result.text != text
    if check:
        return changed, result.warnings
    target = out if out is not None else path
    if changed or out is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.text, encoding="utf-8", newline="\n")
        _assert_v7_valid_path(target)
    return changed, result.warnings


def _apply_v5_frontmatter(text: str, *, werkbank: bool) -> str:
    if werkbank:
        return text
    bom = ""
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]
    fm, body, _ = strip_yaml_frontmatter(text)
    if not fm:
        return bom + text
    cleaned = _strip_empty_and_unknown(fm)
    if cleaned == fm and text.startswith("---"):
        # Zelfde sleutels; mogelijk alleen volgorde — dump als inhoud gelijk.
        if _fm_shallow_equal(fm, cleaned):
            return bom + text
    if not cleaned:
        return bom + body
    return bom + _dump_fm(cleaned) + body


def _strip_empty_and_unknown(fm: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in fm.items():
        if key not in _DOCUMENTED_KEYS:
            continue
        if val is None or val == "" or val == {} or val == []:
            continue
        if key == "bron" and isinstance(val, dict):
            bron = {
                k: v
                for k, v in val.items()
                if v not in (None, "", {}, [])
            }
            if bron:
                out["bron"] = bron
            continue
        if key == "partituur" and isinstance(val, dict):
            part = {
                k: v
                for k, v in val.items()
                if v not in (None, "", {}, [])
            }
            if part:
                out["partituur"] = part
            continue
        out[key] = val
    # title → titel
    if "titel" not in out and isinstance(out.get("title"), str):
        out["titel"] = out.pop("title")
    elif "title" in out and "titel" in out:
        out.pop("title", None)
    return out


def _fm_shallow_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a == b


def _apply_v3_v4(
    text: str,
    *,
    dict_interactive: bool | None,
    source_path: Path | str | None,
) -> tuple[str, list[VsaKuiserWarning]]:
    result = syllabify_vsa_source(text)
    out = result.text
    interactive = (
        is_interactive_stdin()
        if dict_interactive is None
        else dict_interactive
    )
    findings = find_dictionary_syllable_issues(out)
    actionable = [
        f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
    ]
    if interactive and actionable:
        from .input_paths import source_id_for_prompt

        sid = (
            source_id_for_prompt(Path(source_path))
            if source_path is not None
            else None
        )
        session = prompt_dictionary_fixes(
            actionable, source_id=sid, source_path=source_path
        )
        if session.replacements:
            out = apply_replacements_to_source(out, session.replacements)
            out = syllabify_vsa_source(out).text
            findings = find_dictionary_syllable_issues(out)
        if session.aborted:
            warnings = [
                VsaKuiserWarning(
                    1,
                    1,
                    "VSA-SYLLABLE-DICT-ABORTED: Interactieve "
                    "syllable-dictionary-check afgebroken (Esc).",
                )
            ]
            return out, warnings

    warnings: list[VsaKuiserWarning] = []
    for finding in findings:
        if finding.code not in {CODE_MISMATCH, CODE_UNKNOWN}:
            continue
        warnings.append(
            VsaKuiserWarning(
                finding.line,
                finding.column,
                f"{finding.code}: {finding.message_nl}",
            )
        )
    return out, warnings


def _apply_v1_v2(
    text: str, *, source_path: Path | str | None
) -> str:
    bom = ""
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    old_fm, body, _ = strip_yaml_frontmatter(text)
    soort, toon = _resolve_soort_toon(old_fm, source_path)

    new_fm: dict[str, Any] = {
        k: v
        for k, v in old_fm.items()
        if k
        not in {
            "titel",
            "title",
            "taal",
            "soort",
            "toon",
            "zoektekst",
            "do",
            "mode",
            "tempo",
            "bron",
        }
        and v not in (None, "", {}, [])
    }

    title = _title_from_fm_or_path(old_fm, source_path, toon)
    if title:
        new_fm["titel"] = title

    taal = old_fm.get("taal")
    if isinstance(taal, str) and taal.strip():
        new_fm["taal"] = taal.strip()
    else:
        new_fm["taal"] = "nl"

    if soort:
        new_fm["soort"] = soort
    if toon is not None:
        new_fm["toon"] = toon

    bron = _merge_bron(old_fm.get("bron"), source_path)
    if bron:
        new_fm["bron"] = bron

    # do/mode: alleen behouden, niet verzinnen.
    do = old_fm.get("do")
    if isinstance(do, str) and do.strip():
        new_fm["do"] = do.strip()
    mode = old_fm.get("mode")
    if isinstance(mode, str) and mode.strip():
        new_fm["mode"] = mode.strip()

    tempo = _resolve_tempo(old_fm.get("tempo"), soort)
    if tempo is not None:
        new_fm["tempo"] = tempo

    # Zoektekst ná FM-dump via apply op voorlopige tekst.
    ordered = _order_meta(new_fm)
    provisional = bom + _dump_fm(ordered) + body if ordered else bom + body
    zt = expected_zoektekst(provisional, kind="vsa")
    if zt:
        ordered["zoektekst"] = LiteralZoektekst(zt)
        ordered = _order_meta(ordered)

    if not ordered:
        return bom + body
    return bom + _dump_fm(ordered) + body


def _resolve_soort_toon(
    fm: dict[str, Any], source_path: Path | str | None
) -> tuple[str | None, int | None]:
    soort = fm.get("soort") if isinstance(fm.get("soort"), str) else None
    toon_raw = fm.get("toon")
    toon: int | None = None
    if isinstance(toon_raw, int) and 1 <= toon_raw <= 8:
        toon = toon_raw
    elif isinstance(toon_raw, str) and toon_raw.strip().isdigit():
        n = int(toon_raw.strip())
        if 1 <= n <= 8:
            toon = n
    if source_path is not None:
        derived = _soort_toon_from_source_name(str(source_path))
        if soort is None:
            soort = derived.get("soort")
        if toon is None and isinstance(derived.get("toon"), int):
            toon = derived["toon"]
        if soort is None:
            stem = Path(source_path).stem.lower()
            m = re.match(r"^([a-z0-9]+)-toon-[1-8](?:-|$)", stem)
            if m:
                soort = m.group(1)
    return soort, toon


def _title_from_fm_or_path(
    fm: dict[str, Any],
    source_path: Path | str | None,
    toon: int | None,
) -> str | None:
    from .mvsa_kuiser_q23 import _title_from_fm_or_path as _mvsa_title

    return _mvsa_title(fm, source_path, toon)


def _merge_bron(
    existing: Any, source_path: Path | str | None
) -> dict[str, str] | None:
    from .mvsa_kuiser_q1 import _merge_bron as _mvsa_merge

    return _mvsa_merge(existing, source_path)


def _resolve_tempo(raw: Any, soort: str | None) -> int | None:
    bpm: int | None = None
    if isinstance(raw, int):
        bpm = raw
    elif isinstance(raw, str) and raw.strip().isdigit():
        bpm = int(raw.strip())
    if should_replace_tempo(bpm):
        return kuiser_tempo_for_soort(soort)
    return bpm


def _order_meta(meta: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _KEY_ORDER:
        if key in meta:
            out[key] = meta[key]
    for key, val in meta.items():
        if key not in out:
            out[key] = val
    return out


def _dump_fm(meta: dict[str, Any]) -> str:
    dumped = yaml.dump(
        meta,
        Dumper=_ZoektekstDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=88,
    )
    if not dumped.endswith("\n"):
        dumped += "\n"
    return f"---\n{dumped}---\n\n"


def _assert_v7_valid_text(
    text: str, *, source_path: Path | str | None
) -> None:
    """Valideer via tijdelijk pad of in-memory file helper."""
    import tempfile

    suffix = ".vsa"
    if source_path is not None:
        suffix = Path(source_path).suffix or ".vsa"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=suffix,
        delete=False,
        newline="\n",
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    try:
        _assert_v7_valid_path(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _assert_v7_valid_path(path: Path) -> None:
    result = validate_file(path)
    errors = [m for m in result.messages if m.severity == "error"]
    if errors:
        first = errors[0]
        raise VsaKuiserError(
            f"{first.code}: {first.message_nl}",
            line=getattr(first, "line", 0) or 0,
        )
