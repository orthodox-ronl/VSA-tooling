#!/usr/bin/env python3
"""Fase A: toon-4 VSA → ftxt + afgeleide MVSA + S-vergelijking (herstelde versie).

Belangrijke mappingkeuzes (voor Fase B):
- Frasegrens: `*` in VSA, anders niet-lege regels binnen het muziekblok.
  VSA-`//` is géén ftxt-`**` (blad-aanwijzing / cue).
- Klemtoon `'`: alleen VSA-scopes met length_modifier (`_` / `__` / …),
  niet elke toonbeweging. (Structurele ankers ≈ duratieklemtonen.)
- @l.st. = laatste zo gemarkeerde klemtoon in de frase.
- Cadens = lettergrepen ná die klemtoon; formule verwacht vaste cadenslengte.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from vsa.ast import PitchMarkerNode, PitchTransitionNode, ScopeNode, TextNode  # noqa: E402
from vsa.dutch_syllables import recite_syllables  # noqa: E402
from vsa.music import Pitch  # noqa: E402
from vsa.pitch_resolver import PitchResolver  # noqa: E402
from vsa.vsa_stanzas import parse_vsa_source  # noqa: E402
from vsa.yaml_frontmatter import parse_vsa_frontmatter  # noqa: E402

VSA_DIR = Path(__file__).resolve().parents[1] / "vsa-bestanden"
FORMULE = (
    Path(__file__).resolve().parents[1]
    / "tropaar-toon-4"
    / "formules"
    / "tropaar-toon-4.formule.mvsa"
)

MI, FA, RE = "A4", "Bb4", "G4"


@dataclass
class Syl:
    text: str
    stressed: bool = False
    pitch: Pitch | None = None
    word_start: bool = False


@dataclass
class Phrase:
    syllables: list[Syl] = field(default_factory=list)


def pitch_key(p: Pitch | None) -> str:
    if p is None:
        return "?"
    alter = {0: "", 1: "#", -1: "b"}.get(int(p.alter), f"({p.alter})")
    return f"{p.step}{alter}{p.octave}"


def restore_original_body(raw: str) -> tuple[str, str]:
    """Return (frontmatter_with_dashes, original_vsa_body)."""
    fm_m = re.match(r"^(---\n.*?\n---\n)", raw, flags=re.S)
    fm = fm_m.group(1) if fm_m else ""
    rest = raw[len(fm) :]
    if "# === oorspronkelijke VSA" in rest:
        m = re.search(r"# === oorspronkelijke VSA[^\n]*\n(.*)\Z", rest, flags=re.S)
        if not m:
            raise ValueError("kan oorspronkelijke VSA-commentaar niet vinden")
        lines = []
        for ln in m.group(1).splitlines():
            if ln.startswith("# "):
                lines.append(ln[2:])
            elif ln == "#":
                lines.append("")
            else:
                lines.append(ln)
        body = "\n".join(lines).strip() + "\n"
        return fm, body
    if "# === nieuwe notatie" in rest:
        body = rest.split("# === nieuwe notatie", 1)[0].strip() + "\n"
        return fm, body
    return fm, rest if rest.endswith("\n") else rest + "\n"


def music_lines(body: str) -> list[str]:
    """Extract sung lines (skip HTML comments); keep order."""
    lines = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("<!--"):
            continue
        lines.append(s)
    return lines


def split_phrase_texts(body: str) -> list[str]:
    """Phrase texts from VSA body."""
    joined = "\n".join(music_lines(body))
    # Strip outer [//:] … [//:]
    joined = re.sub(r"^\[//:\]\s*", "", joined.strip())
    joined = re.sub(r"\s*\[//:\]\s*$", "", joined.strip())
    if "*" in joined:
        parts = re.split(r"\s*\*\s*", joined)
        return [p.strip() for p in parts if p.strip()]
    # Geen *: regel = frase (na strip van VSA // cue-prefix op een regel)
    out = []
    for ln in music_lines(body):
        s = ln.strip()
        s = re.sub(r"^\[//:\]\s*", "", s)
        s = re.sub(r"\s*\[//:\]\s*$", "", s)
        # VSA blad-cue // aan begin van regel: hoort bij tekst, geen frase-einde
        s = re.sub(r"^//\s*", "", s)
        if s:
            out.append(s)
    return out


def parse_phrase_vsa(fragment: str, resolver: PitchResolver, started: list[bool]) -> list[Syl]:
    """Parse one phrase fragment as mini-document continuation."""
    # Wrap with pitch marker if needed
    text = fragment
    if not started[0]:
        # keep existing markers in fragment; if none, assume already started globally
        pass
    wrap = text if text.startswith("[") else text
    # Use parser on a fake doc with metadata already applied via resolver state
    mini = "---\ndo: F4\nmode: major\n---\n\n" + (
        "[//:] " + wrap + " [//:]" if "[//:]" not in wrap else wrap
    )
    # Better: reuse nodes from full doc — handled in extract_all instead
    raise NotImplementedError


def extract_all(meta: dict, body: str) -> list[Phrase]:
    full = (
        f"---\ndo: {meta.get('do') or 'F4'}\nmode: {meta.get('mode') or 'major'}\n---\n\n"
        + body
    )
    _m, doc = parse_vsa_source(full)
    resolver = PitchResolver.from_metadata(
        {"do": meta.get("do") or "F4", "mode": meta.get("mode") or "major"}
    )
    started = False
    # Build flat syllable stream with phrase breaks
    phrase_texts = split_phrase_texts(body)
    # Walk nodes into syllables; assign to phrases by consuming `*` or newlines
    syls_flat: list[Syl] = []
    pending = ""
    pending_word_start = True

    def emit_pending():
        nonlocal pending, pending_word_start
        chunk = pending
        pending = ""
        if not chunk.strip():
            pending_word_start = True
            return
        # preserve leading space → word boundary
        if chunk.startswith(" ") or chunk.startswith("\n"):
            pending_word_start = True
        tokens = chunk.split()
        for ti, token in enumerate(tokens):
            units = recite_syllables(token)
            for ui, (core, _syllabic) in enumerate(units):
                ws = pending_word_start and ui == 0
                syls_flat.append(
                    Syl(
                        text=core,
                        stressed=False,
                        pitch=resolver.current_pitch,
                        word_start=ws,
                    )
                )
                pending_word_start = False
            pending_word_start = True  # space between tokens
        pending_word_start = True

    for n in doc.nodes:
        if isinstance(n, PitchMarkerNode):
            if not started:
                resolver.apply_start_marker(list(n.height_modifier))
                started = True
            continue
        if isinstance(n, PitchTransitionNode):
            resolver.apply_start_marker(list(n.to_ehm))
            continue
        if isinstance(n, TextNode):
            t = n.text
            # phrase break * 
            if "*" in t:
                parts = re.split(r"\*", t)
                for i, part in enumerate(parts):
                    pending += part
                    emit_pending()
                    if i < len(parts) - 1:
                        syls_flat.append(Syl(text="*", stressed=False, pitch=None))
                continue
            pending += t
            continue
        if isinstance(n, ScopeNode):
            emit_pending()
            for ehm in n.height_modifier:
                resolver.resolve_ehm(ehm)
            stressed = bool(n.length_modifier)
            text = (n.text or "").strip()
            if text:
                syls_flat.append(
                    Syl(
                        text=text,
                        stressed=stressed,
                        pitch=resolver.current_pitch,
                        word_start=pending_word_start,
                    )
                )
                pending_word_start = False
            continue
    emit_pending()

    # Split flat on * markers; if no *, split by phrase_texts counts via greedy match
    if any(s.text == "*" for s in syls_flat):
        phrases: list[Phrase] = []
        cur: list[Syl] = []
        for s in syls_flat:
            if s.text == "*":
                if cur:
                    phrases.append(Phrase(cur))
                    cur = []
            else:
                cur.append(s)
        if cur:
            phrases.append(Phrase(cur))
        return phrases

    # No * in AST: split syllables into len(phrase_texts) groups by matching text length
    # Fall back: one phrase per non-empty original line — match by concatenating
    phrases = []
    # Rebuild from phrase_texts by re-parsing each line with continuing resolver
    resolver = PitchResolver.from_metadata(
        {"do": meta.get("do") or "F4", "mode": meta.get("mode") or "major"}
    )
    started = False
    # Apply start from full doc first marker
    for n in doc.nodes:
        if isinstance(n, PitchMarkerNode):
            resolver.apply_start_marker(list(n.height_modifier))
            started = True
            break

    for pt in phrase_texts:
        mini_body = f"[//:] {pt} [//:]"
        mini = (
            f"---\ndo: {meta.get('do') or 'F4'}\nmode: {meta.get('mode') or 'major'}\n---\n\n"
            + mini_body
        )
        _mm, d2 = parse_vsa_source(mini)
        # Don't re-apply [//:] start — use transition from current
        # Skip first PitchMarker in mini (would reset). Manually walk.
        local: list[Syl] = []
        pending = ""
        pending_word_start = True

        def emit2():
            nonlocal pending, pending_word_start
            chunk = pending
            pending = ""
            if not chunk.strip():
                return
            for token in chunk.split():
                units = recite_syllables(token)
                for ui, (core, _) in enumerate(units):
                    local.append(
                        Syl(
                            core,
                            False,
                            resolver.current_pitch,
                            word_start=(pending_word_start and ui == 0),
                        )
                    )
                    pending_word_start = False
                pending_word_start = True
            pending_word_start = True

        first_marker = True
        for n in d2.nodes:
            if isinstance(n, PitchMarkerNode):
                if first_marker:
                    first_marker = False
                    if not started:
                        resolver.apply_start_marker(list(n.height_modifier))
                        started = True
                    # else ignore re-start on mi
                continue
            if isinstance(n, TextNode):
                pending += n.text
                continue
            if isinstance(n, ScopeNode):
                emit2()
                for ehm in n.height_modifier:
                    resolver.resolve_ehm(ehm)
                text = (n.text or "").strip()
                if text:
                    local.append(
                        Syl(
                            text,
                            bool(n.length_modifier),
                            resolver.current_pitch,
                            word_start=pending_word_start,
                        )
                    )
                    pending_word_start = False
                continue
        emit2()
        if local:
            phrases.append(Phrase(local))
    return phrases


def phrase_to_ftxt(p: Phrase) -> str:
    parts: list[str] = []
    for i, s in enumerate(p.syllables):
        piece = s.text
        if s.stressed and not piece.endswith("'"):
            piece += "'"
        if i == 0 or s.word_start:
            if i > 0:
                parts.append(" ")
            parts.append(piece)
        else:
            parts.append("-" + piece)
    return "".join(parts)


def assign_blok(i: int, n: int) -> str:
    if i == n - 1:
        return "laatste"
    return "f1" if i % 2 == 0 else "f2"


def map_s(blok: str, syls: list[Syl]) -> tuple[list[str], list[str], list[str]]:
    stresses = [i for i, s in enumerate(syls) if s.stressed]
    issues: list[str] = []
    if not syls:
        return [], [], ["lege frase"]
    if not stresses:
        issues.append("geen '_'‑klemtoon in VSA-scopes → geen @l.st.; fallback laatste syl")
        stresses = [len(syls) - 1]

    derived: list[str] = []
    l_toks: list[str] = []

    def add(syl: Syl, pitch: str, elm: str = ""):
        derived.append(pitch)
        t = syl.text.rstrip("'")
        l_toks.append(f"{t}{elm}" if elm else t)

    last = stresses[-1]
    if blok in ("f1", "laatste"):
        for i, s in enumerate(syls):
            if i < last:
                add(s, MI)
            elif i == last:
                add(s, MI, "_")
            else:
                after = i - last
                if blok == "f1":
                    add(s, FA if after == 1 else MI, "_")
                    if after > 2:
                        issues.append(f"f1: extra cadens-syl #{after}")
                else:
                    add(s, RE if after == 1 else MI, "_" if after == 1 else "__")
                    if after > 2:
                        issues.append(f"laatste: extra cadens-syl #{after}")
        after_count = len(syls) - 1 - last
        if after_count == 0:
            issues.append(f"{blok}: 0 syl na @l.st. (formule wil 2 cadensnoten)")
        elif after_count == 1:
            issues.append(f"{blok}: 1 syl na @l.st. (formule wil 2 cadensnoten)")
    else:  # f2
        first = stresses[0]
        for i, s in enumerate(syls):
            if i < first:
                add(s, MI)
            elif i == first:
                add(s, FA, "_")
            elif i < last:
                add(s, FA)
            elif i == last:
                add(s, FA, "_")
            else:
                after = i - last
                add(s, MI, "_")
                if after > 1:
                    issues.append(f"f2: extra na @l.st. #{after}")
        after_count = len(syls) - 1 - last
        if after_count == 0:
            issues.append("f2: 0 syl na @l.st. (formule wil slot mi)")
    return derived, l_toks, issues


def compress_voice(xs: list[str]) -> str:
    if not xs:
        return ""
    out = [xs[0]]
    prev = xs[0]
    for x in xs[1:]:
        if x == prev:
            out.append("-")
        else:
            out.append(x)
            prev = x
    return " ".join(out) + " |"


def satb_from_s(s_pitches: list[str]) -> dict[str, str]:
    smap = {MI: "a", FA: "bb", RE: "g"}
    amap = {MI: "f", FA: "g", RE: "e"}
    tmap = {MI: "c", FA: "d", RE: "c"}
    bmap = {MI: "f", FA: "g", RE: "c"}
    return {
        "S": compress_voice([smap.get(p, "a") for p in s_pitches]),
        "A": compress_voice([amap.get(p, "f") for p in s_pitches]),
        "T": compress_voice([tmap.get(p, "c") for p in s_pitches]),
        "B": compress_voice([bmap.get(p, "f") for p in s_pitches]),
    }


def compare(vsa: list[str], der: list[str]) -> list[str]:
    if vsa == der:
        return ["S-hoogtes: IDENTIEK"]
    lines = [f"S-hoogtes: VERSCHIL — VSA {len(vsa)}, afgeleid {len(der)}"]
    diffs = 0
    for i in range(max(len(vsa), len(der))):
        a = vsa[i] if i < len(vsa) else "—"
        b = der[i] if i < len(der) else "—"
        if a != b:
            diffs += 1
            if diffs <= 10:
                lines.append(f"  [{i}] VSA={a} afgeleid={b}")
    if diffs > 10:
        lines.append(f"  … +{diffs - 10} meer")
    lines.append(f"Afwijkingen: {diffs}/{max(len(vsa), len(der))}")
    # classify
    if len(vsa) == len(der):
        # how many would match if we aligned cadence from first pitch leave
        lines.append(
            "Lengtes gelijk → verschil zit in welke lettergreep welke formuletoon krijgt."
        )
    return lines


def process_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    fm, body = restore_original_body(raw)
    meta, _ = parse_vsa_frontmatter(fm + body)
    phrases = extract_all(meta, body)
    n = len(phrases)

    ftxt_lines = []
    mvsa_blocks = []
    analysis: list[str] = []
    all_issues: list[str] = []
    identical_phrases = 0

    for i, ph in enumerate(phrases):
        blok = assign_blok(i, n)
        ftxt = phrase_to_ftxt(ph)
        end = "**" if i == n - 1 else "*"
        ftxt_lines.append(f"{ftxt} {end}")
        der, l_toks, issues = map_s(blok, ph.syllables)
        vsa_p = [pitch_key(s.pitch) for s in ph.syllables]
        voices = satb_from_s(der)
        mvsa_blocks.append(
            f"@blok {blok}  # frase {i + 1}/{n}\n"
            f"L: {' '.join(l_toks)} |\n"
            f"S: {voices['S']}\n"
            f"A: {voices['A']}\n"
            f"T: {voices['T']}\n"
            f"B: {voices['B']}"
        )
        analysis.append(f"### Frase {i + 1} → `{blok}` ({len(ph.syllables)} syl)")
        analysis.append(f"- ftxt: {ftxt} {end}")
        analysis.append(
            f"- klemtonen: {[j for j, s in enumerate(ph.syllables) if s.stressed]}"
        )
        analysis.append(f"- VSA S: {' '.join(vsa_p)}")
        analysis.append(f"- afgeleid S: {' '.join(der)}")
        cmp = compare(vsa_p, der)
        if cmp and cmp[0].startswith("S-hoogtes: IDENTIEK"):
            identical_phrases += 1
        analysis.extend(cmp)
        for iss in issues:
            analysis.append(f"ISSUE: {iss}")
            all_issues.append(f"{path.name} f{i + 1}/{blok}: {iss}")
        analysis.append("")

    title = meta.get("title") or meta.get("titel") or path.stem
    mvsa_head = "\n".join(
        [
            f'@title "{title}"',
            f"@do {meta.get('do') or 'F4'}",
            f"@mode {meta.get('mode') or 'major'}",
            "@oct S=0 A=0 T=-1 B=-1",
            "@speelplan |: f1, f2 :| laatste",
            "# Afgeleid (experimenteel) uit ftxt + tropaar-toon-4.formule.mvsa",
        ]
    )
    vsa_comment = "\n".join(
        ("# " + ln if ln.strip() else "#") for ln in body.strip().splitlines()
    )
    new_body = "\n".join(
        [
            "",
            "# === nieuwe notatie (tekst + klemtoon) ===",
            "# @formule tropaar-toon-4",
            *ftxt_lines,
            "",
            "# === afgeleide mvsa (formule tropaar-toon-4) ===",
            mvsa_head,
            "",
            *mvsa_blocks,
            "",
            "# === analyse S-stem vs oorspronkelijke VSA ===",
            *["# " + ln if ln else "#" for ln in analysis],
            "",
            "# === oorspronkelijke VSA (commentaar) ===",
            vsa_comment,
            "",
        ]
    )
    path.write_text(fm + new_body, encoding="utf-8", newline="\n")
    return {
        "file": path.name,
        "phrases": n,
        "identical_phrases": identical_phrases,
        "issues": all_issues,
        "analysis": analysis,
    }


def main() -> int:
    files = sorted(VSA_DIR.glob("*toon-4*.vsa"))
    results = []
    for f in files:
        print("process", f.name, flush=True)
        try:
            results.append(process_file(f))
        except Exception as e:
            import traceback

            traceback.print_exc()
            results.append({"file": f.name, "error": str(e), "issues": [str(e)]})

    report = VSA_DIR / "FASE-A-B-RAPPORT.md"
    lines = [
        "# Fase A/B — tropaar/kondak toon 4 × formule",
        "",
        f"Formule: `{FORMULE.as_posix()}`",
        "",
        "## Fase A — per bestand",
        "",
    ]
    all_issues: list[str] = []
    id_ph = 0
    tot_ph = 0
    for r in results:
        if r.get("error"):
            lines.append(f"- **{r['file']}**: FOUT `{r['error']}`")
            continue
        id_ph += r["identical_phrases"]
        tot_ph += r["phrases"]
        lines.append(
            f"- **{r['file']}**: {r['phrases']} frasen, "
            f"S-identiek {r['identical_phrases']}/{r['phrases']}, "
            f"issues={len(r['issues'])}"
        )
        all_issues.extend(r["issues"])
    lines += ["", f"Frasen met identieke S: **{id_ph}/{tot_ph}**", "", "## ISSUES", ""]
    kinds = Counter()
    for iss in all_issues:
        if "0 syl na @l.st" in iss:
            kinds["0 lettergrepen na @l.st."] += 1
        elif "1 syl na @l.st" in iss:
            kinds["1 lettergreep na @l.st. (wil 2)"] += 1
        elif "geen '_'‑klemtoon" in iss or "geen '_'‑klemtoon" in iss:
            kinds["geen length-klemtoon"] += 1
        elif "fallback" in iss:
            kinds["geen length-klemtoon"] += 1
        else:
            kinds["overig"] += 1
        lines.append(f"- {iss}")
    lines += ["", "## Clusters", ""]
    for k, v in kinds.most_common():
        lines.append(f"- {k}: {v}")

    lines += [
        "",
        "## Fase B — bevindingen en voorstel",
        "",
        "### Wat structureel fout ging",
        "",
        "1. **Cadens vs klemtoon** — In de VSA begint de cadens vaak *vóór* de",
        "   laatste `_`-lettergreep (toon verlaat recite; daarna nog 1–2 syl).",
        "   Onze ftxt-regel «@l.st. = laatste `_`» + «alles erna = cadens» botst",
        "   met «formule heeft altijd 2 vaste cadensnoten»: teksten hebben 0 of 1",
        "   syl na die klemtoon, terwijl VSA-cadensnoten *op* die klemtonen liggen.",
        "",
        "2. **Klemtoon ≠ anker** — Lexicale `_` in VSA markeert duur/gewicht, niet",
        "   per se toonboek-`e.st.`/`l.st.`. Te veel of verkeerde `'` verschuift",
        "   @e.st./@l.st.",
        "",
        "3. **Frasegrenzen** — Sommige bronnen hebben `*`, andere alleen regels;",
        "   VSA-`//` is blad-cue, geen `**`. Zonder consistente frasegrenzen",
        "   klopt `@speelplan |: f1,f2 :| laatste` niet (alles → verkeerde blokken).",
        "",
        "4. **Melisma** (`{-&/…}`) — één lettergreep, meerdere hoogtes in VSA;",
        "   ftxt heeft één slot → S-lengte kan toevallig kloppen maar toon niet.",
        "",
        "### Concreet voorstel",
        "",
        "1. **Ftxt-ankers expliciet maken** (kortetermijn): markeer structureel",
        "   `@e` / `@l` (of `e.` / `l.`) op de ankerlettergrepen i.p.v. alle `_`",
        "   uit VSA als `'`. Optioneel: alleen `'` = ankerklemtoon.",
        "",
        "2. **Cadensmodel versoepelen**: vaste `/_ \\_` niet eisen als syl-telling;",
        "   cadensnoten mogen op de ankerlettergreep + melisma (zoals VSA), of",
        "   optionele cadensslots (`/?` `\\?`) zoals haakjesnoten.",
        "",
        "3. **Frase = `*` of expliciete regels** in ftxt afdwingen; `**` alleen",
        "   slotfrase; VSA-`//` nooit automatisch naar `**`.",
        "",
        "4. **Referentie-S**: vergelijk niet alleen eindtonen per syl maar",
        "   «recite-toon tot eerste afwijking» — dat is dichter bij toonboek.",
        "",
        "5. **Volgende experiment**: 2–3 handmatig gecorrigeerde ftxt (Elia,",
        "   Nicolaas, Hosea) met expliciete `@l`/`@e`, opnieuw afleiden, tot S",
        "   ≥90% match — dán pas toolen.",
        "",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote", report)
    print(f"identical phrases {id_ph}/{tot_ph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
