"""Post-process MuseScore ``.mscz`` for canonieke partituur-conventies.

Clears visible staff/instrument names and applies A4/leesbaarheid-Style
(see docs/formats/mscz-leesbaarheid.md and VSA-demo mscz-partituur-contract).
"""

from __future__ import annotations

import re
import zipfile
from fractions import Fraction
from pathlib import Path

# A4 in inches (MuseScore). 15 mm = 0.590551 in.
_A4_W = "8.26772"
_A4_H = "11.6929"
_M = "0.590551"
_PRINTABLE = "7.08662"  # A4_W - 2 * 15 mm
_FONT = "Source Sans 3"

# MuseScore Style: A4 + typografie + leesbaarheid (Oefenhoek / MCI-contract).
# Copyright-footertekst (oddFooterC) blijft leeg tot checklist P4.
_STYLE_OVERRIDES = {
    "pageWidth": _A4_W,
    "pageHeight": _A4_H,
    "pagePrintableWidth": _PRINTABLE,
    "pageEvenLeftMargin": _M,
    "pageOddLeftMargin": _M,
    "pageEvenTopMargin": _M,
    "pageOddTopMargin": _M,
    "pageEvenBottomMargin": _M,
    "pageOddBottomMargin": _M,
    "pageTwosided": "0",
    "enableIndentationOnFirstSystem": "0",
    "firstSystemIndentationValue": "0",
    "lastSystemFillLimit": "0",
    "enableVerticalSpread": "0",
    "maxPageFillSpread": "0",
    "minSystemDistance": "8",
    "maxSystemDistance": "14",
    "hideInstrumentNameIfOneInstrument": "1",
    "firstSystemInstNameVisibility": "0",
    "subsSystemInstNameVisibility": "0",
    "showMeasureNumber": "1",
    "showMeasureNumberOne": "1",
    "measureNumberSystem": "1",
    "measureNumberInterval": "0",
    "frameSystemDistance": "14",
    "lyricsOddAlign": "center,baseline",
    "lyricsEvenAlign": "center,baseline",
    "lyricsMinDistance": "0.6",
    "minNoteDistance": "0.5",
    "measureSpacing": "1.2",
    "lyricsPlacement": "1",
    "lyricsOddFontFace": _FONT,
    "lyricsEvenFontFace": _FONT,
    "lyricsOddFontSize": "13",
    "lyricsEvenFontSize": "13",
    "lyricsOddFontSpatiumDependent": "0",
    "lyricsEvenFontSpatiumDependent": "0",
    "staffTextFontFace": _FONT,
    "staffTextFontSize": "12",
    "staffTextFontSpatiumDependent": "0",
    "systemTextFontFace": _FONT,
    "systemTextFontSize": "12",
    "systemTextFontSpatiumDependent": "0",
    "titleFontFace": _FONT,
    "titleFontSize": "18",
    "composerFontFace": _FONT,
    "composerFontSize": "12",
    "subTitleFontFace": _FONT,
    "subTitleFontSize": "14",
    "frameFontFace": _FONT,
    "frameFontSize": "12",
    "footerFontFace": _FONT,
    "footerFontSize": "8",
    "footerFontSpatiumDependent": "0",
    "copyrightFontFace": _FONT,
    "copyrightFontSize": "8",
    "copyrightFontSpatiumDependent": "0",
}

_LONG_NAME_RE = re.compile(
    r"<longName>.*?</longName>",
    re.DOTALL,
)
_SHORT_NAME_RE = re.compile(
    r"<shortName>.*?</shortName>",
    re.DOTALL,
)
_TRACK_NAME_RE = re.compile(
    r"<trackName>.*?</trackName>",
    re.DOTALL,
)
_STAFF_TEXT_RE = re.compile(r"<StaffText>(.*?)</StaffText>", re.DOTALL)
_MEASURE_RE = re.compile(r"(<Measure\b[^>]*>)(.*?)(</Measure>)", re.DOTALL)
_REST_BLOCK_RE = re.compile(r"<Rest\b[^>]*>.*?</Rest>", re.DOTALL)
_CHORD_BLOCK_RE = re.compile(r"<Chord\b[^>]*>.*?</Chord>", re.DOTALL)
_COLOPHON_VBOX_RE = re.compile(
    r"[ \t]*<VBox>(?:(?!</VBox>).)*?"
    r"Colofon"
    r"(?:(?!</VBox>).)*?</VBox>",
    re.S,
)
_COLOPHON_TITLE = "Colofon"
_BIB_ID_LABEL = "Bibliotheek-id:"
_BRON_LABEL = "Bron:"
_SEE_COLOPHON = "zie colofon"
_LITURGY_COPY = (
    "Voor gebruik in de orthodoxe eredienst is kopiëren toegestaan."
)
_DEFAULT_SHORT = f"CC BY-SA 4.0 — {_SEE_COLOPHON}"
_DEFAULT_FULL = (
    "Deze partituur: CC BY-SA 4.0 (orthodox-ronl).\n" + _LITURGY_COPY
)


class MsczPartituurError(Exception):
    """MSCZ partituur post-process failed."""


def apply_partituur_mscz_conventions(
    path: Path,
    *,
    system_texts: list[str] | None = None,
    hbox_before_texts: list[str] | None = None,
    copyright: str | None = None,
    bibliotheek_id: str | None = None,
    title: str | None = None,
    composer: str | None = None,
    bron: str | None = None,
    ondertitel: str | None = None,
    tekstdichter: str | None = None,
    arrangeur: str | None = None,
    vertaler: str | None = None,
) -> None:
    """In-place: empty instrument names + leesbaarheid-Style + colofon.

    When *system_texts* is given, matching ``StaffText`` elements (from MusicXML
    ``@tekst`` import) are promoted to ``SystemText`` so the cue sits above the
    staff at the start of that measure.

    *hbox_before_texts* is ignored (kept for call-site compatibility). Mid-system
    HBox causes MuseScore accolades; empty short rest measures are stripped.

    *title* (``@title``) wordt als ``workTitle``-meta én als Title-tekst in de
    kop-VBox gezet — MusicXML-import laat dat veld soms leeg.

    *bron* (``@bron``) → meta ``source`` én regel in het colofon. MuseScore
    toont meta ``source`` niet in de kop; daarom geen lyricist-workaround meer.
    *tekstdichter* blijft optioneel als echte lyricist-tekst in de kop.
    """
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".mscz":
        raise MsczPartituurError(f"geen .mscz: {path}")
    del hbox_before_texts  # no mid-system HBox

    with zipfile.ZipFile(path, "r") as zin:
        names = zin.namelist()
        mscx_name = next((n for n in names if n.lower().endswith(".mscx")), None)
        if mscx_name is None:
            raise MsczPartituurError(f"geen .mscx in {path}")
        mscx = zin.read(mscx_name).decode("utf-8")
        other = {n: zin.read(n) for n in names if n != mscx_name}

    mscx = _clear_instrument_names(mscx)
    mscx = _ensure_style_overrides(mscx)
    if system_texts:
        mscx = _promote_tekst_staff_texts(mscx, system_texts)
        mscx = _wrap_system_text_ellipsis(mscx, system_texts)
    # Korte rust-only maten (oude spacers / lege |:-maat) → weg, niet HBox.
    mscx = _strip_short_rest_measures(mscx)
    mscx = _strip_trailing_hboxes(mscx)
    # Same-pitch tie-ketens → compacte noten incl. stip (leesbaar 3/4 i.p.v. 2/4+1/4).
    # Bewust ná MuseScore-import: gestipte MusicXML-collapse corruptte soms de score.
    mscx = _collapse_same_pitch_tie_runs(mscx)
    # Recite-print (S8/R3): ||O||-kop + onhoorbare spacers; maatlengte herstellen.
    mscx = _apply_recite_print_conventions(mscx)
    if title:
        mscx = _ensure_score_title(mscx, title)
    sheet_lyricist = (tekstdichter or "").strip() or None
    for meta_name, value in (
        ("composer", composer),
        ("source", bron),
        ("subtitle", ondertitel),
        ("lyricist", sheet_lyricist),
        ("arranger", arrangeur),
        ("translator", vertaler),
    ):
        if value:
            mscx = _set_meta(mscx, meta_name, value)
    if sheet_lyricist:
        mscx = _ensure_header_text(mscx, style="lyricist", text=sheet_lyricist)
    short, full = _format_copyright_notices(copyright, bibliotheek_id, bron=bron)
    mscx = _set_meta(mscx, "copyright", short)
    mscx = _set_footer_style(mscx, short)
    mscx = _insert_colophon_after_staff1(mscx, full)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for n, data in other.items():
            zout.writestr(n, data)
        zout.writestr(mscx_name, mscx.encode("utf-8"))
    tmp.replace(path)


def _clear_instrument_names(mscx: str) -> str:
    mscx = _LONG_NAME_RE.sub("<longName></longName>", mscx)
    mscx = _SHORT_NAME_RE.sub("<shortName></shortName>", mscx)
    mscx = _TRACK_NAME_RE.sub("<trackName></trackName>", mscx)
    return mscx


def _plain_cue_text(s: str) -> str:
    """Normalize MuseScore/MusicXML cue text for matching (br/newlines/entities)."""
    t = (
        s.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
    )
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # ``Gezegend\n...`` en ``Gezegend ...`` als dezelfde cue.
    t = re.sub(r"[ \t]*\n[ \t]*", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _promote_tekst_staff_texts(mscx: str, texts: list[str]) -> str:
    """Rename StaffText → SystemText when the body contains a known @tekst."""
    if not texts:
        return mscx
    wanted_plain = [_plain_cue_text(t) for t in texts if t]
    wanted_plain = [t for t in wanted_plain if t]

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        plain = _plain_cue_text(inner)
        if any(w and w in plain for w in wanted_plain):
            return f"<SystemText>{inner}</SystemText>"
        return match.group(0)

    return _STAFF_TEXT_RE.sub(repl, mscx)


def _ensure_rest_gap(rest: str) -> str:
    """MuseScore gap-rest: geen kolombreedte, wel ticks (VSA-demo)."""
    if "<gap>" not in rest:
        rest = re.sub(
            r"<Rest(\s[^>]*)?>",
            r"<Rest\1>\n            <gap>1</gap>",
            rest,
            count=1,
        )
    else:
        rest = re.sub(r"<gap>.*?</gap>", "<gap>1</gap>", rest, count=1)
    if "<visible>0</visible>" not in rest:
        rest = re.sub(
            r"(<Rest(?:\s[^>]*)?>)",
            r"\1\n            <visible>0</visible>",
            rest,
            count=1,
        )
    return rest


def _gap_cue_spacer_rests(mscx: str) -> str:
    """Korte rust-only maten (``@tekst``-spacers) → onzichtbare MuseScore gap-rust.

    Heuristiek: maat zonder Chord, wél Rest, en ``<len>`` strikt kleiner dan
    een hele noot (``1/1``) — typisch de 16e uit MusicXML-import.
    """

    def fix_measure(m: re.Match[str]) -> str:
        open_tag, body, close = m.group(1), m.group(2), m.group(3)
        if _CHORD_BLOCK_RE.search(body):
            return m.group(0)
        rests = list(_REST_BLOCK_RE.finditer(body))
        if not rests:
            return m.group(0)
        len_m = re.search(r"<len>([^<]+)</len>", body)
        if len_m is None:
            return m.group(0)
        try:
            raw = len_m.group(1).strip()
            frac = Fraction(raw) if "/" in raw else Fraction(int(raw), 1)
        except (ValueError, ZeroDivisionError):
            return m.group(0)
        if frac >= 1:
            return m.group(0)
        new_body = body
        for rest_m in reversed(rests):
            new_body = (
                new_body[: rest_m.start()]
                + _ensure_rest_gap(rest_m.group(0))
                + new_body[rest_m.end() :]
            )
        return open_tag + new_body + close

    return _MEASURE_RE.sub(fix_measure, mscx)


def _xml_text(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _set_meta(mscx: str, name: str, value: str) -> str:
    pat = rf'<metaTag name="{re.escape(name)}">.*?</metaTag>'
    repl = f'<metaTag name="{name}">{_xml_text(value)}</metaTag>'
    if re.search(pat, mscx, flags=re.S):
        return re.sub(pat, repl, mscx, count=1, flags=re.S)
    insert = f"    {repl}\n    "
    if "</Score>" in mscx:
        return mscx.replace("</Score>", insert + "</Score>", 1)
    return mscx + insert


_TITLE_TEXT_BLOCK_RE = re.compile(
    r"<Text>\s*<style>\s*title\s*</style>[\s\S]*?</Text>",
)
_LYRICIST_TEXT_BLOCK_RE = re.compile(
    r"<Text>\s*<style>\s*lyricist\s*</style>[\s\S]*?</Text>",
)
# Eerste VBox direct onder Staff (kopkader vóór Measures).
_HEADER_VBOX_RE = re.compile(
    r"(<Staff\b[^>]*>\s*)(<VBox\b[^>]*>)([\s\S]*?)(</VBox>)",
)


def _ensure_header_text(mscx: str, *, style: str, text: str) -> str:
    """Zet of vul een Text-blok met *style* in de kop-VBox."""
    text = text.strip()
    if not text:
        return mscx
    escaped = _xml_text(text)
    style_l = style.lower()
    block_re = (
        _TITLE_TEXT_BLOCK_RE if style_l == "title" else _LYRICIST_TEXT_BLOCK_RE
    )
    if style_l not in ("title", "lyricist"):
        block_re = re.compile(
            rf"<Text>\s*<style>\s*{re.escape(style)}\s*</style>[\s\S]*?</Text>",
        )

    def repl_existing(m: re.Match[str]) -> str:
        block = m.group(0)
        if re.search(r"<text[\s/>]", block):
            return re.sub(
                r"<text(?:\s[^>]*)?>[\s\S]*?</text>|<text(?:\s[^>]*)?/>",
                f"<text>{escaped}</text>",
                block,
                count=1,
            )
        return block.replace("</Text>", f"<text>{escaped}</text></Text>", 1)

    new_mscx, n = block_re.subn(repl_existing, mscx, count=1)
    if n:
        return new_mscx

    text_block = (
        "<Text>\n"
        f"          <style>{style}</style>\n"
        f"          <text>{escaped}</text>\n"
        "          </Text>\n"
        "        "
    )

    def repl_vbox(m: re.Match[str]) -> str:
        staff_open, vbox_open, body, vbox_close = m.groups()
        return f"{staff_open}{vbox_open}{body}{text_block}{vbox_close}"

    new_mscx, n = _HEADER_VBOX_RE.subn(repl_vbox, mscx, count=1)
    if n:
        return new_mscx

    title_vbox = (
        "<VBox>\n"
        "        <height>10</height>\n"
        f"        {text_block}"
        "</VBox>\n"
        "      "
    )
    return re.sub(
        r"(<Staff\b[^>]*>\s*)(<Measure\b)",
        rf"\1{title_vbox}\2",
        mscx,
        count=1,
    )


def _ensure_score_title(mscx: str, title: str) -> str:
    """Zet ``workTitle``-meta én vul/plaats Title-tekst in de kop-VBox."""
    title = title.strip()
    if not title:
        return mscx
    mscx = _set_meta(mscx, "workTitle", title)
    return _ensure_header_text(mscx, style="title", text=title)


def _format_copyright_notices(
    copyright: str | None,
    bibliotheek_id: str | None,
    *,
    bron: str | None = None,
) -> tuple[str, str]:
    """(korte footer, volledige colofontekst)."""
    raw = (copyright or "").strip()
    if not raw:
        short, full = _DEFAULT_SHORT, _DEFAULT_FULL
    else:
        short = raw if len(raw) <= 70 else raw[:67].rstrip(" ,;.-") + "…"
        if _SEE_COLOPHON not in short.lower():
            short = f"{short} — {_SEE_COLOPHON}"
        full = raw
        if _LITURGY_COPY.lower() not in full.lower():
            full = f"{full}\n{_LITURGY_COPY}"
    source = (bron or "").strip()
    if source:
        full = re.sub(
            rf"(?im)^\s*{re.escape(_BRON_LABEL)}\s*.*$",
            "",
            full,
        ).strip()
        # Strip optional leading ``bron:`` from the value itself.
        if source.lower().startswith("bron:"):
            source = source[5:].strip()
        full = f"{full}\n{_BRON_LABEL} {source}"
    ident = (bibliotheek_id or "").strip()
    if ident:
        full = re.sub(
            rf"(?im)^\s*{re.escape(_BIB_ID_LABEL)}\s*.*$",
            "",
            full,
        ).strip()
        full = f"{full}\n{_BIB_ID_LABEL} {ident}"
    return short, full


def _set_footer_style(mscx: str, short: str) -> str:
    """Letterlijke footertekst op oneven/even pagina's (VSA-demo-patroon)."""
    for key in ("oddFooterC", "evenFooterC"):
        pat = re.compile(rf"<{key}>.*?</{key}>", re.DOTALL)
        tag = f"<{key}>{_xml_text(short)}</{key}>"
        if pat.search(mscx):
            mscx = pat.sub(tag, mscx)
        elif "<Style>" in mscx:
            mscx = mscx.replace("<Style>", f"<Style>{tag}", 1)
    for key, val in (
        ("showFooter", "1"),
        ("footerFirstPage", "1"),
        ("footerOddEven", "1"),
    ):
        pat = re.compile(rf"<{key}>.*?</{key}>", re.DOTALL)
        tag = f"<{key}>{val}</{key}>"
        if pat.search(mscx):
            mscx = pat.sub(tag, mscx)
        elif "<Style>" in mscx:
            mscx = mscx.replace("<Style>", f"<Style>{tag}", 1)
    return mscx


def _build_colophon_vbox(full_text: str) -> str:
    body = f"{_COLOPHON_TITLE}\n\n{full_text.strip()}"
    return "\n".join(
        [
            "      <VBox>",
            "        <height>8</height>",
            "        <boxAutoSize>1</boxAutoSize>",
            "        <topGap>8</topGap>",
            "        <bottomGap>2</bottomGap>",
            "        <Text>",
            "          <style>frame</style>",
            "          <align>left,top</align>",
            f"          <text>{_xml_text(body)}</text>",
            "          </Text>",
            "        </VBox>",
        ]
    )


def _insert_colophon_after_staff1(mscx: str, full_text: str) -> str:
    mscx = _COLOPHON_VBOX_RE.sub("", mscx)
    if not full_text.strip():
        return mscx
    vbox = _build_colophon_vbox(full_text)
    # Eerste Staff-blok met Measure (niet Part-definitie).
    staff_m = re.search(
        r'<Staff\b[^>]*>.*?<Measure\b.*?</Staff>',
        mscx,
        flags=re.S,
    )
    if staff_m is None:
        return mscx
    block = staff_m.group(0)
    close = block.rfind("</Staff>")
    if close < 0:
        return mscx
    new_block = block[:close] + vbox + "\n      " + block[close:]
    return mscx[: staff_m.start()] + new_block + mscx[staff_m.end() :]



def _wrap_system_text_ellipsis(mscx: str, texts: list[str]) -> str:
    """Zet newline vóór ``...`` in SystemText (twee regels op het blad)."""
    from vsa.mvsa_musicxml import wrap_tekst_at_ellipsis

    wanted_plain = [_plain_cue_text(t) for t in texts if t]

    def fix_system(m: re.Match[str]) -> str:
        block = m.group(0)
        tm = re.search(r"<text>(.*?)</text>", block, re.S)
        if tm is None:
            return block
        raw = tm.group(1)
        plain = _plain_cue_text(raw)
        if wanted_plain and not any(w and w in plain for w in wanted_plain):
            return block
        wrapped = wrap_tekst_at_ellipsis(plain)
        if wrapped == plain and "<br" in raw.lower():
            return block
        # MuseScore: harde regelbreuk als ``<br/>``, niet als letterlijke newline.
        out = wrapped.replace("\n", "<br/>")
        return block[: tm.start(1)] + out + block[tm.end(1) :]

    return re.sub(r"<SystemText>.*?</SystemText>", fix_system, mscx, flags=re.S)


_HBOX_SNIPPET = (
    "      <HBox>\n"
    "        <width>1.5</width>\n"
    "        <boxAutoSize>0</boxAutoSize>\n"
    "        </HBox>\n"
)


def _tekst_match_needles(texts: list[str]) -> list[str]:
    """Match keys for SystemText / HBox: full, flat, and first line."""
    needles: list[str] = []
    for t in texts:
        if not t:
            continue
        needles.append(t)
        flat = t.replace("\n", "").replace("\r", "")
        if flat and flat not in needles:
            needles.append(flat)
        first = t.splitlines()[0].strip() if t.splitlines() else t.strip()
        if first and first not in needles:
            needles.append(first)
    return needles


def _measure_has_cue_text(part: str, needles: list[str]) -> bool:
    if "<SystemText>" not in part and "<StaffText>" not in part:
        return False
    return any(n in part for n in needles)


def _is_short_rest_only_measure(body: str) -> bool:
    """True for short rest-only measures (MusicXML cue-spacers)."""
    if _CHORD_BLOCK_RE.search(body):
        return False
    if not _REST_BLOCK_RE.search(body):
        return False
    if "<SystemText>" in body or "<StaffText>" in body:
        return False
    len_m = re.search(r"<len>([^<]+)</len>", body)
    if len_m is None:
        # MusicXML-import zonder <len>: korte print-object=no rust.
        if 'print-object="no"' in body or "<visible>0</visible>" in body:
            return True
        return False
    try:
        raw = len_m.group(1).strip()
        frac = Fraction(raw) if "/" in raw else Fraction(int(raw), 1)
    except (ValueError, ZeroDivisionError):
        return False
    return frac < 1


_CHORD_DUR_FRAC: dict[str, Fraction] = {
    "longa": Fraction(4, 1),
    "breve": Fraction(2, 1),
    "whole": Fraction(1, 1),
    "half": Fraction(1, 2),
    "quarter": Fraction(1, 4),
    "eighth": Fraction(1, 8),
    "16th": Fraction(1, 16),
    "32nd": Fraction(1, 32),
    "64th": Fraction(1, 64),
    "128th": Fraction(1, 128),
}

# Compacte single-note vormen voor MSCZ-postprocess (gestipt mag wél — geen MusicXML-import).
_DURATION_TYPE_ORDER = (
    "whole",
    "half",
    "quarter",
    "eighth",
    "16th",
    "32nd",
    "64th",
    "128th",
)

_TIE_SPANNER_RE = re.compile(
    r'<Spanner type="Tie">.*?</Spanner>',
    re.DOTALL,
)
_SLUR_SPANNER_RE = re.compile(
    r'<Spanner type="Slur">.*?</Spanner>',
    re.DOTALL,
)
_VOICE_BLOCK_RE = re.compile(r"(<voice>)(.*?)(</voice>)", re.DOTALL)
_CHORD_SPLIT_RE = re.compile(r"(<Chord\b[^>]*>.*?</Chord>)", re.DOTALL)


def _chord_pitch_key(chord_xml: str) -> tuple[tuple[str, str], ...] | None:
    """Stable pitch identity for Notes in a Chord (pitch+tpc), or None if empty."""
    notes = re.findall(r"<Note\b[^>]*>.*?</Note>", chord_xml, flags=re.S)
    if not notes:
        return None
    keys: list[tuple[str, str]] = []
    for note in notes:
        pitch = re.search(r"<pitch>([^<]+)</pitch>", note)
        tpc = re.search(r"<tpc>([^<]+)</tpc>", note)
        if pitch is None:
            return None
        keys.append((pitch.group(1), tpc.group(1) if tpc else ""))
    return tuple(keys)


def _chord_has_tie_next(chord_xml: str) -> bool:
    return bool(
        re.search(
            r'<Spanner type="Tie">(?:(?!</Spanner>).)*?<next>',
            chord_xml,
            flags=re.S,
        )
    )


def _chord_has_tie_prev(chord_xml: str) -> bool:
    return bool(
        re.search(
            r'<Spanner type="Tie">(?:(?!</Spanner>).)*?<prev>',
            chord_xml,
            flags=re.S,
        )
    )


def _collapse_forbidden(chord_xml: str) -> bool:
    """Recite spacers / ||O|| — niet samentrekken."""
    if "<visible>0</visible>" in chord_xml:
        return True
    if "<noStem>1</noStem>" in chord_xml:
        return True
    if "<headType>breve</headType>" in chord_xml:
        return True
    if "<durationType>breve</durationType>" in chord_xml:
        return True
    return False


def _fraction_to_type_dots(frac: Fraction) -> tuple[str, int] | None:
    """Map duur → één MuseScore durationType + dots (0–2), zonder breve/longa."""
    if frac <= 0:
        return None
    for name in _DURATION_TYPE_ORDER:
        base = _CHORD_DUR_FRAC[name]
        if frac == base:
            return name, 0
        if frac == base * Fraction(3, 2):
            return name, 1
        if frac == base * Fraction(7, 4):
            return name, 2
    return None


def _set_chord_duration(chord_xml: str, *, duration_type: str, dots: int) -> str:
    """Zet durationType + dots; verwijder oude dots-tags."""
    out = re.sub(r"<dots>\d+</dots>", "", chord_xml)
    out = re.sub(r"<dots\s*/>", "", out)
    out = re.sub(
        r"<durationType>[^<]+</durationType>",
        f"<durationType>{duration_type}</durationType>",
        out,
        count=1,
    )
    if dots > 0:
        out = re.sub(
            r"(<Chord\b[^>]*>)",
            rf"\1<dots>{dots}</dots>",
            out,
            count=1,
        )
    return out


def _strip_tie_spanners(chord_xml: str) -> str:
    return _TIE_SPANNER_RE.sub("", chord_xml)


def _move_slur_spanners(src_chord: str, dst_chord: str) -> tuple[str, str]:
    """Verplaats Slur-Spanners van src naar dst (bij collapse van eindnoot)."""
    slurs = _SLUR_SPANNER_RE.findall(src_chord)
    if not slurs:
        return src_chord, dst_chord
    cleaned_src = _SLUR_SPANNER_RE.sub("", src_chord)
    # Plak voor </Chord> van dst.
    insert = "".join(slurs)
    cleaned_dst = re.sub(r"</Chord>\s*$", insert + "</Chord>", dst_chord, count=1)
    return cleaned_src, cleaned_dst


def _set_slur_fractions(chord_xml: str, *, next_frac: Fraction | None, prev_frac: Fraction | None) -> str:
    """Werk location/fractions bij op Slur-Spanners in deze Chord."""

    def fix_spanner(m: re.Match[str]) -> str:
        block = m.group(0)
        if next_frac is not None and "<next>" in block:
            block = re.sub(
                r"(<next>\s*<location>\s*<fractions>)[^<]+(</fractions>)",
                rf"\g<1>{next_frac.numerator}/{next_frac.denominator}\2",
                block,
                count=1,
            )
        if prev_frac is not None and "<prev>" in block:
            block = re.sub(
                r"(<prev>\s*<location>\s*<fractions>)[^<]+(</fractions>)",
                rf"\g<1>{prev_frac.numerator}/{prev_frac.denominator}\2",
                block,
                count=1,
            )
        return block

    return _SLUR_SPANNER_RE.sub(fix_spanner, chord_xml)


def _slur_has_next(chord_xml: str) -> bool:
    return bool(
        re.search(
            r'<Spanner type="Slur">(?:(?!</Spanner>).)*?<next>',
            chord_xml,
            flags=re.S,
        )
    )


def _slur_has_prev(chord_xml: str) -> bool:
    return bool(
        re.search(
            r'<Spanner type="Slur">(?:(?!</Spanner>).)*?<prev>',
            chord_xml,
            flags=re.S,
        )
    )


def _recompute_slur_fractions(chords: list[str]) -> list[str]:
    """Herbereken Slur next/prev fractions uit werkelijke chord-duuren."""
    starts: list[int] = []
    pairs: list[tuple[int, int]] = []
    for i, ch in enumerate(chords):
        if _slur_has_next(ch):
            starts.append(i)
        if _slur_has_prev(ch):
            if starts:
                pairs.append((starts.pop(), i))
    out = list(chords)
    for start, end in pairs:
        if start == end:
            # Degenerate: slur op één noot → weg.
            out[start] = _SLUR_SPANNER_RE.sub("", out[start])
            continue
        dist = sum(_chord_nominal_duration(out[i]) for i in range(start, end))
        if dist <= 0:
            continue
        out[start] = _set_slur_fractions(out[start], next_frac=dist, prev_frac=None)
        out[end] = _set_slur_fractions(out[end], next_frac=None, prev_frac=-dist)
    return out


def _collapse_tie_runs_in_voice(voice_body: str) -> str:
    """Samentrekken van same-pitch Tie-ketens tot compacte (evt. gestipte) noten."""
    parts = _CHORD_SPLIT_RE.split(voice_body)
    chord_indices = [i for i, p in enumerate(parts) if p.startswith("<Chord")]
    if len(chord_indices) < 2:
        return voice_body

    chords: list[str | None] = [parts[i] for i in chord_indices]
    i = 0
    while i < len(chords) - 1:
        cur = chords[i]
        if cur is None or _collapse_forbidden(cur):
            i += 1
            continue
        key = _chord_pitch_key(cur)
        if key is None or not _chord_has_tie_next(cur):
            i += 1
            continue
        j = i + 1
        while j < len(chords):
            nxt = chords[j]
            if nxt is None or _collapse_forbidden(nxt):
                break
            if _chord_pitch_key(nxt) != key:
                break
            if not _chord_has_tie_prev(nxt):
                break
            j += 1
            if not _chord_has_tie_next(nxt):
                break
        run_end = j  # exclusive
        if run_end - i < 2:
            i += 1
            continue
        total = Fraction(0)
        for k in range(i, run_end):
            ch = chords[k]
            if ch is not None:
                total += _chord_nominal_duration(ch)
        packed = _fraction_to_type_dots(total)
        if packed is None:
            i = run_end
            continue
        dur_type, dots = packed
        survivor = _set_chord_duration(cur, duration_type=dur_type, dots=dots)
        survivor = _strip_tie_spanners(survivor)
        for k in range(i + 1, run_end):
            doomed = chords[k]
            if doomed is None:
                continue
            _src, survivor = _move_slur_spanners(doomed, survivor)
            chords[k] = None
        chords[i] = survivor
        i = run_end

    surviving = [c for c in chords if c is not None]
    surviving = _recompute_slur_fractions(surviving)
    kept_flags = [c is not None for c in chords]
    kept_iter = iter(surviving)
    out_parts: list[str] = []
    chord_slot = 0
    for part in parts:
        if part.startswith("<Chord"):
            if kept_flags[chord_slot]:
                out_parts.append(next(kept_iter))
            chord_slot += 1
        else:
            out_parts.append(part)
    return "".join(out_parts)


def _collapse_same_pitch_tie_runs(mscx: str) -> str:
    """MSCZ-postprocess (S13): same-pitch Tie-keten → één compacte noot (stip ok).

    MusicXML-partituur blijft I1 (ongestipt + ties) voor veilige MuseScore-import;
    hier — ná import — maken we het leesbeeld compact (bijv. half+kwart → gestipte half).
    """

    def fix_voice(m: re.Match[str]) -> str:
        open_v, body, close_v = m.group(1), m.group(2), m.group(3)
        return open_v + _collapse_tie_runs_in_voice(body) + close_v

    return _VOICE_BLOCK_RE.sub(fix_voice, mscx)


def _apply_recite_print_conventions(mscx: str) -> str:
    """Canonieke recite-print in MSCZ (checklist S8 / leesbaarheid R2–R3).

    - ``||O||``-midden: stokloos + zichtbare noot → ``headType`` breve; als
      MuseScore ``durationType=breve`` heeft gezet (te brede maat), terug naar
      ``quarter`` zodat de metrische breedte = één randduur blijft.
    - Spacer-noten (``visible=0``): ook ``play=0`` (templates / geen
      stotter-playback).
    - ``Measure len`` herberekenen uit chord-duuren (na breve-fix).
    """
    mscx = _fix_recite_breve_and_mute_spacers(mscx)
    return _recompute_measure_lens(mscx)


def _fix_recite_breve_and_mute_spacers(mscx: str) -> str:
    def fix_chord(m: re.Match[str]) -> str:
        ch = m.group(0)
        no_stem = "<noStem>1</noStem>" in ch
        has_hidden_note = bool(
            re.search(r"<Note>\s*(?:<eid>[^<]*</eid>\s*)?<visible>0</visible>", ch)
        )
        # Spacers: mute playback (visible blijft 0 zodat lyrics zichtbaar blijven).
        if has_hidden_note:

            def mute_note(nm: re.Match[str]) -> str:
                note = nm.group(0)
                if "<visible>0</visible>" not in note:
                    return note
                if "<play>0</play>" not in note:
                    note = re.sub(
                        r"(<visible>0</visible>)",
                        r"\1<play>0</play>",
                        note,
                        count=1,
                    )
                return note

            ch = re.sub(r"<Note>.*?</Note>", mute_note, ch, flags=re.S)
            return ch

        # durationType=breve blaast MuseScore-maatbreedte op — altijd weg.
        if "<durationType>breve</durationType>" in ch:
            if no_stem:
                # ||O||-midden: metrisch = randduur (quarter) + headType.
                ch = ch.replace(
                    "<durationType>breve</durationType>",
                    "<durationType>quarter</durationType>",
                    1,
                )
            else:
                # Melisma-collapse-artifact: whole i.p.v. breve-lengte.
                ch = ch.replace(
                    "<durationType>breve</durationType>",
                    "<durationType>whole</durationType>",
                    1,
                )
            ch = re.sub(r"<Events>.*?</Events>", "", ch, flags=re.S)

        # ||O||-midden: stokloos, zichtbare kop → breve-head.
        if not no_stem:
            return ch

        def breve_note(nm: re.Match[str]) -> str:
            note = nm.group(0)
            if "<visible>0</visible>" in note:
                return note
            if "<headType>" not in note:
                note = re.sub(
                    r"(<Note>(?:\s*<eid>[^<]*</eid>)?)",
                    r"\1<headType>breve</headType>",
                    note,
                    count=1,
                )
            return note

        return re.sub(r"<Note>.*?</Note>", breve_note, ch, flags=re.S)

    return re.sub(r"<Chord>.*?</Chord>", fix_chord, mscx, flags=re.S)


def _chord_nominal_duration(chord_xml: str) -> Fraction:
    dt = re.search(r"<durationType>([^<]+)</durationType>", chord_xml)
    if dt is None:
        return Fraction(0)
    base = _CHORD_DUR_FRAC.get(dt.group(1), Fraction(0))
    n_dots = len(re.findall(r"<dots(?:\s*/>|>[^<]*</dots>)", chord_xml))
    if n_dots == 1:
        return base * Fraction(3, 2)
    if n_dots >= 2:
        return base * Fraction(7, 4)
    return base


def _recompute_measure_lens(mscx: str) -> str:
    """Zet ``Measure len`` op max stem-duur, **gelijk** over alle staves.

    MuseScore markeert de score corrupt als staff 1 en staff 2 dezelfde
    maatindex een verschillende ``len`` geven (typisch na breve-artifact).
    """
    # Pass 1: per maatindex de max duur over alle staves/voices.
    staff_measures: list[list[Fraction]] = []
    for sm in re.finditer(r"<Staff\b[^>]*>(.*?)</Staff>", mscx, flags=re.S):
        lengths: list[Fraction] = []
        for mm in re.finditer(r"<Measure\b[^>]*>(.*?)</Measure>", sm.group(1), flags=re.S):
            body = mm.group(1)
            voice_totals: list[Fraction] = []
            for vm in re.finditer(r"<voice>(.*?)</voice>", body, flags=re.S):
                total = Fraction(0)
                for cm in re.finditer(r"<Chord>.*?</Chord>", vm.group(1), flags=re.S):
                    total += _chord_nominal_duration(cm.group(0))
                for rm in re.finditer(r"<Rest>.*?</Rest>", vm.group(1), flags=re.S):
                    total += _chord_nominal_duration(rm.group(0))
                if total > 0:
                    voice_totals.append(total)
            lengths.append(max(voice_totals) if voice_totals else Fraction(0))
        if lengths:
            staff_measures.append(lengths)

    if not staff_measures:
        return mscx

    n = max(len(ls) for ls in staff_measures)
    global_lens: list[Fraction] = []
    for i in range(n):
        vals = [ls[i] for ls in staff_measures if i < len(ls) and ls[i] > 0]
        global_lens.append(max(vals) if vals else Fraction(0))

    # Pass 2: schrijf len per Measure in documentvolgorde, per staff.
    staff_idx = {"n": -1, "m": 0}

    def fix_staff(m: re.Match[str]) -> str:
        staff_idx["n"] += 1
        staff_idx["m"] = 0
        open_s, body, close_s = m.group(1), m.group(2), m.group(3)

        def fix_measure(mm: re.Match[str]) -> str:
            mi = staff_idx["m"]
            staff_idx["m"] += 1
            open_tag, mbody, mclose = mm.group(1), mm.group(2), mm.group(3)
            length = global_lens[mi] if mi < len(global_lens) else Fraction(0)
            if length <= 0:
                return mm.group(0)
            len_s = f"{length.numerator}/{length.denominator}"
            if re.search(r"\blen=", open_tag):
                open_tag = re.sub(
                    r'\blen="[^"]*"',
                    f'len="{len_s}"',
                    open_tag,
                    count=1,
                )
            else:
                open_tag = open_tag.replace("<Measure", f'<Measure len="{len_s}"', 1)
            mbody = re.sub(r"<len>[^<]*</len>", "", mbody)
            return open_tag + mbody + mclose

        body = re.sub(
            r"(<Measure\b[^>]*>)(.*?)(</Measure>)",
            fix_measure,
            body,
            flags=re.S,
        )
        return open_s + body + close_s

    return re.sub(
        r"(<Staff\b[^>]*>)(.*?)(</Staff>)",
        fix_staff,
        mscx,
        flags=re.S,
    )


def _strip_short_rest_measures(mscx: str) -> str:
    """Verwijder lege korte rust-maten (spacers / lege ``|:``-maat).

    Geen HBox-vervanging: mid-systeem-HBox tekent in MuseScore een accolade.
    """

    def fix_staff(staff_m: re.Match[str]) -> str:
        body = staff_m.group(0)
        parts = re.split(r"(?=<Measure\b|<HBox\b|<VBox\b)", body)
        out = [parts[0]]
        for part in parts[1:]:
            if part.startswith("<Measure") and _is_short_rest_only_measure(part):
                continue
            out.append(part)
        return "".join(out)

    return re.sub(r"<Staff\b[^>]*>.*?</Staff>", fix_staff, mscx, flags=re.S)


def _replace_short_rest_measures_with_hbox(mscx: str) -> str:
    """Deprecated alias — strips short rests (no mid-system HBox)."""
    return _strip_short_rest_measures(mscx)


def _insert_hbox_before_cues(mscx: str, texts: list[str]) -> str:
    """No-op: mid-systeem-HBox veroorzaakt MuseScore-accolades."""
    del texts
    return mscx


def _strip_trailing_hboxes(mscx: str) -> str:
    """HBox aan het eind van een Staff (vóór ``</Staff>`` / colofon-VBox) weg."""

    def fix_staff(staff_m: re.Match[str]) -> str:
        body = staff_m.group(0)
        prev = None
        while prev != body:
            prev = body
            body = re.sub(
                r"<HBox>\s*<width>[^<]*</width>\s*"
                r"(?:<boxAutoSize>[^<]*</boxAutoSize>\s*)?"
                r"</HBox>\s*(?=</Staff>|<VBox>)",
                "",
                body,
                count=1,
                flags=re.S,
            )
        return body

    return re.sub(r"<Staff\b[^>]*>.*?</Staff>", fix_staff, mscx, flags=re.S)


def _ensure_style_overrides(mscx: str) -> str:
    if "<Style>" not in mscx:
        insert = "<Style>" + "".join(
            f"<{k}>{v}</{k}>" for k, v in _STYLE_OVERRIDES.items()
        ) + "</Style>"
        if "<Part " in mscx or "<Part>" in mscx:
            return mscx.replace("<Part", insert + "<Part", 1)
        return mscx

    for key, val in _STYLE_OVERRIDES.items():
        pat = re.compile(rf"<{key}>.*?</{key}>", re.DOTALL)
        if pat.search(mscx):
            mscx = pat.sub(f"<{key}>{val}</{key}>", mscx)
        else:
            mscx = mscx.replace("<Style>", f"<Style><{key}>{val}</{key}>", 1)
    return mscx
