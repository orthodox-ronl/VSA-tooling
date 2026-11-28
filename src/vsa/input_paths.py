"""Bestand-of-map-invoer voor CLI-commando's (G2).

**Afspraak** (``docs/reference/cli/input-pad.md``): een ``path``-argument is:

1. **bestaand** bestand of map (recursief passende extensies), of
2. **korte lookup** onder ``content-source`` / ``catalogus`` / ``koormappen``, of
3. **catalogus-id** (slash-pad, soort-/tussenmap, stam, ``stam.ext``).

**Batch (map):** sla geneste afgeleiden over — bestanden waarvan de stam al
een brontype-extensie heeft (``lied.mvsa.mscz`` bij zoeken op ``.mscz``).
Eén expliciet bestandspad blijft toegestaan.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

# Extensies die als brontype in ``stem.brontype.doeltype`` voorkomen.
# Een batch mag geen product-van-product oppikken (``*.mvsa.mscz`` → svg).
BRONTYPE_SUFFIXES = frozenset(
    {
        ".mvsa",
        ".vsa",
        ".mscz",
        ".mxl",
        ".musicxml",
        ".xml",
    }
)

_ID_PART = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)
_CATALOGUS_ID = re.compile(
    r"^[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)*$",
    re.IGNORECASE,
)
# Foutlocatie uit CLI: ``…/lied.vsa:29:28`` of ``…/lied.vsa:29:28:``.
_LOC_SUFFIX_RE = re.compile(
    r"^(?P<path>.+\.[A-Za-z0-9_+-]+)(?::\d+){1,2}:?$"
)


class InputPathError(ValueError):
    """Pad ontbreekt, is geen bestand/map, of past niet bij de extensies."""


def normalize_suffixes(suffixes: Sequence[str]) -> frozenset[str]:
    """Normaliseer tot lowercase extensies met leidende punt (``.mvsa``)."""
    out: set[str] = set()
    for raw in suffixes:
        s = str(raw).strip().lower()
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        out.add(s)
    if not out:
        raise InputPathError("minstens één bestands-extensie vereist")
    return frozenset(out)


def is_nested_derived_source(path: Path | str) -> bool:
    """True als ``path`` een afgeleide is van een ander brontype.

    Voorbeeld: ``lied.mvsa.mscz`` (stam eindigt op ``.mvsa``) — product van
    ``lied.mvsa``, geen losse ``.mscz``-bron voor batch-``products``.
    """
    stem = Path(path).stem.lower()
    return any(stem.endswith(bron) for bron in BRONTYPE_SUFFIXES)


def strip_cli_location_suffix(raw: Path | str) -> str:
    """Haal ``:regel`` / ``:regel:kolom`` weg (plakken vanuit foutmeldingen).

    Quotes rondom het pad worden ook gestript. Geen wijziging als het geen
    locatie-suffix is (gewone paden blijven intact).
    """
    text = str(raw).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    match = _LOC_SUFFIX_RE.match(text.replace("\\", "/"))
    if not match:
        return text
    return match.group("path")


def catalogus_id_from_path(path: Path | str | None) -> str | None:
    """``soort/variant/uitvoeringsvorm`` uit ``…/catalogus/…``, of ``None``."""
    if path is None:
        return None
    parts = Path(path).resolve().parts
    for i, part in enumerate(parts):
        if part != "catalogus":
            continue
        if i + 3 >= len(parts):
            return None
        segs = parts[i + 1 : i + 4]
        if all(_ID_PART.fullmatch(s) for s in segs):
            return "/".join(segs)
        return None
    return None


def source_id_for_prompt(path: Path | str | None) -> str:
    """Label voor TTY-prompts: catalogus-id, anders bestandsstam."""
    if path is None:
        return ""
    hit = catalogus_id_from_path(path)
    if hit:
        return hit
    p = Path(path)
    return p.stem if p.suffix else p.name


def looks_like_catalogus_id(raw: str | Path) -> bool:
    """True als ``raw`` een catalogus-id kan zijn (geen bestaand pad-check).

    Accepteert slash-vorm en stamvorm **zonder** extensie. Voor
    ``stam.vsa`` / ``stam.mvsa``: zie :func:`catalogus_id_from_cli_token`.
    """
    s = str(raw).strip().replace("\\", "/")
    if not s or ":" in s:
        return False
    if s.startswith(".") or s.startswith("/"):
        return False
    if Path(s).suffix:
        return False
    return bool(_CATALOGUS_ID.fullmatch(s))


def catalogus_id_from_cli_token(
    raw: str | Path,
    *,
    suffixes: Sequence[str] | None = None,
) -> str | None:
    """Catalogus-id uit een CLI-token, of ``None``.

    - ``soort/variant/uv`` of ``soort-variant-uv`` of soort-map ``alleluia``
    - optioneel ``soort-variant-uv.vsa`` (kale bestandsnaam + extensie)
    """
    s = str(raw).strip().replace("\\", "/")
    if not s or ":" in s:
        return None
    if s.startswith(".") or s.startswith("/"):
        return None
    p = Path(s)
    if p.suffix:
        if "/" in s:
            return None
        if suffixes is not None:
            allowed = normalize_suffixes(suffixes)
            if p.suffix.lower() not in allowed:
                return None
        stem = p.stem
        if is_nested_derived_source(p.name):
            return None
        if _CATALOGUS_ID.fullmatch(stem):
            return stem
        return None
    if _CATALOGUS_ID.fullmatch(s):
        return s
    return None


def discover_repo_root(
    *,
    explicit: Path | str | None = None,
) -> Path | None:
    """Repository-root met ``content-source`` (cwd, of sibling bibliotheek)."""
    if explicit is not None:
        root = Path(explicit)
        try:
            return root.resolve()
        except OSError:
            return root

    cwd = Path.cwd()
    if (cwd / "content-source").is_dir():
        try:
            return cwd.resolve()
        except OSError:
            return cwd

    tooling = Path(__file__).resolve().parents[2]
    for cand in (
        tooling.parent / "bibliotheek",
        tooling / ".." / "bibliotheek",
    ):
        if (cand / "content-source").is_dir():
            try:
                return cand.resolve()
            except OSError:
                return cand
    return None


def discover_catalogus_roots(
    *,
    extra: Sequence[Path | str] | None = None,
) -> list[Path]:
    """Zoek ``content-source/catalogus`` (cwd, sibling bibliotheek, env)."""
    found: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        try:
            resolved = p.resolve()
        except OSError:
            return
        if resolved in seen or not resolved.is_dir():
            return
        seen.add(resolved)
        found.append(resolved)

    for item in extra or ():
        _add(Path(item))

    env = (os.environ.get("VSA_CATALOGUS") or "").strip()
    if env:
        _add(Path(env))

    tooling = Path(__file__).resolve().parents[2]
    cwd = Path.cwd()
    bases = [
        cwd,
        cwd / "content-source" / "catalogus",
        tooling.parent / "bibliotheek",
        tooling / ".." / "bibliotheek",
    ]
    for base in bases:
        b = Path(base)
        if b.name == "catalogus" and (b.parent.name == "content-source"):
            _add(b)
            continue
        _add(b / "content-source" / "catalogus")
        if b.name == "content-source":
            _add(b / "catalogus")
    return found


def resolve_cli_path(
    raw: Path | str,
    *,
    repo_root: Path | str | None = None,
) -> Path:
    """Bestaand bestand of map zoeken (G2 stappen 1–2).

    Volgorde (eerste bestaande kandidaat wint):

    1. pad zoals opgegeven (absoluut, of relatief t.o.v. cwd; bij relatief
       ook ``repo_root / pad``);
    2. ``content-source/<pad>``;
    3. ``content-source/catalogus/<pad>``;
    4. ``content-source/koormappen/<pad>``.

    ``repo_root`` default: :func:`discover_repo_root`. Locatie-suffix
    ``:regel:kolom`` wordt genegeerd.

    Raises
    ------
    InputPathError
        Geen kandidaat bestaat.
    """
    cleaned = strip_cli_location_suffix(raw)
    raw_path = Path(cleaned)
    root = discover_repo_root(explicit=repo_root)

    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [raw_path]
        if root is not None:
            content = root / "content-source"
            candidates.extend(
                [
                    root / raw_path,
                    content / raw_path,
                    content / "catalogus" / raw_path,
                    content / "koormappen" / raw_path,
                ]
            )

    seen: set[str] = set()
    for cand in candidates:
        try:
            key = str(cand.resolve())
        except OSError:
            key = str(cand)
        if key in seen:
            continue
        seen.add(key)
        if cand.exists():
            try:
                return cand.resolve()
            except OSError:
                return cand

    raise InputPathError(f"Pad niet gevonden: {raw_path}")


def resolve_catalogus_id(
    catalogus_id: str,
    *,
    suffixes: Sequence[str],
    roots: Sequence[Path | str] | None = None,
    recursive: bool = True,
) -> list[Path]:
    """Zoek bestanden voor een catalogus-id onder de catalogus-roots.

    - Slash-id (``tropaar/…/hemelum``): map ``catalogus/<id>/``.
    - Token zonder ``/``: eerst **soort-/tussenmap** ``catalogus/<token>/``
      als die bestaat; anders bestanden met die exacte stem.
    """
    allowed = normalize_suffixes(suffixes)
    cid = str(catalogus_id).strip().replace("\\", "/")
    if not looks_like_catalogus_id(cid):
        raise InputPathError(f"Geen geldige catalogus-id: {catalogus_id!r}")

    search_roots = (
        [Path(r) for r in roots]
        if roots is not None
        else discover_catalogus_roots()
    )
    if not search_roots:
        raise InputPathError(
            "Geen catalogus-root gevonden "
            "(verwacht content-source/catalogus of VSA_CATALOGUS)."
        )

    hits: list[Path] = []
    if "/" in cid:
        for root in search_roots:
            leaf = root.joinpath(*cid.split("/"))
            if leaf.is_dir():
                hits.extend(
                    collect_input_files(
                        leaf,
                        suffixes=sorted(allowed),
                        recursive=recursive,
                        resolve_ids=False,
                    )
                )
            elif leaf.is_file() and leaf.suffix.lower() in allowed:
                hits.append(leaf)
    else:
        # Soort-/tussenmap vóór stam-zoek (``alleluia``, ``communievers``).
        dir_hits: list[Path] = []
        for root in search_roots:
            folder = root / cid
            if folder.is_dir():
                dir_hits.extend(
                    collect_input_files(
                        folder,
                        suffixes=sorted(allowed),
                        recursive=recursive,
                        resolve_ids=False,
                    )
                )
        if dir_hits:
            hits.extend(dir_hits)
        else:
            stem = cid.lower()
            for root in search_roots:
                for path in root.rglob("*"):
                    if not path.is_file():
                        continue
                    if path.suffix.lower() not in allowed:
                        continue
                    if is_nested_derived_source(path):
                        continue
                    if path.stem.lower() == stem:
                        hits.append(path)

    uniq: list[Path] = []
    seen: set[Path] = set()
    for h in sorted(hits):
        try:
            key = h.resolve()
        except OSError:
            key = h
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    if not uniq:
        raise InputPathError(
            f"Catalogus-id {cid!r} niet gevonden onder "
            + ", ".join(str(r) for r in search_roots)
        )
    return uniq


def collect_input_files(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
    resolve_ids: bool = True,
    catalogus_roots: Sequence[Path | str] | None = None,
    repo_root: Path | str | None = None,
) -> list[Path]:
    """Verzamel bronbestanden: één file, map, korte lookup, of catalogus-id.

    Parameters
    ----------
    path:
        Bestaand bestand/map, korte lookup, of catalogus-id.
    suffixes:
        Toegestane extensies (``.mvsa``, ``mvsa``, …). Case-insensitive.
    recursive:
        Bij een map: ``rglob`` (True) of alleen directe kinderen (False).
    resolve_ids:
        Zoek korte lookup + catalogus-id als het pad niet bestaat.
    catalogus_roots:
        Optionele roots i.p.v. :func:`discover_catalogus_roots`.
    repo_root:
        Optionele repo-root voor korte lookup (:func:`resolve_cli_path`).

    Returns
    -------
    list[Path]
        Gesorteerde lijst van bestaande bestanden. Mag leeg zijn als de map
        geen matches heeft. Bij een **map** worden geneste afgeleiden
        weggelaten. Bij één **bestand** blijft het pad staan, ook als het
        genest is.

    Raises
    ------
    InputPathError
        Pad bestaat niet (en is geen id); is geen file/dir; of is een file
        met verkeerde extensie.
    """
    cleaned = strip_cli_location_suffix(path)
    p = Path(cleaned)
    allowed = normalize_suffixes(suffixes)

    if not p.exists() and resolve_ids:
        # Korte lookup: altijd bij expliciete repo_root; auto-discover
        # (sibling bibliotheek) alleen als catalogus_roots niet is vastgezet
        # (tests/fixtures zetten roots vaak zonder echte repo).
        try_short = repo_root is not None or catalogus_roots is None
        if try_short:
            try:
                p = resolve_cli_path(cleaned, repo_root=repo_root)
            except InputPathError:
                pass

    if p.exists():
        if p.is_file():
            if p.suffix.lower() not in allowed:
                want = ", ".join(sorted(allowed))
                raise InputPathError(
                    f"Verwacht bestand met extensie {want}; kreeg: {p.name}"
                )
            return [p]
        if p.is_dir():
            if recursive:
                candidates: Iterable[Path] = p.rglob("*")
            else:
                candidates = p.iterdir()
            return sorted(
                c
                for c in candidates
                if c.is_file()
                and c.suffix.lower() in allowed
                and not is_nested_derived_source(c)
            )
        raise InputPathError("Geen bestand of map.")

    if resolve_ids:
        cid = catalogus_id_from_cli_token(cleaned, suffixes=sorted(allowed))
        if cid is not None:
            return resolve_catalogus_id(
                cid,
                suffixes=sorted(allowed),
                roots=catalogus_roots,
                recursive=recursive,
            )

    raise InputPathError("Pad niet gevonden.")


def collect_cli_sources(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
    resolve_ids: bool = True,
    catalogus_roots: Sequence[Path | str] | None = None,
    repo_root: Path | str | None = None,
) -> list[Path]:
    """Zoals :func:`collect_input_files`, maar lege map → :exc:`InputPathError`."""
    files = collect_input_files(
        path,
        suffixes=suffixes,
        recursive=recursive,
        resolve_ids=resolve_ids,
        catalogus_roots=catalogus_roots,
        repo_root=repo_root,
    )
    if not files:
        raise InputPathError("Geen passende bestanden gevonden.")
    return files


def reject_multi_with_output(
    files: Sequence[Path],
    output: Path | str | None,
    *,
    flag: str = "-o/--output",
) -> None:
    """Weiger enkelvoudig uitvoerpad bij meer dan één bronbestand."""
    if output is not None and len(files) > 1:
        raise InputPathError(
            f"{flag} is alleen toegestaan bij precies één bronbestand "
            f"(nu {len(files)} bestanden)"
        )
