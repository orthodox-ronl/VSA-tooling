"""Headless OSMD MusicXML → SVG (``mvsa svg --engine osmd``).

Keten: ``.mvsa`` → Score-IR → from-ir MusicXML → Node ``scripts/osmd-svg/render.mjs``.
Geen MuseScore. Vereist Node + ``npm install`` in ``scripts/osmd-svg``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .atomic_io import write_text
from .score_ir import export_mvsa_path_to_score_ir
from .score_ir_musicxml import score_ir_json_to_musicxml

__all__ = [
    "OsmdSvgError",
    "SVG_ENGINES",
    "normalize_svg_engine",
    "find_osmd_render_script",
    "render_musicxml_to_svg",
    "export_mvsa_to_osmd_svg",
]

SVG_ENGINES: tuple[str, ...] = ("musescore", "osmd")


class OsmdSvgError(Exception):
    """OSMD SVG export failed (Node, puppeteer, or MusicXML)."""


def normalize_svg_engine(name: str | None) -> str:
    if name is None or not str(name).strip():
        return "musescore"
    key = str(name).strip().lower()
    if key not in SVG_ENGINES:
        known = ", ".join(SVG_ENGINES)
        raise OsmdSvgError(
            f"onbekende SVG-engine {name!r} (verwacht: {known})"
        )
    return key


def find_osmd_render_script() -> Path:
    """Locate ``scripts/osmd-svg/render.mjs`` (or ``VSA_OSMD_RENDER``)."""
    env = os.environ.get("VSA_OSMD_RENDER")
    if env:
        p = Path(env).expanduser()
        if not p.is_file():
            raise OsmdSvgError(f"VSA_OSMD_RENDER is geen bestand: {p}")
        return p.resolve()

    here = Path(__file__).resolve()
    roots = [here.parents[2], Path.cwd()]
    seen: set[Path] = set()
    for root in roots:
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)
        candidate = root / "scripts" / "osmd-svg" / "render.mjs"
        if candidate.is_file():
            return candidate
    raise OsmdSvgError(
        "scripts/osmd-svg/render.mjs niet gevonden. "
        "Zet VSA_OSMD_RENDER of werk vanuit de VSA-tooling-repo."
    )


def render_musicxml_to_svg(
    musicxml: Path,
    out: Path,
    *,
    node: Path | None = None,
    timeout_s: float = 180.0,
) -> Path:
    """Run headless OSMD: ``musicxml`` → ``out`` (.svg)."""
    musicxml = Path(musicxml).resolve()
    out = Path(out)
    if out.suffix.lower() != ".svg":
        out = out.with_suffix(".svg")
    out = out.resolve()
    if not musicxml.is_file():
        raise OsmdSvgError(f"MusicXML niet gevonden: {musicxml}")

    node_bin = Path(node) if node else None
    if node_bin is None:
        which = shutil.which("node")
        if not which:
            raise OsmdSvgError(
                "Node.js niet gevonden op PATH (nodig voor --engine osmd)"
            )
        node_bin = Path(which)

    script = find_osmd_render_script()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Absolute paden: render.mjs draait met cwd=scripts/osmd-svg.
        proc = subprocess.run(
            [str(node_bin), str(script), str(musicxml), str(out)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            cwd=str(script.parent),
        )
    except subprocess.TimeoutExpired as exc:
        raise OsmdSvgError(
            f"OSMD-render time-out na {timeout_s:.0f}s"
        ) from exc
    except OSError as exc:
        raise OsmdSvgError(f"kon Node niet starten: {exc}") from exc

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise OsmdSvgError(
            err or f"OSMD-render faalde (exit {proc.returncode})"
        )
    if not out.is_file() or out.stat().st_size < 32:
        raise OsmdSvgError(f"OSMD schreef geen bruikbare SVG: {out}")
    return out


def export_mvsa_to_osmd_svg(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    bibliotheek_id: str | None = None,
    keep_musicxml: Path | None = None,
    node: Path | None = None,
) -> list[Path]:
    """``.mvsa`` → Score-IR → from-ir MusicXML → OSMD SVG.

    Returns ``[out]``.
    """
    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".svg":
        out = out.with_suffix(".svg")
    if path.suffix.lower() != ".mvsa":
        raise OsmdSvgError(f"--engine osmd verwacht .mvsa, kreeg: {path.name}")

    tmp_ir: Path | None = None
    tmp_xml: Path | None = None
    try:
        fd, name = tempfile.mkstemp(suffix=".score-ir.json", prefix="mvsa-osmd-")
        os.close(fd)
        tmp_ir = Path(name)
        export_mvsa_path_to_score_ir(
            path,
            tmp_ir,
            section_id=section_id,
            bibliotheek_id=bibliotheek_id,
        )
        xml_text = score_ir_json_to_musicxml(
            tmp_ir.read_text(encoding="utf-8")
        )

        if keep_musicxml is not None:
            xml_path = Path(keep_musicxml)
            # from-ir is plain MusicXML (geen gezipte .mxl).
            if xml_path.suffix.lower() in {"", ".mxl"}:
                xml_path = xml_path.with_suffix(".musicxml")
            elif xml_path.suffix.lower() not in {".musicxml", ".xml"}:
                xml_path = xml_path.with_suffix(".musicxml")
            xml_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            fd, name = tempfile.mkstemp(
                suffix=".musicxml", prefix="mvsa-osmd-"
            )
            os.close(fd)
            tmp_xml = Path(name)
            xml_path = tmp_xml

        write_text(xml_path, xml_text, encoding="utf-8", newline="\n")
        render_musicxml_to_svg(xml_path, out, node=node)
        return [out]
    finally:
        if tmp_ir is not None:
            tmp_ir.unlink(missing_ok=True)
        if tmp_xml is not None:
            tmp_xml.unlink(missing_ok=True)
