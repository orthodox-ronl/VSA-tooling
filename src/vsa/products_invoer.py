"""Vingerafdruk van de invoer van een product (migratie stap 6).

Eén vingerafdruk per bron: wat bepaalt of afgeleide producten nog kloppen.
Opgebouwd uit vier delen, elk apart bewaard zodat ``freshness`` kan zeggen
*wat* veranderde:

* ``bron``: SHA-256 van de bronbytes;
* ``woorden``: de woorden die de bron zingt, met hun vorm in de woordenlijst
  (verandert een ander woord in de lijst, dan blijft deze waarde gelijk);
* ``template``: inhoud van het template van een ``.vsa`` (leeg bij andere bronnen);
* ``recept``: getal per bronsoort, met de hand opgehoogd als de export
  bewust anders uitpakt (:data:`RECEPT_VERSIE`).

De tooling-commit telt niet mee. Norm: ``docs/formats/products-meta.md``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

#: Ophogen in dezelfde PR die de uitkomst van een export bewust wijzigt.
RECEPT_VERSIE: dict[str, int] = {"vsa": 1, "mvsa": 1, "mscz": 1}

_ONBEKEND = "onbekend"
_FOUT = "fout"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return _sha256_bytes(text.encode("utf-8"))


def _soort(bron: Path) -> str:
    return bron.suffix.lower().lstrip(".")


def _woordkernen(bron: Path, text: str) -> list[tuple[str, str | None]]:
    """``(woordkern, taalcode)`` van de gezongen woorden; leeg voor andere bronnen."""
    from .syllable_dict_check import (
        iter_mvsa_lyric_word_cores_tagged,
        iter_vsa_lyric_word_cores_tagged,
    )

    soort = _soort(bron)
    if soort == "vsa":
        from .vsa_stanzas import parse_vsa_source

        _meta, document = parse_vsa_source(text)
        return iter_vsa_lyric_word_cores_tagged(document)
    if soort == "mvsa":
        return iter_mvsa_lyric_word_cores_tagged(text)
    return []


def woorden_component(bron: Path, text: str) -> str:
    """Hash over de woorden van de bron en hun toegestane vormen in de lijst.

    Woorden in een taal zonder lijst (``@taal ro``) tellen niet mee: ze worden
    niet gecontroleerd en dus ook niet door de lijst bepaald.
    """
    from .syllable_dictionary import (
        LYRICS_LANGS,
        allowed_syllable_forms,
        lyrics_lang_for_core,
        lyrics_lang_scope,
        syllable_lemma,
    )

    per_taal: dict[str, set[str]] = {}
    for core, tag in _woordkernen(bron, text):
        taal = tag if tag is not None else lyrics_lang_for_core(core)
        if taal in LYRICS_LANGS and syllable_lemma(core):
            per_taal.setdefault(taal, set()).add(core)
    if not per_taal:
        return ""
    regels: list[list[Any]] = []
    for taal in sorted(per_taal):
        with lyrics_lang_scope(taal):
            gezien: dict[str, list[str] | None] = {}
            for core in per_taal[taal]:
                vormen = allowed_syllable_forms(core)
                gezien[syllable_lemma(core)] = sorted(vormen) if vormen else None
        regels.extend([taal, lemma, gezien[lemma]] for lemma in sorted(gezien))
    return _sha256_json(regels)


def template_component(bron: Path, text: str) -> str:
    """Hash van het template-bestand dat bij een ``.vsa`` hoort; anders leeg."""
    if _soort(bron) != "vsa":
        return ""
    from .template_library import (
        TemplateLibraryError,
        load_resolved_template,
        select_template_id,
    )
    from .yaml_frontmatter import parse_vsa_frontmatter

    meta, _body = parse_vsa_frontmatter(text)
    try:
        naam = meta.get("template")
        if not isinstance(naam, str) or not naam.strip():
            naam = select_template_id(
                soort=meta.get("soort"),
                toon=meta.get("toon"),
                formule=meta.get("formule"),
                bron=meta.get("bron"),
                path=bron,
            )
        gevonden = load_resolved_template(naam)
    except (TemplateLibraryError, ValueError, OSError):
        return _ONBEKEND
    paden = sorted({gevonden.path, gevonden.formula_path})
    return _sha256_json([_sha256_bytes(p.read_bytes()) for p in paden])


def _veilig(functie: Any, bron: Path, text: str) -> str:
    """Een kapotte bron mag het schrijven van meta niet stoppen: vaste waarde."""
    try:
        return functie(bron, text)
    except Exception as exc:  # noqa: BLE001 - zelfde fout geeft dezelfde waarde
        return f"{_FOUT}:{type(exc).__name__}"


def bereken_invoer(bron: Path) -> dict[str, Any]:
    """De vingerafdruk van ``bron``: onderdelen plus gecombineerde ``sha256``."""
    data = bron.read_bytes()
    text = data.decode("utf-8", errors="replace")
    delen: dict[str, Any] = {
        "bron": _sha256_bytes(data),
        "woorden": _veilig(woorden_component, bron, text),
        "template": _veilig(template_component, bron, text),
        "recept": RECEPT_VERSIE.get(_soort(bron), 0),
    }
    return {**delen, "sha256": _sha256_json(delen)}


def verschillen(opgeslagen: Any, nu: dict[str, Any]) -> list[str]:
    """Leesbare redenen waarom de opgeslagen vingerafdruk niet meer klopt."""
    if not isinstance(opgeslagen, dict) or not opgeslagen.get("sha256"):
        return ["geen invoer-vingerafdruk in meta"]
    if opgeslagen.get("sha256") == nu["sha256"]:
        return []
    redenen: list[str] = []
    if opgeslagen.get("bron") != nu["bron"]:
        redenen.append("bron veranderd")
    if opgeslagen.get("woorden") != nu["woorden"]:
        redenen.append("woordenlijst: een gebruikt woord is veranderd")
    if opgeslagen.get("template") != nu["template"]:
        redenen.append("template veranderd")
    if opgeslagen.get("recept") != nu["recept"]:
        redenen.append(f"recept {opgeslagen.get('recept')} -> {nu['recept']}")
    return redenen or ["invoer-vingerafdruk wijkt af"]
