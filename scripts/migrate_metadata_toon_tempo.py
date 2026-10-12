"""Voeg ``@toon`` / optioneel ``@tempo 130`` toe aan ``.mvsa``-bestanden.

Leid ``@toon`` af uit ``@title`` (``Toon N``) of pad/bestandsnaam (``toon-N``).
Bestaande ``@toon`` / ``@tempo`` blijven onaangeroerd.

Standaard: dry-run (alleen rapport). Schrijven: ``--apply``.

Voorbeelden::

    python scripts/migrate_metadata_toon_tempo.py examples\\mvsa
    python scripts/migrate_metadata_toon_tempo.py ..\\bibliotheek --apply
    python scripts/migrate_metadata_toon_tempo.py . --tempo --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Document-metadata die in de kop bij elkaar horen (vóór @do / @sectie / …).
_HEADER_META = frozenset(
    {
        "title",
        "composer",
        "copyright",
        "bron",
        "ondertitel",
        "tekstdichter",
        "arrangeur",
        "vertaler",
        "tempo",
        "toon",
        "genre",
        "opmerkingen",
    }
)

_DIRECTIVE_RE = re.compile(
    r"^(\s*)@([A-Za-z][A-Za-z-_]*)(?::)?(?:\s+(.*))?$"
)
_TITLE_TOON_RE = re.compile(
    r"(?i)\btoon\s*([1-8])\b"
)
_PATH_TOON_RE = re.compile(
    r"(?i)(?:^|[/\\_-])toon-([1-8])(?:[/\\_-]|$)"
)
_HAS_TOON_RE = re.compile(r"(?m)^\s*@toon\b")
_HAS_TEMPO_RE = re.compile(r"(?m)^\s*@tempo\b")
_TITLE_LINE_RE = re.compile(
    r'(?m)^\s*@title(?::)?\s+"((?:\\.|[^"\\])*)"'
)

DEFAULT_TEMPO = 130


def _directive_name(line: str) -> str | None:
    m = _DIRECTIVE_RE.match(line.rstrip("\n"))
    if not m:
        return None
    return m.group(2).lower().rstrip(":")


def infer_toon(text: str, path: Path) -> str | None:
    """Bepaal toonnummer 1–8 uit @title of pad; anders None."""
    for m in _TITLE_LINE_RE.finditer(text):
        tm = _TITLE_TOON_RE.search(m.group(1))
        if tm:
            return tm.group(1)
    # Hele pad (posix) + stem: ``…/9a-toon-1/…/alleluia-9a-toon-1-….mvsa``
    hay = path.as_posix()
    pm = _PATH_TOON_RE.search(hay)
    if pm:
        return pm.group(1)
    pm = _PATH_TOON_RE.search(path.stem)
    if pm:
        return pm.group(1)
    return None


def _header_meta_end(lines: list[str]) -> int:
    """Index ná de laatste opeenvolgende header-meta-regel vanaf top.

    Slaat commentaar en lege regels over totdat de eerste inhoud komt.
    Binnen het meta-blok: ``@title`` e.d. (+ lege regels / ``#`` ertussen).
    """
    i = 0
    n = len(lines)
    seen_meta = False
    last_meta_idx = -1

    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            if seen_meta:
                # Lege regel / commentaar ná meta: nog toestaan tot non-meta.
                i += 1
                continue
            i += 1
            continue
        name = _directive_name(stripped)
        if name is None:
            break
        if name in _HEADER_META:
            seen_meta = True
            last_meta_idx = i
            i += 1
            continue
        # Andere @-directive (@do, @speelplan, …): einde van de kop-meta.
        break

    if last_meta_idx < 0:
        return -1
    return last_meta_idx + 1


def patch_mvsa(
    text: str,
    path: Path,
    *,
    add_tempo: bool,
) -> tuple[str | None, list[str]]:
    """Return (nieuwe tekst of None) en lijst van acties."""
    actions: list[str] = []
    need_toon = not _HAS_TOON_RE.search(text)
    need_tempo = add_tempo and not _HAS_TEMPO_RE.search(text)

    toon_val: str | None = None
    if need_toon:
        toon_val = infer_toon(text, path)
        if toon_val is None:
            need_toon = False

    if not need_toon and not need_tempo:
        return None, actions

    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    insert_at = _header_meta_end(lines)
    if insert_at < 0:
        # Geen meta-kop: vooraan na eventuele #-commentaren.
        insert_at = 0
        while insert_at < len(lines):
            s = lines[insert_at].strip()
            if not s or s.startswith("#"):
                insert_at += 1
                continue
            break

    block: list[str] = []
    if need_tempo:
        block.append(f"@tempo {DEFAULT_TEMPO}")
        actions.append(f"@tempo {DEFAULT_TEMPO}")
    if need_toon and toon_val is not None:
        block.append(f'@toon "{toon_val}"')
        actions.append(f'@toon "{toon_val}"')

    new_lines = lines[:insert_at] + block + lines[insert_at:]
    new_text = nl.join(new_lines)
    if text.endswith(("\n", "\r\n")):
        new_text += nl

    return new_text, actions


def iter_mvsa(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        root = root.resolve()
        if root.is_file() and root.suffix.lower() == ".mvsa":
            files.append(root)
            continue
        if not root.is_dir():
            print(f"Overgeslagen (geen map/bestand): {root}", file=sys.stderr)
            continue
        files.extend(sorted(root.rglob("*.mvsa")))
    # Uniek, stabiele volgorde
    seen: set[Path] = set()
    out: list[Path] = []
    for p in files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Voeg @toon (uit titel/pad) en optioneel @tempo 130 toe aan .mvsa."
        )
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=["."],
        help="Map(pen) of .mvsa-bestand(en); default: huidige map",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Schrijf wijzigingen (zonder deze flag: dry-run)",
    )
    parser.add_argument(
        "--tempo",
        action="store_true",
        help=f"Ook @tempo {DEFAULT_TEMPO} toevoegen als die ontbreekt",
    )
    args = parser.parse_args(argv)

    roots = [Path(r) for r in args.roots]
    files = iter_mvsa(roots)
    if not files:
        print("Geen .mvsa gevonden.", file=sys.stderr)
        return 1

    changed = 0
    skipped = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            print(f"FOUT lezen {path}: {exc}", file=sys.stderr)
            return 1

        new_text, actions = patch_mvsa(text, path, add_tempo=args.tempo)
        if new_text is None:
            skipped += 1
            continue

        rel = path
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            pass
        mode = "APPLY" if args.apply else "DRY"
        print(f"{mode} {rel}: {', '.join(actions)}")
        if args.apply:
            path.write_text(new_text, encoding="utf-8")
        changed += 1

    print(
        f"Klaar: {changed} te wijzigen, {skipped} ongewijzigd "
        f"({len(files)} .mvsa). "
        + ("Geschreven." if args.apply else "Dry-run - opnieuw met --apply.")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
