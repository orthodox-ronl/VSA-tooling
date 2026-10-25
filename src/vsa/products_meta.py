"""Sidecar ``*.products-meta.json`` for street ``products`` freshness.

Schema and semantics: docs/formats/contract-index.md ·
docs/plans/straat-clis.md. No content contract for .mxl/.mscz — only
source hash vs siblings.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = 1
META_SUFFIX = ".products-meta.json"

Freshness = Literal["ok", "missing", "stale", "no_meta"]


@dataclass(frozen=True)
class ProductSpec:
    """One product key → sibling path (absolute or relative to bron parent)."""

    key: str
    path: Path


def meta_path_for(bron: Path) -> Path:
    """``lied.mvsa`` → ``lied.mvsa.products-meta.json``."""
    return bron.with_name(f"{bron.name}{META_SUFFIX}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_meta(
    bron: Path,
    products: dict[str, Path],
    *,
    bron_sha256: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build meta dict; product values are **file names** (siblings)."""
    return {
        "schema": SCHEMA_VERSION,
        "bron": bron.name,
        "bron_sha256": bron_sha256 or sha256_file(bron),
        "generated_at": generated_at or utc_now_iso(),
        "products": {k: p.name for k, p in sorted(products.items())},
    }


def write_meta(bron: Path, products: dict[str, Path]) -> Path:
    dest = meta_path_for(bron)
    payload = build_meta(bron, products)
    dest.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return dest


def load_meta(bron: Path) -> dict[str, Any] | None:
    path = meta_path_for(bron)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def resolve_product_path(bron: Path, name: str) -> Path:
    return bron.parent / name


def freshness(
    bron: Path,
    *,
    required_keys: set[str] | None = None,
) -> tuple[Freshness, str]:
    """Fast check: meta + bron hash + listed product files exist.

    If *required_keys* is set, only those product keys are required to exist.
    Otherwise every key in meta ``products`` must exist on disk.
    """
    if not bron.is_file():
        return "missing", f"bron ontbreekt: {bron}"
    meta = load_meta(bron)
    if meta is None:
        return "no_meta", f"geen {meta_path_for(bron).name}"
    stored = meta.get("bron_sha256")
    if not isinstance(stored, str) or not stored:
        return "stale", "meta zonder bron_sha256"
    actual = sha256_file(bron)
    if stored != actual:
        return "stale", "bron_sha256 wijkt af van huidige bron"
    products = meta.get("products")
    if not isinstance(products, dict) or not products:
        return "stale", "meta zonder products"
    keys = required_keys if required_keys is not None else set(products)
    for key in keys:
        name = products.get(key)
        if not isinstance(name, str) or not name:
            return "missing", f"product '{key}' ontbreekt in meta"
        path = resolve_product_path(bron, name)
        if not path.is_file():
            return "missing", f"productbestand ontbreekt: {path.name}"
    return "ok", "meta en producten in orde"
