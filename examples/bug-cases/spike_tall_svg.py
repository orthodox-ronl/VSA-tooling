"""Spike B: tall MuseScore-SVG + pagina-PDF uit index.md (shortcodes).

Bronnen in deze map:
  vriendelijk-licht-default-groningen.mscz
  vriendelijk-licht-index.md

Zichtbare artefacten in deze map (niet in een verborgen uitmap):
  vriendelijk-licht-a4-1.svg / -2.svg   — huidige A4-bladreeks
  vriendelijk-licht-tall.svg            — één hoge strip
  vriendelijk-licht-index.md.pdf        — index.md (kop/tekst/bieb) + tall-SVG
  vriendelijk-licht-index-preview.html  — zelfde inhoud in de browser

  python examples/bug-cases/spike_tall_svg.py
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from vsa.mscz_partituur import (  # noqa: E402
    MsczPartituurError,
    strip_mscz_sheet_chrome,
)
from vsa.musescore_cli import (  # noqa: E402
    MuseScoreConvertError,
    MuseScoreNotFoundError,
    convert_with_musescore,
    list_musescore_svg_pages,
)
from vsa.mvsa_mscz import export_mscz_to_svg  # noqa: E402
from vsa.svg_trim import SvgTrimError, trim_musescore_svg  # noqa: E402

HERE = Path(__file__).resolve().parent
MSCZ = HERE / "vriendelijk-licht-default-groningen.mscz"
INDEX_MD = HERE / "vriendelijk-licht-index.md"

STEM = "vriendelijk-licht"
TALL_SVG = HERE / f"{STEM}-tall.svg"
A4_SVG = HERE / f"{STEM}-a4.svg"  # MuseScore maakt -1/-2 bij multi-page
INDEX_PDF = HERE / f"{STEM}-index.md.pdf"
INDEX_HTML = HERE / f"{STEM}-index-preview.html"

_TALL_PAGE_HEIGHT_IN = "40"
_A4_W = 595.28
_A4_H = 841.89
_MARGIN = 28.0

# Hugo: {{< name >}} / {{< /name >}}; tolerant ook {{ /name }} (tikfout).
_SC = re.compile(
    r"\{\{(?:<\s*)?(/?)\s*([a-z0-9_-]+)([^>}]*?)(?:\s*>)?\}\}",
    re.IGNORECASE,
)
_FM = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)
_BIEB_ONDERDELEN = frozenset(
    {"titel", "title", "muziek", "bron", "copyright", "veld"}
)


def _bieb_onderdeel(params: str) -> str | None:
    stripped = re.sub(r'\bid\s*=\s*"[^"]*"', " ", params, flags=re.I)
    for tok in stripped.replace("/", " ").split():
        t = tok.strip().lower()
        if t in _BIEB_ONDERDELEN:
            return t
    return None


@dataclass
class KopItem:
    text: str


@dataclass
class NoteItem:
    text: str


@dataclass
class MusicItem:
    """``bieb`` / ``muziek`` — spike vult dit met de tall-SVG."""

    uv_id: str | None


FlowItem = KopItem | NoteItem | MusicItem


def _strip_frontmatter(text: str) -> str:
    return _FM.sub("", text, count=1)


def parse_index_flow(md_text: str) -> list[FlowItem]:
    """Minimale shortcode-parse: ``kop``, ``bieb``/``muziek``, overige tekst."""
    body = _strip_frontmatter(md_text)
    items: list[FlowItem] = []
    pos = 0
    open_kop = False
    kop_buf: list[str] = []
    open_bieb_id: str | None = None

    def flush_gap(gap: str) -> None:
        text = " ".join(gap.split()).strip()
        if not text:
            return
        if open_kop:
            kop_buf.append(text)
        else:
            items.append(NoteItem(text))

    for m in _SC.finditer(body):
        flush_gap(body[pos : m.start()])
        pos = m.end()
        closing, name, params = m.group(1), m.group(2).lower(), m.group(3)
        if name == "kop":
            if closing:
                text = " ".join(kop_buf).strip()
                if text:
                    items.append(KopItem(text))
                kop_buf.clear()
                open_kop = False
            else:
                open_kop = True
                kop_buf.clear()
            continue
        if open_kop:
            # geneste shortcodes in kop: negeren (alleen platte tekst in kop_buf)
            continue
        if name == "bieb":
            id_m = re.search(r'\bid\s*=\s*"([^"]+)"', params, re.I)
            uv = id_m.group(1) if id_m else None
            ond = _bieb_onderdeel(params)
            if closing:
                # sluitend blok zonder onderdeel → muziek al via {{< muziek >}}
                open_bieb_id = None
                continue
            if "/" in params:
                # self-close: kale bieb / muziek → partituur; copyright/bron → label
                if ond in (None, "muziek"):
                    items.append(MusicItem(uv))
                elif ond == "copyright":
                    items.append(NoteItem("[copyright]"))
                elif ond == "bron":
                    items.append(NoteItem("[bron]"))
                open_bieb_id = None
                continue
            open_bieb_id = uv
            continue
        if name == "muziek" and not closing:
            items.append(MusicItem(open_bieb_id))
            continue
        if name == "copyright" and not closing:
            items.append(NoteItem("[copyright]"))
            continue
        # overige shortcodes: negeren in spike
    flush_gap(body[pos:])
    if open_kop and kop_buf:
        items.append(KopItem(" ".join(kop_buf).strip()))
    return [i for i in items if not (isinstance(i, KopItem) and not i.text)]


def _patch_style_in_mscz(path: Path, overrides: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "r") as zin:
        names = zin.namelist()
        mscx_name = next((n for n in names if n.lower().endswith(".mscx")), None)
        if mscx_name is None:
            raise MsczPartituurError(f"geen .mscx in {path}")
        files = {n: zin.read(n) for n in names}

    def patch_xml(raw: bytes) -> bytes:
        text = raw.decode("utf-8")
        if "<Style>" not in text:
            return raw
        for key, val in overrides.items():
            pat = re.compile(rf"<{key}>.*?</{key}>", re.DOTALL)
            tag = f"<{key}>{val}</{key}>"
            if pat.search(text):
                text = pat.sub(tag, text)
            else:
                text = text.replace("<Style>", f"<Style>{tag}", 1)
        return text.encode("utf-8")

    files[mscx_name] = patch_xml(files[mscx_name])
    for name in list(files):
        if name.lower().endswith(".mss") or name.endswith("score_style.mss"):
            files[name] = patch_xml(files[name])

    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    tmp.replace(path)


def _svg_dims(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    w = re.search(r'\bwidth="([^"]+)"', text)
    h = re.search(r'\bheight="([^"]+)"', text)
    return (w.group(1) if w else "?", h.group(1) if h else "?")


def _svg_page_index(path: Path) -> int:
    m = re.search(r"-(\d+)\.svg$", path.name, re.I)
    return int(m.group(1)) if m else 0


def export_tall_mscz_svg(
    mscz: Path,
    out: Path,
    *,
    page_height_in: str = _TALL_PAGE_HEIGHT_IN,
) -> list[Path]:
    out = Path(out)
    if out.suffix.lower() != ".svg":
        out = out.with_suffix(".svg")
    if out.exists():
        out.unlink()
    for stale in out.parent.glob(f"{out.stem}-*.svg"):
        stale.unlink(missing_ok=True)

    fd, tmp_name = tempfile.mkstemp(suffix=".mscz", prefix="tall-svg-")
    import os

    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copy2(mscz, tmp)
        strip_mscz_sheet_chrome(tmp)
        _patch_style_in_mscz(
            tmp,
            {
                "pageHeight": page_height_in,
                "enableVerticalSpread": "0",
                "maxPageFillSpread": "0",
                "lastSystemFillLimit": "0",
                "showFooter": "0",
                "footerFirstPage": "0",
                "showHeader": "0",
                "headerFirstPage": "0",
            },
        )
        first = convert_with_musescore(tmp, out)
    except (MuseScoreNotFoundError, MuseScoreConvertError, MsczPartituurError):
        tmp.unlink(missing_ok=True)
        raise
    finally:
        tmp.unlink(missing_ok=True)

    pages = list_musescore_svg_pages(out)
    if out.is_file() and not pages:
        written = [out]
    elif pages:
        written = pages
    else:
        written = [first]
    for path in written:
        trimmed = trim_musescore_svg(
            path.read_text(encoding="utf-8"),
            white_background=True,
        )
        path.write_text(trimmed, encoding="utf-8", newline="\n")
    return written


def _staff_line_ys(svg_text: str) -> list[float]:
    """Y-coördinaten van MuseScore ``StaffLines`` (SVG user space)."""
    ys: list[float] = []
    for pat in (
        r'<polyline[^>]*class="StaffLines"[^>]*points="([^"]+)"',
        r'<polyline[^>]*points="([^"]+)"[^>]*class="StaffLines"',
    ):
        for m in re.finditer(pat, svg_text):
            first = m.group(1).split()[0]
            ys.append(float(first.split(",")[1]))
    return sorted({round(y, 2) for y in ys})


def _cluster_systems(staff_ys: list[float], *, gap_min: float = 200.0) -> list[tuple[float, float]]:
    """Per systeem (top, bottom) in SVG-y op basis van staflijn-clusters."""
    if not staff_ys:
        return []
    clusters: list[list[float]] = [[staff_ys[0]]]
    for y in staff_ys[1:]:
        if y - clusters[-1][-1] > gap_min:
            clusters.append([y])
        else:
            clusters[-1].append(y)
    return [(c[0], c[-1]) for c in clusters]


def system_cut_points_pdf(svg_path: Path, pdf_height: float) -> list[float]:
    """Y-snijpunten in PDF-coördinaten (na SVG→PDF), tussen systemen.

    Snede ligt midden in de gap tussen systemen (lyrics-ruimte), zodat een
    pagina nooit midden door een notenbalk eindigt. Laatste punt = ``pdf_height``.
    """
    text = svg_path.read_text(encoding="utf-8")
    vb_m = re.search(r'viewBox="([^"]+)"', text)
    if not vb_m:
        return [pdf_height]
    vb = [float(x) for x in vb_m.group(1).split()]
    min_y, vb_h = vb[1], vb[3]
    if vb_h <= 0:
        return [pdf_height]

    def to_pdf(svg_y: float) -> float:
        return (svg_y - min_y) / vb_h * pdf_height

    systems = _cluster_systems(_staff_line_ys(text))
    if not systems:
        return [pdf_height]

    cuts: list[float] = []
    for i, (_top, bottom) in enumerate(systems):
        if i + 1 < len(systems):
            next_top = systems[i + 1][0]
            mid = (bottom + next_top) / 2.0
        else:
            mid = min_y + vb_h  # onderkant viewBox
        cuts.append(to_pdf(mid))
    # Uniek, oplopend, eindigend op pdf_height
    out = sorted({round(c, 3) for c in cuts if 0 < c <= pdf_height + 1e-6})
    if not out or out[-1] < pdf_height - 0.5:
        out.append(pdf_height)
    else:
        out[-1] = pdf_height
    return out


def compose_index_pdf(
    dest: Path,
    *,
    flow: list[FlowItem],
    tall_svg: Path,
) -> int:
    """Render index-flow naar A4: kop/tekst + tall-SVG, afbreken op systeembrenzen."""
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError(
            "pymupdf ontbreekt (nodig voor de proef-PDF). "
            "Installeer met: python -m pip install pymupdf"
        ) from exc

    svg_doc = pymupdf.open(tall_svg)
    try:
        music_src = pymupdf.open("pdf", svg_doc.convert_to_pdf())
    finally:
        svg_doc.close()

    try:
        sw = music_src[0].rect.width
        sh = music_src[0].rect.height
        content_w = _A4_W - 2 * _MARGIN
        scale = min(content_w / sw, 1.0) if sw > 0 else 1.0
        draw_w = sw * scale
        cuts = system_cut_points_pdf(tall_svg, sh)
        print(
            f"  systeemsnee: {len(cuts)} snijpunt(en) in tall-SVG",
            flush=True,
        )

        doc = pymupdf.open()
        page = doc.new_page(width=_A4_W, height=_A4_H)
        y = _MARGIN

        def new_page() -> None:
            nonlocal page, y
            page = doc.new_page(width=_A4_W, height=_A4_H)
            y = _MARGIN

        def place_music_band(src_y0: float, src_y1: float) -> None:
            nonlocal y
            band_h = (src_y1 - src_y0) * scale
            if band_h <= 1e-6:
                return
            if y + band_h > _A4_H - _MARGIN + 0.5 and y > _MARGIN + 1:
                new_page()
            clip = pymupdf.Rect(0, src_y0, sw, src_y1)
            x0 = _MARGIN + max(0.0, (content_w - draw_w) / 2)
            dest_rect = pymupdf.Rect(x0, y, x0 + draw_w, y + band_h)
            page.show_pdf_page(dest_rect, music_src, 0, clip=clip)
            y += band_h

        for item in flow:
            if isinstance(item, KopItem):
                box_h = 28.0
                if y + box_h > _A4_H - _MARGIN and y > _MARGIN + 1:
                    new_page()
                rc = page.insert_textbox(
                    pymupdf.Rect(_MARGIN, y, _A4_W - _MARGIN, y + box_h),
                    item.text,
                    fontsize=14,
                    align=pymupdf.TEXT_ALIGN_CENTER,
                )
                if rc < 0:
                    raise RuntimeError(f"kop past niet: {item.text!r}")
                y += box_h + 6.0
            elif isinstance(item, NoteItem):
                box_h = 18.0
                if y + box_h > _A4_H - _MARGIN and y > _MARGIN + 1:
                    new_page()
                rc = page.insert_textbox(
                    pymupdf.Rect(_MARGIN, y, _A4_W - _MARGIN, y + box_h),
                    item.text,
                    fontsize=10,
                    align=pymupdf.TEXT_ALIGN_LEFT,
                )
                if rc < 0:
                    raise RuntimeError(f"tekst past niet: {item.text!r}")
                y += box_h + 8.0
            else:
                # Pack zoveel hele systemen als op de rest van de pagina passen.
                src_y = 0.0
                cut_i = 0
                while src_y < sh - 1e-3 and cut_i < len(cuts):
                    avail = _A4_H - _MARGIN - y
                    if avail < 36.0 and y > _MARGIN + 1:
                        new_page()
                        avail = _A4_H - _MARGIN - y
                    max_src = src_y + avail / scale
                    # Grootste snijpunt dat nog op deze pagina past
                    chosen: float | None = None
                    j = cut_i
                    while j < len(cuts) and cuts[j] <= max_src + 1e-3:
                        chosen = cuts[j]
                        j += 1
                    if chosen is None:
                        # Volgend systeem past niet → nieuwe pagina, tenzij
                        # we al bovenaan staan (systeem hoger dan A4).
                        if y > _MARGIN + 1:
                            new_page()
                            continue
                        chosen = cuts[cut_i]
                        print(
                            "  WAARSCHUWING: systeem hoger dan rest-A4; "
                            "alsnog één systeem geplaatst",
                            flush=True,
                        )
                    place_music_band(src_y, chosen)
                    # Zoek cut_i voorbij chosen
                    while cut_i < len(cuts) and cuts[cut_i] <= chosen + 1e-6:
                        cut_i += 1
                    src_y = chosen
                    if src_y < sh - 1e-3 and cut_i < len(cuts):
                        # Meer muziek → volgende A4 (tenzij nog ruimte voor
                        # nóg een systeem; place-loop handelt avail af)
                        if (_A4_H - _MARGIN - y) < 36.0:
                            new_page()

        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        doc.save(tmp)
        n = doc.page_count
        doc.close()
        tmp.replace(dest)
        return n
    finally:
        music_src.close()


def _write_preview_html(
    dest: Path, *, flow: list[FlowItem], tall_svg_name: str
) -> None:
    parts: list[str] = []
    for item in flow:
        if isinstance(item, KopItem):
            parts.append(f"<h1>{item.text}</h1>")
        elif isinstance(item, NoteItem):
            parts.append(f"<p class='note-line'>{item.text}</p>")
        else:
            parts.append(
                f'<img src="{tall_svg_name}" alt="partituur '
                f'({item.uv_id or "bieb"})"/>'
            )
    body = "\n    ".join(parts)
    dest.write_text(
        f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8"/>
  <title>spike — {INDEX_MD.name}</title>
  <style>
    body {{ font-family: "Source Sans 3", system-ui, sans-serif; margin: 1.5rem; }}
    .page {{
      width: 210mm; max-width: 100%; margin: 0 auto;
      border: 1px solid #ccc; padding: 10mm; box-sizing: border-box;
      background: #fff;
    }}
    h1 {{ text-align: center; font-weight: 400; font-size: 1.25rem; margin: 0 0 0.75rem; }}
    .note-line {{ margin: 0 0 1rem; color: #333; }}
    img {{ width: 100%; height: auto; display: block; }}
  </style>
</head>
<body>
  <div class="page">
    {body}
  </div>
</body>
</html>
""",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    if not MSCZ.is_file():
        print(f"FOUT: bron ontbreekt: {MSCZ}", file=sys.stderr)
        return 1
    if not INDEX_MD.is_file():
        print(f"FOUT: index ontbreekt: {INDEX_MD}", file=sys.stderr)
        return 1

    md_text = INDEX_MD.read_text(encoding="utf-8")
    flow = parse_index_flow(md_text)
    print(f"index-flow ({INDEX_MD.name}):")
    for item in flow:
        if isinstance(item, KopItem):
            print(f"  kop: {item.text!r}")
        elif isinstance(item, NoteItem):
            print(f"  tekst: {item.text!r}")
        else:
            print(f"  muziek/bieb: {item.uv_id!r}")
    if not any(isinstance(i, MusicItem) for i in flow):
        print("FOUT: geen bieb/muziek in index.md", file=sys.stderr)
        return 1

    # --- A4 baseline (zichtbaar naast tall) ---
    print("\n=== A4 (huidige mscz svg) ===")
    for stale in HERE.glob(f"{STEM}-a4*.svg"):
        stale.unlink(missing_ok=True)
    try:
        a4_pages = export_mscz_to_svg(MSCZ, A4_SVG)
    except Exception as exc:
        print(f"FOUT A4-export: {exc}", file=sys.stderr)
        return 1
    # hernoem naar vriendelijk-licht-a4-N.svg als MuseScore -1/-2 schreef
    renamed_a4: list[Path] = []
    for p in a4_pages:
        if p.name.startswith(f"{STEM}-a4"):
            renamed_a4.append(p)
            continue
        # onverwacht
        renamed_a4.append(p)
    # Zorg voor stabiele namen vriendelijk-licht-a4-1.svg …
    final_a4: list[Path] = []
    pages_sorted = sorted(a4_pages, key=_svg_page_index) if len(a4_pages) > 1 else a4_pages
    if len(pages_sorted) == 1 and pages_sorted[0].name == A4_SVG.name:
        target = HERE / f"{STEM}-a4-1.svg"
        pages_sorted[0].replace(target)
        final_a4 = [target]
    else:
        for p in pages_sorted:
            idx = _svg_page_index(p) or (len(final_a4) + 1)
            target = HERE / f"{STEM}-a4-{idx}.svg"
            if p.resolve() != target.resolve():
                if target.exists():
                    target.unlink()
                p.replace(target)
            final_a4.append(target)
    print(f"  bestanden: {len(final_a4)}")
    for p in final_a4:
        w, h = _svg_dims(p)
        print(f"  {p.name}: {w} × {h}")

    # --- tall ---
    print(f"\n=== tall (pageHeight={_TALL_PAGE_HEIGHT_IN} in) ===")
    if TALL_SVG.exists():
        TALL_SVG.unlink()
    for stale in HERE.glob(f"{STEM}-tall-*.svg"):
        stale.unlink(missing_ok=True)
    try:
        tall_pages = export_tall_mscz_svg(MSCZ, TALL_SVG)
    except Exception as exc:
        print(f"FOUT tall-export: {exc}", file=sys.stderr)
        return 1
    if len(tall_pages) != 1:
        print(f"NIET OK: {len(tall_pages)} tall-SVG(s), verwacht 1", file=sys.stderr)
        for p in tall_pages:
            print(f"  {p.name}: {_svg_dims(p)}")
        return 2
    tall = tall_pages[0]
    if tall.resolve() != TALL_SVG.resolve():
        if TALL_SVG.exists():
            TALL_SVG.unlink()
        tall.replace(TALL_SVG)
        tall = TALL_SVG
    w, h = _svg_dims(tall)
    print(f"  {tall.name}: {w} × {h}")

    # --- index.md → PDF ---
    print("\n=== index.md.pdf (shortcodes + tall-SVG) ===")
    try:
        n_pages = compose_index_pdf(INDEX_PDF, flow=flow, tall_svg=tall)
    except Exception as exc:
        print(f"FOUT PDF: {exc}", file=sys.stderr)
        return 1
    print(f"  {INDEX_PDF.name}: {n_pages} A4")

    _write_preview_html(INDEX_HTML, flow=flow, tall_svg_name=tall.name)
    print(f"  {INDEX_HTML.name}")

    print("\n=== oordeel ===")
    print("OK: tall-SVG + index-PDF in examples/bug-cases/ (zichtbaar).")
    print(f"  Open {INDEX_PDF.name} — kop/tekst uit index, muziek uit tall-SVG.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
