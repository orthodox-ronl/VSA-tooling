"""Genereer tropaar-toon-4-hemelum: formuleblad en/of corpus VSA → MSCZ/MXL/(PDF).

Canonieke artefacten onder ``library/tropaar-toon-4-hemelum/``:

- ``template.yaml`` — formule-bron (git)
- ``template.mscz`` — formuleblad voor MuseScore-controle (git)
- ``template.mxl`` — formule MusicXML om te delen (git)
- ``template.pdf`` — print (lokaal; ``*.pdf`` in .gitignore)
- ``examples/corpus/*.vsa`` — bronteksten (git)
- ``examples/corpus/*.mscz`` / ``*.mxl`` — instance (git)
- ``examples/corpus/*.pdf`` — print (lokaal)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIBRARY = REPO / "docs" / "specification-vsa-templates" / "library"
TEMPLATE_DIR = LIBRARY / "tropaar-toon-4-hemelum"
TEMPLATE_YAML = TEMPLATE_DIR / "template.yaml"
ONDERZOEK = REPO / "docs" / "plans" / "onderzoeks-troparen-en-kondaken.md"
CORPUS_DIR = TEMPLATE_DIR / "examples" / "corpus"

MUSESCORE_CANDIDATES = (
    Path(r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"),
    Path(r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe"),
)

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import render_vsa_template_musicxml as render  # noqa: E402

from vsa.corpus_vsa import load_corpus, load_corpus_from_vsa_dir, write_vsa_file  # noqa: E402
from vsa.template_instance import TemplateInstanceError, map_vsa_to_template  # noqa: E402
from vsa.yaml_frontmatter import parse_vsa_frontmatter  # noqa: E402


def find_musescore() -> Path | None:
    which = shutil.which("MuseScore4") or shutil.which("mscore")
    if which:
        return Path(which)
    for path in MUSESCORE_CANDIDATES:
        if path.is_file():
            return path
    return None


def export_pdf(mscz: Path, *, musescore: Path) -> Path:
    """MuseScore CLI: mscz → pdf naast het bronbestand."""
    pdf = mscz.with_suffix(".pdf")
    subprocess.run(
        [str(musescore), "-f", "-o", str(pdf), str(mscz)],
        check=True,
    )
    if not pdf.is_file():
        raise RuntimeError(f"MuseScore did not write {pdf}")
    return pdf


def instance_title(vsa_path: Path, vsa_text: str) -> str:
    """Titel = frontmatter ``title``, anders bestandsstem (zonder extensie)."""
    frontmatter, _ = parse_vsa_frontmatter(vsa_text)
    raw = frontmatter.get("title")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return vsa_path.stem


def render_instance(
    doc: dict,
    piece,
    *,
    output_dir: Path,
    write_vsa: bool,
    musescore: Path | None = None,
) -> Path:
    """Uitgewerkt zangstuk: S=VSA, A/T/B=template → .vsa/.mscz/.mxl/[.pdf]."""
    stem = piece.filename_stem()
    vsa_path = output_dir / f"{stem}.vsa"
    if write_vsa or not vsa_path.exists():
        write_vsa_file(piece, vsa_path)
    vsa_text = vsa_path.read_text(encoding="utf-8")

    mapped = map_vsa_to_template(doc, vsa_text, source=str(vsa_path))
    title = instance_title(vsa_path, vsa_text)
    mscx = render.render_instance_mscx(doc, mapped, title=title)
    out = output_dir / f"{stem}.mscz"
    render.write_mscx_output(out, mscx)

    from vsa.musicxml_package import write_musicxml_output

    xml = render.render_instance_musicxml(doc, mapped, title=title)
    write_musicxml_output(output_dir / f"{stem}.mxl", xml)

    if musescore is not None:
        pdf = export_pdf(out, musescore=musescore)
        print(f"wrote {pdf.relative_to(REPO)}")
    return out


def render_template_artefacts(doc: dict, *, musescore: Path | None = None) -> Path:
    """Formuleblad → template.mscz + template.mxl (+ optioneel PDF)."""
    from vsa.musicxml_package import write_musicxml_output

    mscx = render.render_template_mscx(doc)
    out = TEMPLATE_DIR / "template.mscz"
    render.write_mscx_output(out, mscx)
    write_musicxml_output(TEMPLATE_DIR / "template.mxl", render.render_template_musicxml(doc))
    print(f"wrote {(TEMPLATE_DIR / 'template.mxl').relative_to(REPO)}")
    if musescore is not None:
        pdf = export_pdf(out, musescore=musescore)
        print(f"wrote {pdf.relative_to(REPO)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Tropaar-toon-4: corpus (.vsa → .mscz/.mxl/[.pdf]) "
            "en/of formuleblad (template.mscz + template.mxl)."
        )
    )
    parser.add_argument(
        "--onderzoek",
        type=Path,
        default=ONDERZOEK,
        help="Bron: onderzoeks-troparen-en-kondaken.md (alleen zonder --no-vsa)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=CORPUS_DIR,
        help="Uitvoermap voor corpus (.vsa/.mscz/.mxl)",
    )
    parser.add_argument(
        "--id",
        dest="piece_id",
        help="Alleen dit corpus-id (bijv. T4-06)",
    )
    parser.add_argument(
        "--from-onderzoek",
        action="store_true",
        help=(
            "Extraheer .vsa opnieuw uit onderzoeks-md (overschrijft corpus-.vsa). "
            "Default: bestaande examples/corpus/*.vsa gebruiken."
        ),
    )
    parser.add_argument(
        "--no-vsa",
        action="store_true",
        help=argparse.SUPPRESS,  # legacy alias: zelfde als default
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Alleen formuleblad: template.mscz + template.mxl (geen corpus)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Exporteer .mscz → .pdf via MuseScore CLI",
    )
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="Alleen bestaande .mscz naar .pdf (geen re-render)",
    )
    args = parser.parse_args()
    output_dir = args.output_dir

    musescore: Path | None = None
    if args.pdf or args.pdf_only:
        musescore = find_musescore()
        if musescore is None:
            raise SystemExit(
                "MuseScore niet gevonden (verwacht o.a. "
                r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe)"
            )
        print(f"using {musescore}")

    if args.pdf_only:
        paths = sorted(output_dir.glob("T4-*.mscz"))
        template_mscz = TEMPLATE_DIR / "template.mscz"
        if template_mscz.is_file() and template_mscz not in paths:
            paths.append(template_mscz)
        if not paths:
            raise SystemExit(f"geen T4-*.mscz in {output_dir}")
        assert musescore is not None
        for mscz in paths:
            pdf = export_pdf(mscz, musescore=musescore)
            print(f"wrote {pdf.relative_to(REPO)}")
        return 0

    doc = render.load_resolved(TEMPLATE_YAML, LIBRARY)

    if args.template:
        out = render_template_artefacts(doc, musescore=musescore)
        print(f"wrote {out.relative_to(REPO)} (template)")
        return 0

    if args.from_onderzoek:
        pieces = load_corpus(args.onderzoek)
        write_vsa = True
    else:
        pieces = load_corpus_from_vsa_dir(output_dir)
        write_vsa = False
    if args.piece_id:
        pieces = [p for p in pieces if p.piece_id == args.piece_id]
        if not pieces:
            raise SystemExit(f"unknown corpus id: {args.piece_id!r}")

    failures: list[str] = []
    for piece in pieces:
        try:
            out = render_instance(
                doc,
                piece,
                output_dir=output_dir,
                write_vsa=write_vsa,
                musescore=musescore,
            )
            print(f"wrote {out.relative_to(REPO)}")
        except TemplateInstanceError as exc:
            for line in exc.format_lines():
                print(line, file=sys.stderr)
            msg = f"{piece.piece_id}: {exc.code}"
            failures.append(msg)
            print(f"FAILED {msg}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            msg = f"{piece.piece_id}: {exc}"
            failures.append(msg)
            print(f"FAILED {msg}", file=sys.stderr)

    if failures:
        print(f"{len(failures)} failed:", file=sys.stderr)
        for msg in failures:
            print(f"  {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
