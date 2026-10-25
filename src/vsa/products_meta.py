"""Sidecar ``*.products-meta.json`` for street ``products`` freshness.

Normative hub: ``docs/formats/products-meta.md`` (schema 2).
No M*/S* content contract — only provenance/freshness.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = 2
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


def product_file_name(entry: Any) -> str | None:
    """Schema 2 ``{file, sha256}`` of legacy schema-1 bestandsnaam."""
    if isinstance(entry, str) and entry:
        return entry
    if isinstance(entry, dict):
        name = entry.get("file")
        if isinstance(name, str) and name:
            return name
    return None


def product_sha256(entry: Any) -> str | None:
    """Product-inhouds-hash uit schema-2-entry; anders ``None``."""
    if isinstance(entry, dict):
        sha = entry.get("sha256")
        if isinstance(sha, str) and sha:
            return sha
    return None


def build_product_entry(
    path: Path,
    *,
    generated_at: str | None = None,
) -> dict[str, str]:
    """Schema-2 productentry: ``file`` + ``sha256`` + ``generated_at``."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"productbestand ontbreekt voor meta: {path}")
    return {
        "file": path.name,
        "sha256": sha256_file(path),
        "generated_at": generated_at or utc_now_iso(),
    }


def build_meta(
    bron: Path,
    products: dict[str, Path],
    *,
    bron_sha256: str | None = None,
    generated_at: str | None = None,
    product_generated_at: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build schema-2 meta; each product has ``file`` + ``sha256`` + ``generated_at``."""
    stamp = generated_at or utc_now_iso()
    product_entries: dict[str, dict[str, str]] = {}
    for key, path in sorted(products.items()):
        per_key = None
        if product_generated_at is not None:
            per_key = product_generated_at.get(key)
        product_entries[key] = build_product_entry(
            path, generated_at=per_key or stamp
        )
    return {
        "schema": SCHEMA_VERSION,
        "bron": bron.name,
        "bron_sha256": bron_sha256 or sha256_file(bron),
        "generated_at": stamp,
        "products": product_entries,
    }


def _bron_sha256_matches(meta: dict[str, Any], bron_sha: str) -> bool:
    stored = meta.get("bron_sha256")
    return isinstance(stored, str) and stored == bron_sha


def write_meta(
    bron: Path,
    products: dict[str, Path],
    *,
    merge: bool = False,
    drop_keys: set[str] | None = None,
    generated_at: str | None = None,
    product_generated_at: dict[str, str] | None = None,
) -> Path:
    """Write schema-2 sidecar.

    ``merge=False`` (default, ``{straat} products``): replace ``products``
    with exactly the keys in *products*.

    ``merge=True`` (individuele product-subs): keep other product keys when
    existing meta is schema 2 and ``bron_sha256`` still matches; otherwise
    write only the keys from this run (no silent mix of old/new bron).

    *drop_keys*: after merge (or on the new set), remove these product keys
    (bijv. dode ``svg`` na bladreeks ``svg-1``…).
    """
    dest = meta_path_for(bron)
    stamp = generated_at or utc_now_iso()
    bron_sha = sha256_file(bron)
    payload = build_meta(
        bron,
        products,
        bron_sha256=bron_sha,
        generated_at=stamp,
        product_generated_at=product_generated_at,
    )

    if merge:
        existing = load_meta(bron)
        if (
            existing is not None
            and existing.get("schema") == SCHEMA_VERSION
            and _bron_sha256_matches(existing, bron_sha)
        ):
            kept = existing.get("products")
            if isinstance(kept, dict) and kept:
                merged = dict(kept)
                merged.update(payload["products"])
                payload["products"] = dict(sorted(merged.items()))

    if drop_keys:
        for key in drop_keys:
            payload["products"].pop(key, None)

    if not payload["products"]:
        raise ValueError("products-meta: geen product-keys over na schrijven")

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
    """Fast check: schema 2 + bron-hash + product files + product-hashes.

    If *required_keys* is set, only those product keys are required.
    Otherwise every key in meta ``products`` must exist and match.
    """
    if not bron.is_file():
        return "missing", f"bron ontbreekt: {bron}"
    meta = load_meta(bron)
    if meta is None:
        return "no_meta", f"geen {meta_path_for(bron).name}"
    schema = meta.get("schema")
    if schema != SCHEMA_VERSION:
        return "stale", f"meta schema {schema!r} (verwacht {SCHEMA_VERSION})"
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
        entry = products.get(key)
        name = product_file_name(entry)
        if not name:
            return "missing", f"product '{key}' ontbreekt in meta"
        path = resolve_product_path(bron, name)
        if not path.is_file():
            return "missing", f"productbestand ontbreekt: {path.name}"
        expected = product_sha256(entry)
        if not expected:
            return "stale", f"product '{key}' zonder sha256"
        if sha256_file(path) != expected:
            return "stale", f"product '{key}' sha256 wijkt af van bestand"
    return "ok", "meta en producten in orde"
