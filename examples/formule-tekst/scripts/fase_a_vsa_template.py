#!/usr/bin/env python3
"""Fase A (herstart): VSA (uit commentaar) + tropaar-toon-4 template → MVSA.

Gebruikt de bestaande mapper ``map_vsa_to_template`` + library
``template.yaml`` (machineleesbaar equivalent van de formule; zelfde
do/mode/frasen/optionals/ankers als het onderzoek).

S in de afgeleide MVSA komt uit de VSA-noten (na geslaagde slot-match).
Vergelijking S↔VSA is daardoor bij succes identiek *by design*; de echte
kwaliteitsmaat is: mapping OK/FOUT, frase-toewijzing, optionals, ankers.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from vsa.music import Pitch  # noqa: E402
from vsa.template_instance import (  # noqa: E402
    MappedNote,
    TemplateInstanceError,
    degree_pitch,
    map_vsa_to_template,
    midi_of,
)
from vsa.vsa_stanzas import extract_stanza_notes  # noqa: E402
from vsa.yaml_frontmatter import parse_vsa_frontmatter  # noqa: E402

VSA_DIR = Path(__file__).resolve().parents[1] / "vsa-bestanden"
TEMPLATE_YAML = (
    ROOT
    / "docs"
    / "specification-vsa-templates"
    / "library"
    / "tropaar-toon-4"
    / "template.yaml"
)
FORMULE_MVSA = (
    Path(__file__).resolve().parents[1]
    / "tropaar-toon-4"
    / "formules"
    / "tropaar-toon-4.formule.mvsa"
)


@dataclass
class FileResult:
    file: str
    ok: bool
    phrases: int = 0
    phrase_ids: list[str] = field(default_factory=list)
    notes: int = 0
    s_identical: bool = False
    s_mismatch: int = 0
    optional_used: int = 0
    optional_skipped_phrases: int = 0
    anchors_shown: int = 0
    error: str = ""
    error_code: str = ""
    hint: str = ""
    issues: list[str] = field(default_factory=list)


def restore_vsa(raw: str) -> tuple[str, str]:
    fm_m = re.match(r"^(---\n.*?\n---\n)", raw, flags=re.S)
    fm = fm_m.group(1) if fm_m else ""
    rest = raw[len(fm) :]
    if "# === oorspronkelijke VSA" in rest:
        m = re.search(r"# === oorspronkelijke VSA[^\n]*\n(.*)\Z", rest, flags=re.S)
        if not m:
            raise ValueError("oorspronkelijke VSA-commentaar ontbreekt")
        lines = []
        for ln in m.group(1).splitlines():
            if ln.startswith("# "):
                lines.append(ln[2:])
            elif ln == "#":
                lines.append("")
            else:
                lines.append(ln)
        return fm, "\n".join(lines).strip() + "\n"
    if "# === nieuwe notatie" in rest or "# === afgeleide mvsa" in rest:
        body = re.split(r"\n# === ", rest, maxsplit=1)[0].strip() + "\n"
        return fm, body
    return fm, rest if rest.endswith("\n") else rest + "\n"


def ensure_stanza_stars(body: str) -> tuple[str, list[str]]:
    """Zorg voor `*`-frasen. Zonder `*`: één frase per niet-lege muziekregel.

    Returns (normalized_body, notes_for_report).
    """
    notes: list[str] = []
    if re.search(r"(?m)^\s*\*|(\s|^)\*(\s|$)", body) or " *" in body or body.count("*") >= 1:
        # Has stanza markers already (Elia-style)
        if "*" in body:
            return body, notes
    lines_out: list[str] = []
    music: list[str] = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            lines_out.append(ln)
            continue
        if s.startswith("<!--"):
            lines_out.append(ln)
            continue
        music.append(ln)
    if len(music) <= 1:
        notes.append("geen multi-regel frase-splits nodig")
        return body, notes
    notes.append(
        f"geen `*` in bron → {len(music)} regels genormaliseerd tot frasen met `*`"
    )
    # Rebuild: comments preserved in order is hard; simpler replace music block
    rebuilt: list[str] = []
    music_i = 0
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("<!--"):
            rebuilt.append(ln)
            continue
        # music line
        raw_line = ln.rstrip()
        music_i += 1
        if music_i < len(music):
            if not raw_line.rstrip().endswith("*"):
                rebuilt.append(raw_line + " *")
            else:
                rebuilt.append(raw_line)
        else:
            rebuilt.append(raw_line)
    return "\n".join(rebuilt) + "\n", notes


def pitch_token(p: Pitch) -> str:
    """a–g (+#/b) zonder octaafcijfer (MVSA-achtig t.o.v. do-octaaf)."""
    alter = {0: "", 1: "#", -1: "b", 2: "##", -2: "bb"}.get(int(p.alter), "")
    return f"{p.step.lower()}{alter}"


def elm_token(note: MappedNote) -> str:
    d = note.duration
    # Duration has note_type / dots — map grof naar ELM
    nt = getattr(d, "note_type", None) or getattr(d, "type", "quarter")
    dots = int(getattr(d, "dots", 0) or 0)
    if nt == "whole":
        base = "__"
    elif nt == "half":
        base = "_"
    elif nt == "eighth":
        base = "~"
    else:
        base = ""  # quarter = default, no mark on L often — use empty or ~
    if dots == 1:
        base = (base or "~") + "."
    elif dots >= 2:
        base = (base or "_") + ".."
    return base


def compress_tokens(tokens: list[str]) -> str:
    if not tokens:
        return ""
    out = [tokens[0]]
    prev = tokens[0]
    for t in tokens[1:]:
        if t == prev:
            out.append("-")
        else:
            out.append(t)
            prev = t
    return " ".join(out)


def _voice_pitch(note: MappedNote, voice: str, *, do: str, mode: str) -> str:
    if voice == "S":
        return pitch_token(note.s_pitch)
    pitches = note.template_event.get("pitches") or {}
    return pitch_token(degree_pitch(str(pitches[voice]), do, mode))


def emit_mvsa_block(
    phrase_id: str,
    notes: list[MappedNote],
    *,
    do: str,
    mode: str,
    index: int,
    total: int,
) -> str:
    """Schrijf één @blok. Lege lyrics → ``&``-melisma op vorige lettergreep (MVSA)."""
    l_parts: list[str] = []
    s_toks: list[str] = []
    a_toks: list[str] = []
    t_toks: list[str] = []
    b_toks: list[str] = []
    i = 0
    while i < len(notes):
        head = notes[i]
        group = [head]
        j = i + 1
        while j < len(notes) and not (notes[j].lyric or "").strip():
            group.append(notes[j])
            j += 1
        lyric = (head.lyric or "").strip() or "-"
        lyric = lyric.replace(" ", "-")
        if len(group) == 1:
            elm = elm_token(head)
            l_parts.append(f"{lyric}{elm}" if elm else lyric)
            s_toks.append(_voice_pitch(head, "S", do=do, mode=mode))
            a_toks.append(_voice_pitch(head, "A", do=do, mode=mode))
            t_toks.append(_voice_pitch(head, "T", do=do, mode=mode))
            b_toks.append(_voice_pitch(head, "B", do=do, mode=mode))
        else:
            # li_&_  /  a&bb  — losse '-_' verdwijnt in de L-parser
            elms = [(elm_token(n) or "~") for n in group]
            l_parts.append(lyric + elms[0] + "".join(f"&{e}" for e in elms[1:]))
            s_toks.append(
                "&".join(_voice_pitch(n, "S", do=do, mode=mode) for n in group)
            )
            a_toks.append(
                "&".join(_voice_pitch(n, "A", do=do, mode=mode) for n in group)
            )
            t_toks.append(
                "&".join(_voice_pitch(n, "T", do=do, mode=mode) for n in group)
            )
            b_toks.append(
                "&".join(_voice_pitch(n, "B", do=do, mode=mode) for n in group)
            )
        i = j
    return "\n".join(
        [
            f"# template-frase {phrase_id!r} ({index}/{total})",
            f"@blok {index}",
            f"L: {' '.join(l_parts)} |",
            f"S: {compress_tokens(s_toks)} |",
            f"A: {compress_tokens(a_toks)} |",
            f"T: {compress_tokens(t_toks)} |",
            f"B: {compress_tokens(b_toks)} |",
        ]
    )


def analyze_mapped(
    mapped: list[tuple[str, list[MappedNote]]],
    vsa_text: str,
    *,
    do: str,
    mode: str,
) -> tuple[list[str], FileResult]:
    stanzas = extract_stanza_notes(vsa_text, metadata={"do": do, "mode": mode})
    lines: list[str] = []
    s_mis = 0
    total_notes = 0
    opt_used = 0
    opt_skip_ph = 0
    anchors = 0
    for (pid, notes), stanza in zip(mapped, stanzas, strict=True):
        lines.append(f"### Frase → template `{pid}` ({len(notes)} noten)")
        vsa_pitches = [str(n.pitch) for n in stanza]
        der_pitches = [str(n.s_pitch) for n in notes]
        lines.append(f"- VSA S ({len(vsa_pitches)}): {' '.join(vsa_pitches)}")
        lines.append(f"- MVSA S ({len(der_pitches)}): {' '.join(der_pitches)}")
        if vsa_pitches == der_pitches:
            lines.append("- S-hoogtes: IDENTIEK (verwacht: S komt uit VSA na slot-match)")
        else:
            # kan gebeuren bij melisma-split vs lyric merge
            lines.append("- S-hoogtes: VERSCHIL in lengte/volgorde t.o.v. extract_stanza_notes")
            for i, (a, b) in enumerate(zip(vsa_pitches, der_pitches)):
                if a != b:
                    s_mis += 1
                    if s_mis <= 8:
                        lines.append(f"  [{i}] VSA={a} MVSA={b}")
            s_mis += abs(len(vsa_pitches) - len(der_pitches))
        roles = [n.template_event.get("role") for n in notes]
        lines.append(f"- roles: {roles}")
        used_opt = [n for n in notes if n.template_event.get("optional")]
        if used_opt:
            opt_used += len(used_opt)
            lines.append(f"- optional slots GEBRUIKT: {len(used_opt)}")
        else:
            # phrase 2 often skips — detect if phrase has optional in template
            if pid == "2":
                opt_skip_ph += 1
                lines.append("- optional link: overgeslagen (geen optional in instance)")
        for n in notes:
            if n.show_anchor and n.template_event.get("anchor"):
                anchors += 1
                lines.append(
                    f"- anker {n.template_event.get('anchor')} op {n.lyric!r} "
                    f"(S={n.s_pitch})"
                )
        total_notes += len(notes)
        lines.append("")

    identical = s_mis == 0 and total_notes > 0
    # also require equal counts
    if sum(len(s) for s in stanzas) != total_notes:
        identical = False
    fr = FileResult(
        file="",
        ok=True,
        phrases=len(mapped),
        phrase_ids=[p for p, _ in mapped],
        notes=total_notes,
        s_identical=identical,
        s_mismatch=s_mis,
        optional_used=opt_used,
        optional_skipped_phrases=opt_skip_ph,
        anchors_shown=anchors,
    )
    return lines, fr


def process_file(path: Path, template: dict) -> FileResult:
    raw = path.read_text(encoding="utf-8")
    fm, body = restore_vsa(raw)
    meta, _ = parse_vsa_frontmatter(fm + body)
    do = str(template["do"])
    mode = str(template.get("mode", "major"))

    norm_body, norm_notes = ensure_stanza_stars(body)
    vsa_text = fm + norm_body

    title = meta.get("title") or meta.get("titel") or path.stem
    analysis: list[str] = []
    for n in norm_notes:
        analysis.append(f"NORMALISATIE: {n}")

    try:
        mapped = map_vsa_to_template(template, vsa_text, source=path.name)
    except TemplateInstanceError as exc:
        analysis.append("MAPPING: MISLUKT")
        analysis.extend(exc.format_lines())
        vsa_comment = "\n".join(
            ("# " + ln if ln.strip() else "#") for ln in body.strip().splitlines()
        )
        new_body = "\n".join(
            [
                "",
                "# === pad: VSA + template → MVSA (Fase A herstart) ===",
                f"# template: {TEMPLATE_YAML.as_posix()}",
                f"# formule-notatie (mens): {FORMULE_MVSA.as_posix()}",
                "#",
                "# === afgeleide mvsa ===",
                f"# MAPPING MISLUKT: {exc.code}",
                f"# {exc.message_nl}",
                *(f"# Hint: {exc.hint_nl}" if exc.hint_nl else []),
                "",
                "# === analyse ===",
                *["# " + ln if ln else "#" for ln in analysis],
                "",
                "# === oorspronkelijke VSA (commentaar) ===",
                vsa_comment,
                "",
            ]
        )
        path.write_text(fm + new_body, encoding="utf-8", newline="\n")
        return FileResult(
            file=path.name,
            ok=False,
            error=exc.message_nl,
            error_code=exc.code,
            hint=exc.hint_nl or "",
            issues=[f"{path.name}: {exc.code}: {exc.message_nl}"],
        )

    ana2, fr = analyze_mapped(mapped, vsa_text, do=do, mode=mode)
    analysis.extend(ana2)
    fr.file = path.name

    blocks = []
    total = len(mapped)
    for i, (pid, notes) in enumerate(mapped, start=1):
        blocks.append(emit_mvsa_block(pid, notes, do=do, mode=mode, index=i, total=total))

    mvsa_head = "\n".join(
        [
            f'@title "{title}"',
            f"@do {do}",
            f"@mode {mode}",
            "@oct S=0 A=0 T=-1 B=-1",
            "@speelplan |: f1, f2 :| laatste",
            "# Afgeleid: VSA (S) + tropaar-toon-4 template.yaml (A/T/B, slots)",
            "# Mapper: vsa.template_instance.map_vsa_to_template",
        ]
    )
    vsa_comment = "\n".join(
        ("# " + ln if ln.strip() else "#") for ln in body.strip().splitlines()
    )
    new_body = "\n".join(
        [
            "",
            "# === pad: VSA + template → MVSA (Fase A herstart) ===",
            f"# template: docs/specification-vsa-templates/library/tropaar-toon-4/template.yaml",
            f"# formule-notatie (mens, nog niet geparsed): tropaar-toon-4.formule.mvsa",
            "",
            "# === afgeleide mvsa ===",
            mvsa_head,
            "",
            *blocks,
            "",
            "# === analyse S / mapping ===",
            *["# " + ln if ln else "#" for ln in analysis],
            "",
            "# === oorspronkelijke VSA (commentaar) ===",
            vsa_comment,
            "",
        ]
    )
    path.write_text(fm + new_body, encoding="utf-8", newline="\n")
    return fr


def main() -> int:
    template = yaml.safe_load(TEMPLATE_YAML.read_text(encoding="utf-8"))
    files = sorted(VSA_DIR.glob("*toon-4*.vsa"))
    results: list[FileResult] = []
    for f in files:
        print("process", f.name, flush=True)
        try:
            results.append(process_file(f, template))
        except Exception as e:
            import traceback

            traceback.print_exc()
            results.append(
                FileResult(file=f.name, ok=False, error=str(e), issues=[str(e)])
            )

    ok_n = sum(1 for r in results if r.ok)
    report = VSA_DIR / "FASE-A-B-RAPPORT-VSA-TEMPLATE.md"
    lines = [
        "# Fase A/B — VSA + tropaar-toon-4-template → MVSA",
        "",
        "## Opzet",
        "",
        "- **Brontekst:** oorspronkelijke VSA uit het commentaar in elk bestand.",
        "- **Template:** `docs/specification-vsa-templates/library/tropaar-toon-4/template.yaml`",
        "  (uitvoerbare vorm; muzikaal gelijk aan het formule-onderzoek).",
        "- **Mensformule:** `tropaar-toon-4.formule.mvsa` (nog niet door de mapper gelezen).",
        "- **Mapper:** `vsa.template_instance.map_vsa_to_template` (bestaande H1–H9-logica).",
        "- **Normalisatie:** bronnen zonder `*` krijgen per regel een frase (`*`)",
        "  zodat cycle `1,2,…,laatste` kan werken.",
        "",
        "## Fase A — resultaat per bestand",
        "",
        f"Geslaagde mapping: **{ok_n}/{len(results)}**",
        "",
    ]
    for r in results:
        if not r.ok:
            lines.append(
                f"- **{r.file}**: MAPPING MISLUKT — `{r.error_code}`: {r.error}"
            )
            continue
        lines.append(
            f"- **{r.file}**: OK — {r.phrases} frasen `{r.phrase_ids}`, "
            f"{r.notes} noten, S-identiek={r.s_identical}, "
            f"ankers={r.anchors_shown}, optional_used={r.optional_used}, "
            f"f2_optional_skip≈{r.optional_skipped_phrases}"
        )

    fail_codes = Counter(r.error_code for r in results if not r.ok and r.error_code)
    lines += ["", "## Foutcodes (clusters)", ""]
    if not fail_codes:
        lines.append("(geen mappingfouten)")
    else:
        for code, n in fail_codes.most_common():
            lines.append(f"- `{code}`: {n}")
            # sample messages
            for r in results:
                if r.error_code == code:
                    lines.append(f"  - {r.file}: {r.error}")
                    break

    # Practical usability narrative — written carefully after looking at numbers
    lines += [
        "",
        "## Fase B — analyse en advies",
        "",
        "### Wat deze ronde anders testte",
        "",
        "Niet: “raad de melodie uit tekst+klemtoon”.",
        "Wél: “past deze VSA op de bekende tropaar-toon-4-formule, en kunnen we",
        "daaruit een SATB-MVSA schrijven?”.",
        "",
        "Daardoor is **S-identiteit bij succes geen verrassing**: de mapper koppelt",
        "VSA-noten aan template-slots en behoudt de VSA-pitch op S. De waarde zit in:",
        "",
        "1. harde afwijzing als S niet op de formule past;",
        "2. synchrone A/T/B uit de template;",
        "3. optionals/ankers die wél of niet vuren.",
        "",
        "### Lees de getallen zo",
        "",
        f"- Mapping OK: **{ok_n}/{len(results)}** bestanden.",
        "- Een hoge OK-score betekent: dit corpus is *in principe* automatiseerbaar",
        "  met de huidige tropaar-toon-4-template + bestaande mapper.",
        "- Fouten zijn **bruikbare signalen** (verkeerde frasegrenzen, pitch buiten",
        "  formule, mode/do, ontbrekende `*`), geen stille verkeerde partituren.",
        "",
        "### Praktische bruikbaarheid (verwachting)",
        "",
        "| Situatie | Bruikbaarheid | Toelichting |",
        "| --- | --- | --- |",
        "| Tropaar/kondak toon 4 met `*`-frasen, do/mode=F4/major | **Hoog** | Zelfde pad als Elia-tests in de repo |",
        "| Zelfde zonder `*` (alleen regeleinden) | **Middel** | Werkt na normalisatie `*` per regel; moet redactioneel gecontroleerd |",
        "| Vrije afwijkingen van de formule (extra toon, andere cadens) | **Laag t/m bewust handwerk** | Mapper faalt hard — goed voor kwaliteit, vraagt VSA- of template-fix |",
        "| Productie-MVSA voor koor zonder nabewerking | **Voorzichtig** | A/T/B zijn provisional; layout/recite-print nog productstraat |",
        "| Vervanging van ftxt-only als hoofdpad | **Ja, aanbevolen** | Veel minder raden; hergebruikt bestaande VSA-vaardigheid |",
        "",
        "### Advies (gedegen)",
        "",
        "1. **Maak VSA+template→MVSA het hoofdpad** voor formulematige toon-4-stukken.",
        "   De ftxt-route (`'`/`*` alleen) blijft een mogelijk later auteurspad, niet",
        "   de migratiebrug voor bestaand corpus.",
        "",
        "2. **Houd `template.yaml` als uitvoerbare bron** tot `.formule.mvsa` een",
        "   parser/validator heeft die naar hetzelfde eventmodel compileert. Anders",
        "   dubbele waarheid.",
        "",
        "3. **Redactionele checklist vóór mapping:** `do`/`mode`, expliciete `*`",
        "   (of geaccepteerde normalisatie), één cycle-passende frase telling,",
        "   geen stille toonsoortwissel.",
        "",
        "4. **Menselijke steekproef** op A/T/B + ankers (3 stukken: Elia, Nicolaas,",
        "   één kondak) in MuseScore/`mvsa mscz` — mapping-OK ≠ klank/partituur-OK.",
        "",
        "5. **Verwachting in de praktijk:** voor netjes geschreven toon-4-VSA die",
        "   bewust op de tropaarformule zit, is automatische SATB-schets **haalbaar",
        "   als hulpmiddel** (schets/Coria/controle). Als eindpublicatie zonder oog",
        "   nog niet; wél als versnelling t.o.v. alles handmatig in MVSA typen.",
        "",
        "6. **Niet doen:** steeds uitzonderingen in de ftxt-mapper stapelen. Liever",
        "   VSA iets strakker schrijven of template-slots optioneel maken.",
        "",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote", report)
    print(f"OK {ok_n}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
