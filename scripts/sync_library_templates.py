#!/usr/bin/env python3
"""Houd library ``template.mxl`` / ``template.mscz`` synchroon met ``template.yaml``.

Canonieke bron per formule: ``docs/.../library/<id>/template.yaml``.
Afgeleiden staan naast die YAML. Na elke YAML-wijziging:

  python scripts\\sync_library_templates.py
  python scripts\\sync_library_templates.py tropaar-toon-4 groningen-tropaar-toon-4
  python scripts\\sync_library_templates.py --check

``--check`` schrijft niets; exit 1 als een afgeleide ontbreekt of afwijkt.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
LIBRARY = REPO / "docs" / "specification-vsa-templates" / "library"

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import render_vsa_template_musicxml as render  # noqa: E402
from vsa.musicxml_package import write_musicxml_output  # noqa: E402


def _is_same_as_alias(yaml_path: Path) -> bool:
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return isinstance(doc, dict) and "same_as" in doc


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zip_payload_digest(path: Path) -> str:
    """SHA van gesorteerde zip-entries (inhoud); negeert zip-tijdstempels."""
    parts: list[bytes] = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            parts.append(name.encode("utf-8"))
            parts.append(zf.read(name))
    return _digest(b"\0".join(parts))


def _write_pair(yaml_path: Path) -> tuple[Path, Path]:
    doc = render.load_resolved(yaml_path, LIBRARY)
    mxl = yaml_path.with_name("template.mxl")
    mscz = yaml_path.with_name("template.mscz")
    write_musicxml_output(mxl, render.render_template_musicxml(doc))
    render.write_mscx_output(mscz, render.render_template_mscx(doc))
    return mxl, mscz


def _check_pair(yaml_path: Path) -> list[str]:
    errors: list[str] = []
    doc = render.load_resolved(yaml_path, LIBRARY)
    mxl = yaml_path.with_name("template.mxl")
    mscz = yaml_path.with_name("template.mscz")
    if not mxl.is_file():
        errors.append(f"ontbreekt: {mxl.relative_to(REPO)}")
    if not mscz.is_file():
        errors.append(f"ontbreekt: {mscz.relative_to(REPO)}")
    if errors:
        return errors

    # Vergelijk met verse render-bytes in geheugen via tijdelijke bestanden
    # in de map zelf is riskant; herschrijf naar BytesIO-achtig via temp paths
    # onder REPO/generated (kortstondig).
    tmp_dir = REPO / "generated" / "_template-sync-check"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        fresh_mxl = tmp_dir / f"{yaml_path.parent.name}.mxl"
        fresh_mscz = tmp_dir / f"{yaml_path.parent.name}.mscz"
        write_musicxml_output(fresh_mxl, render.render_template_musicxml(doc))
        render.write_mscx_output(fresh_mscz, render.render_template_mscx(doc))
        hint = (
            f"(run: python scripts\\sync_library_templates.py "
            f"{yaml_path.parent.name})"
        )
        if _zip_payload_digest(mxl) != _zip_payload_digest(fresh_mxl):
            errors.append(f"verouderd t.o.v. YAML: {mxl.relative_to(REPO)} {hint}")
        if _zip_payload_digest(mscz) != _zip_payload_digest(fresh_mscz):
            errors.append(f"verouderd t.o.v. YAML: {mscz.relative_to(REPO)} {hint}")
    finally:
        for p in tmp_dir.glob(f"{yaml_path.parent.name}.*"):
            p.unlink(missing_ok=True)
    return errors


def iter_yaml_paths(ids: list[str] | None) -> list[Path]:
    if not ids:
        return sorted(LIBRARY.glob("*/template.yaml"))
    paths: list[Path] = []
    for tid in ids:
        p = LIBRARY / tid / "template.yaml"
        if not p.is_file():
            raise SystemExit(f"onbekend template-id / ontbrekende YAML: {tid}")
        paths.append(p)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync library template.mxl/.mscz from template.yaml"
    )
    parser.add_argument(
        "ids",
        nargs="*",
        help="Library-mapnamen (default: alle met template.yaml)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Alleen controleren; exit 1 bij ontbrekend/verouderd",
    )
    args = parser.parse_args()
    paths = iter_yaml_paths(args.ids or None)

    if args.check:
        all_err: list[str] = []
        for yp in paths:
            if _is_same_as_alias(yp):
                print(f"skip alias {yp.parent.name} (same_as)")
                continue
            errs = _check_pair(yp)
            if errs:
                print(f"{yp.parent.name}:")
                for e in errs:
                    print(f"  {e}")
                all_err.extend(errs)
            else:
                print(f"OK {yp.parent.name}")
        return 1 if all_err else 0

    for yp in paths:
        if _is_same_as_alias(yp):
            print(f"skip alias {yp.parent.name} (same_as)")
            continue
        mxl, mscz = _write_pair(yp)
        print(f"wrote {mxl.relative_to(REPO)}")
        print(f"wrote {mscz.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
