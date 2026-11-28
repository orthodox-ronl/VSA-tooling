"""Handhaving G2: CLI-entrypoints gebruiken gedeelde padhelpers.

Norm: docs/reference/cli/input-pad.md (mijlpaal 5).
Verboden: ad-hoc ``.rglob(`` in ``cli*.py`` zonder ``# G2-allow:``-markering.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src" / "vsa"

_CLI_ENTRYPOINTS = (
    "cli.py",
    "cli_mxl.py",
    "cli_mscz.py",
    "cli_md.py",
    "cli_import.py",
    "cli_score_to_mvsa.py",
)

_HELPER_MARKERS = (
    "collect_cli_sources",
    "resolve_cli_path",
    "_cli_collect_sources",
    "_cli_resolve_existing",
    "validate_path",
)

_RGLOB_RE = re.compile(r"\.rglob\s*\(")
_ALLOW_RE = re.compile(r"G2-allow:")


def _cli_paths() -> list[Path]:
    return [_SRC / name for name in _CLI_ENTRYPOINTS]


@pytest.mark.parametrize("path", _cli_paths(), ids=_CLI_ENTRYPOINTS)
def test_cli_entrypoint_uses_shared_path_helper(path: Path) -> None:
    """Elk CLI-entrypoint importeert/gebruikt een G2-helper."""
    assert path.is_file(), f"ontbreekt: {path}"
    text = path.read_text(encoding="utf-8")
    assert any(marker in text for marker in _HELPER_MARKERS), (
        f"{path.name}: geen G2-helper ({', '.join(_HELPER_MARKERS)}). "
        "Gebruik collect_cli_sources / resolve_cli_path "
        "(docs/reference/cli/input-pad.md)."
    )


@pytest.mark.parametrize("path", _cli_paths(), ids=_CLI_ENTRYPOINTS)
def test_cli_entrypoint_no_unmarked_rglob(path: Path) -> None:
    """``.rglob(`` alleen met ``# G2-allow:`` op dezelfde of vorige regel."""
    lines = path.read_text(encoding="utf-8").splitlines()
    offenders: list[str] = []
    for i, line in enumerate(lines):
        if _RGLOB_RE.search(line) is None:
            continue
        # Bekende uitzondering: alleen basename template.yaml na padresolutie.
        if 'rglob("template.yaml")' in line or "rglob('template.yaml')" in line:
            continue
        prev = lines[i - 1] if i > 0 else ""
        if _ALLOW_RE.search(line) or _ALLOW_RE.search(prev):
            continue
        offenders.append(f"{path.name}:{i + 1}: {line.strip()}")
    assert not offenders, (
        "Ad-hoc rglob in CLI zonder G2-allow:\n  "
        + "\n  ".join(offenders)
        + "\nGebruik collect_cli_sources, of markeer een bewuste uitzondering "
        "met `# G2-allow: <reden>` "
        "(docs/reference/cli/input-pad.md §Handhaving)."
    )


def test_input_pad_contract_lists_handhaving() -> None:
    """Contractpagina blijft de handhavingsankers noemen."""
    hub = _REPO / "docs" / "reference" / "cli" / "input-pad.md"
    text = hub.read_text(encoding="utf-8")
    assert "Handhaving" in text
    assert "collect_cli_sources" in text
    assert "G1" in text and "G8" in text
