"""Zoektekst in YAML-frontmatter van canonieke ``.vsa`` / ``.mvsa``.

Contract: ``docs/formats/zoektekst.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from .text_export import plain_text_from_mvsa, plain_text_from_vsa
from .vsa_stanzas import ensure_stanza_stars
from .yaml_frontmatter import strip_yaml_frontmatter

SourceKind = Literal["vsa", "mvsa"]

_WS_RE = re.compile(r"\s+")
_FM_OPEN_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n?", re.DOTALL)


class LiteralZoektekst(str):
    """Marker voor PyYAML: dump als literal block scalar (``|``), frase per regel."""


class _ZoektekstDumper(yaml.SafeDumper):
    pass


def _represent_literal(
    dumper: yaml.SafeDumper, data: LiteralZoektekst
) -> yaml.Node:
    # Chomp ``-``: geen extra newline na het blok in de YAML-waarde.
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", str(data), style="|"
    )


_ZoektekstDumper.add_representer(LiteralZoektekst, _represent_literal)

# Back-compat alias (oude imports/tests).
FoldedZoektekst = LiteralZoektekst


@dataclass(frozen=True)
class ZoektekstIssue:
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


@dataclass(frozen=True)
class ZoektekstApplyResult:
    text: str
    changed: bool
    expected: str
    previous: str | None


def normalize_zoektekst(text: str) -> str:
    """Leading/trailing strip; interne witruimte → één spatie (equivalentie)."""
    return _WS_RE.sub(" ", (text or "").strip())


def format_zoektekst(text: str) -> str:
    """Behoud frase-regels; witruimte binnen een regel → één spatie."""
    lines: list[str] = []
    for ln in (text or "").replace("\r\n", "\n").split("\n"):
        cleaned = _WS_RE.sub(" ", ln.strip())
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def kind_from_path(path: Path | str) -> SourceKind:
    suffix = Path(path).suffix.lower()
    if suffix == ".vsa":
        return "vsa"
    if suffix == ".mvsa":
        return "mvsa"
    raise ValueError(f"verwacht .vsa of .mvsa; kreeg {Path(path).suffix!r}")


def plain_text_for_zoektekst(source: str, *, kind: SourceKind) -> str:
    """Body-extractie met frasering (één regel per frase waar mogelijk).

    Frontmatter/zoektekst telt niet mee. Voor ``.vsa``: zelfde frasescheiding
    als mapping/validatie — ``*`` / ``/`` / ``**`` / ``//`` (spaties optioneel,
    ook vastgeplakt: ``.*``) via ``ensure_stanza_stars`` +
    ``extract_stanza_notes`` / ``plain_text_from_vsa``.
    """
    if kind == "mvsa":
        return plain_text_from_mvsa(source)

    text = source[1:] if source.startswith("\ufeff") else source
    _meta, body, _base = strip_yaml_frontmatter(text)
    # Zelfde frasegrenzen als vsa mvsa / extract_stanza_notes (T4 / VSA-stanzas).
    norm_body, _notes = ensure_stanza_stars(body)
    m = _FM_OPEN_RE.match(text)
    if m:
        rebuilt = text[: m.end()] + norm_body
    else:
        rebuilt = norm_body
    return plain_text_from_vsa(rebuilt)


def expected_zoektekst(source: str, *, kind: SourceKind) -> str:
    """Canonieke schrijfvorm: frase per regel (genormaliseerd per regel)."""
    return format_zoektekst(plain_text_for_zoektekst(source, kind=kind))


def zoektekst_from_frontmatter(meta: dict[str, Any]) -> str | None:
    if "zoektekst" not in meta:
        return None
    value = meta.get("zoektekst")
    if value is None:
        return ""
    return str(value)


def check_zoektekst(
    source: str,
    *,
    kind: SourceKind,
    require: bool = True,
) -> list[ZoektekstIssue]:
    """Controleer ``zoektekst`` t.o.v. body-extractie.

    ``require``: bij niet-lege verwachte tekst is ontbrekend veld een error.
    Zonder ``require`` alleen mismatch als het veld wél aanwezig is.
    """
    expected = expected_zoektekst(source, kind=kind)
    meta, _body, _base = strip_yaml_frontmatter(
        source[1:] if source.startswith("\ufeff") else source
    )
    current_raw = zoektekst_from_frontmatter(meta)
    if current_raw is None:
        if require and expected:
            return [
                ZoektekstIssue(
                    "ZOEKTEKST-MISSING",
                    "ontbrekende zoektekst (verwacht platte gezongen tekst "
                    "in YAML-frontmatter)",
                )
            ]
        return []
    current = normalize_zoektekst(current_raw)
    if current != normalize_zoektekst(expected):
        return [
            ZoektekstIssue(
                "ZOEKTEKST-MISMATCH",
                "zoektekst wijkt af van body-extractie (vsa text, genormaliseerd)",
            )
        ]
    return []


def apply_zoektekst(source: str, *, kind: SourceKind) -> ZoektekstApplyResult:
    """Schrijf of update ``zoektekst``; overige frontmatter blijft (via dump).

    Herschrijft alleen bij inhoudelijke wijziging (genormaliseerde vergelijking),
    zodat een tweede run geen YAML-opmaak-churn veroorzaakt.
    """
    bom = ""
    text = source
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    expected = expected_zoektekst(text, kind=kind)
    meta, body, _base = strip_yaml_frontmatter(text)
    previous_raw = zoektekst_from_frontmatter(meta)
    previous_fmt = (
        None if previous_raw is None else format_zoektekst(previous_raw)
    )
    previous = (
        None if previous_raw is None else normalize_zoektekst(previous_raw)
    )

    # Ontbrekend veld + geen gezongen tekst → niets te doen.
    if previous_fmt is None and not expected:
        return ZoektekstApplyResult(
            text=source,
            changed=False,
            expected=expected,
            previous=previous,
        )
    # Ook herschrijven als alleen de frasering/opmaak afwijkt, of als het
    # veld niet als literal ``|`` / ``|-`` staat (folded/quoted alinea).
    style_ok = bool(
        re.search(r"(?m)^zoektekst:\s*\|-?\s*$", text)
    )
    if previous_fmt == expected and style_ok:
        return ZoektekstApplyResult(
            text=source,
            changed=False,
            expected=expected,
            previous=previous,
        )

    new_meta: dict[str, Any] = {
        k: v for k, v in meta.items() if k != "zoektekst"
    }
    if expected:
        new_meta["zoektekst"] = LiteralZoektekst(expected)

    if not new_meta:
        new_text = bom + body
    else:
        yaml_body = yaml.dump(
            new_meta,
            Dumper=_ZoektekstDumper,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=88,
        )
        if not yaml_body.endswith("\n"):
            yaml_body += "\n"
        new_text = f"{bom}---\n{yaml_body}---\n\n{body}"

    return ZoektekstApplyResult(
        text=new_text,
        changed=True,
        expected=expected,
        previous=previous,
    )


def iter_vsa_mvsa_files(path: Path) -> list[Path]:
    """Bestand of map → gesorteerde ``.vsa`` / ``.mvsa``-paden."""
    from .input_paths import InputPathError, collect_input_files

    path = Path(path)
    try:
        return collect_input_files(path, suffixes=(".vsa", ".mvsa"))
    except InputPathError as exc:
        if not path.exists():
            raise FileNotFoundError(str(path)) from exc
        if path.is_file():
            raise ValueError(
                f"verwacht .vsa of .mvsa; kreeg {path.suffix!r}"
            ) from exc
        raise ValueError(str(exc)) from exc
