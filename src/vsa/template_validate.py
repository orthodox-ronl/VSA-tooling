"""Structurele + documentregels-toets voor vsa-templates (draft-v0)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .pitch_resolver import ALLOWED_MODES
from .template_instance import CANON_ANCHORS, normalize_anchor

DO_RE = re.compile(r"^[A-G](#|b)?[0-9]$")
DEGREE_RE = re.compile(r"^(#|b)?(do|re|mi|fa|sol|la|ti)([+-][1-3])?$")
ID_RE = re.compile(r"^[a-z0-9_-]+$")
VOICES = ("S", "A", "T", "B")
ROLES = frozenset({"open", "recite", "cadence", "link"})
DURATIONS = frozenset({"~", "-", "-.", "~.", "_", "_.", "__", ".", ".."})
ANCHORS = frozenset(CANON_ANCHORS)
GENRES = frozenset({"tropaar", "kondak", "stichier", "vers", "other"})


class TemplateValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def load_template(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def collect_template_ids(root: Path) -> set[str]:
    """Alle `id:`-waarden uit `template.yaml` onder ``root``."""
    ids: set[str] = set()
    if root.is_file():
        root = root.parent
    for path in root.rglob("template.yaml"):
        doc = load_template(path)
        if isinstance(doc, dict) and isinstance(doc.get("id"), str):
            ids.add(doc["id"])
    return ids


def validate_template(doc: Any, *, known_ids: set[str] | None = None) -> None:
    if not isinstance(doc, dict):
        raise TemplateValidationError("TEMPLATE-ROOT", "root must be a mapping")

    _require(doc, "spec_version", str)
    if doc["spec_version"] != "draft-v0":
        raise TemplateValidationError(
            "TEMPLATE-SPEC-VERSION",
            "spec_version must be draft-v0",
        )

    _require(doc, "id", str)
    if not ID_RE.match(doc["id"]):
        raise TemplateValidationError("TEMPLATE-ID", "id must match [a-z0-9_-]+")

    _require(doc, "genre", str)
    if doc["genre"] not in GENRES:
        raise TemplateValidationError("TEMPLATE-GENRE", f"invalid genre {doc['genre']!r}")

    _require(doc, "tone", int)
    if not 1 <= doc["tone"] <= 8:
        raise TemplateValidationError("TEMPLATE-TONE", "tone must be 1..8")

    do = _require(doc, "do", str)
    if not DO_RE.match(do):
        raise TemplateValidationError("TEMPLATE-DO", f"invalid do pitch {do!r}")

    mode = _require(doc, "mode", str)
    if mode not in ALLOWED_MODES:
        raise TemplateValidationError(
            "TEMPLATE-MODE",
            f"mode must be one of {sorted(ALLOWED_MODES)}; got {mode!r}",
        )

    if "duration-model" in doc:
        dm = doc["duration-model"]
        if not isinstance(dm, str) or not dm.strip():
            raise TemplateValidationError(
                "TEMPLATE-DURATION-MODEL",
                "duration-model must be non-empty string",
            )

    if "pitches_status" in doc:
        if doc["pitches_status"] not in ("verified", "provisional"):
            raise TemplateValidationError(
                "TEMPLATE-PITCHES-STATUS",
                "pitches_status must be verified or provisional",
            )

    if "source" in doc and (
        not isinstance(doc["source"], str) or not doc["source"].strip()
    ):
        raise TemplateValidationError("TEMPLATE-SOURCE", "source must be non-empty string")

    if "key_signature" in doc:
        key = doc["key_signature"]
        if not isinstance(key, dict):
            raise TemplateValidationError("TEMPLATE-KEY", "key_signature must be a mapping")
        has_flats = "flats" in key
        has_sharps = "sharps" in key
        if has_flats == has_sharps:
            raise TemplateValidationError(
                "TEMPLATE-KEY",
                "key_signature needs exactly one of flats or sharps",
            )

    if "also_used_as" in doc:
        als = doc["also_used_as"]
        if not isinstance(als, list) or not als:
            raise TemplateValidationError(
                "TEMPLATE-ALSO-USED-AS",
                "also_used_as must be a non-empty list",
            )
        for g in als:
            if g not in GENRES:
                raise TemplateValidationError(
                    "TEMPLATE-ALSO-USED-AS",
                    f"invalid genre in also_used_as: {g!r}",
                )

    has_same = "same_as" in doc
    has_cycle = "cycle" in doc
    has_final = "final" in doc
    has_seq = "sequence" in doc
    has_phrases = "phrases" in doc

    if has_same:
        same = doc["same_as"]
        if not isinstance(same, str) or not ID_RE.match(same):
            raise TemplateValidationError(
                "TEMPLATE-SAME-AS",
                "same_as must match [a-z0-9_-]+",
            )
        if same == doc["id"]:
            raise TemplateValidationError(
                "TEMPLATE-SAME-AS",
                "same_as must not refer to self",
            )
        if has_cycle or has_final or has_seq or has_phrases:
            raise TemplateValidationError(
                "TEMPLATE-FORM",
                "alias-form (same_as) must not include cycle/final/sequence/phrases",
            )
        if known_ids is not None and same not in known_ids:
            raise TemplateValidationError(
                "TEMPLATE-SAME-AS-REF",
                f"same_as {same!r} not found among templates",
            )
    elif has_seq:
        if has_cycle or has_final:
            raise TemplateValidationError(
                "TEMPLATE-FORM",
                "sequence-form must not include cycle/final",
            )
        if not has_phrases:
            raise TemplateValidationError("TEMPLATE-REQUIRED", "missing phrases")
        sequence = _require(doc, "sequence", list)
        if not sequence:
            raise TemplateValidationError(
                "TEMPLATE-SEQUENCE-NONEMPTY",
                "sequence must be non-empty",
            )
        for item in sequence:
            if not isinstance(item, str) or not item:
                raise TemplateValidationError(
                    "TEMPLATE-SEQUENCE-REF",
                    "sequence items must be non-empty strings",
                )
        id_set = _validate_phrases(doc["phrases"])
        for sid in sequence:
            if sid not in id_set:
                raise TemplateValidationError(
                    "TEMPLATE-SEQUENCE-REF",
                    f"sequence id {sid!r} not in phrases",
                )
        _validate_mapping_extensions(doc, id_set)
    elif has_cycle or has_final:
        if has_seq:
            raise TemplateValidationError(
                "TEMPLATE-FORM",
                "cycle-form must not include sequence",
            )
        if not has_phrases:
            raise TemplateValidationError("TEMPLATE-REQUIRED", "missing phrases")
        cycle = _require(doc, "cycle", list)
        if not cycle:
            raise TemplateValidationError(
                "TEMPLATE-CYCLE-NONEMPTY",
                "cycle must be non-empty",
            )
        for item in cycle:
            if not isinstance(item, str) or not item:
                raise TemplateValidationError(
                    "TEMPLATE-CYCLE-REF",
                    "cycle items must be non-empty strings",
                )
        final = _require(doc, "final", str)
        if not final:
            raise TemplateValidationError("TEMPLATE-FINAL-REF", "final must be non-empty")
        id_set = _validate_phrases(doc["phrases"])
        for cid in cycle:
            if cid not in id_set:
                raise TemplateValidationError(
                    "TEMPLATE-CYCLE-REF",
                    f"cycle id {cid!r} not in phrases",
                )
        if final not in id_set:
            raise TemplateValidationError(
                "TEMPLATE-FINAL-REF",
                f"final {final!r} not in phrases",
            )
        if final in cycle:
            raise TemplateValidationError(
                "TEMPLATE-FINAL-NOT-IN-CYCLE",
                f"final {final!r} must not appear in cycle",
            )
        _validate_mapping_extensions(doc, id_set)
    else:
        raise TemplateValidationError(
            "TEMPLATE-FORM",
            "need cycle+final, sequence, or same_as",
        )

    allowed = {
        "spec_version",
        "id",
        "genre",
        "tone",
        "do",
        "mode",
        "duration-model",
        "key_signature",
        "pitches_status",
        "source",
        "same_as",
        "also_used_as",
        "cycle",
        "final",
        "sequence",
        "text_mapping",
        "mapping_plans",
        "default_mapping_plan",
        "phrases",
        "voice_oct",
    }
    extra = set(doc) - allowed
    if extra:
        raise TemplateValidationError(
            "TEMPLATE-UNKNOWN-FIELD",
            f"unknown top-level fields: {sorted(extra)}",
        )


def _validate_phrases(phrases: Any) -> set[str]:
    if not isinstance(phrases, list) or not phrases:
        raise TemplateValidationError("TEMPLATE-PHRASE-EVENTS", "phrases must be non-empty")
    phrase_ids: list[str] = []
    for phrase in phrases:
        if not isinstance(phrase, dict):
            raise TemplateValidationError("TEMPLATE-PHRASE", "phrase must be a mapping")
        pid = _require(phrase, "id", str)
        if pid in phrase_ids:
            raise TemplateValidationError(
                "TEMPLATE-PHRASE-ID-UNIQUE",
                f"duplicate phrase id {pid!r}",
            )
        phrase_ids.append(pid)
        events = _require(phrase, "events", list)
        if not events:
            raise TemplateValidationError(
                "TEMPLATE-PHRASE-EVENTS",
                f"phrase {pid!r} needs ≥1 event",
            )
        for item in events:
            _validate_event_item(item)
    return set(phrase_ids)


def _validate_mapping_extensions(doc: dict, id_set: set[str]) -> None:
    if "text_mapping" not in doc and "mapping_plans" not in doc:
        return
    from .template_mapping import TemplateMappingError, list_mapping_plans

    try:
        list_mapping_plans(doc)
    except TemplateMappingError as exc:
        raise TemplateValidationError("TEMPLATE-MAPPING", str(exc)) from exc
    if "mapping_plans" in doc:
        plans = doc["mapping_plans"]
        if not isinstance(plans, list) or not plans:
            raise TemplateValidationError(
                "TEMPLATE-MAPPING",
                "mapping_plans must be a non-empty list",
            )
        seen: set[str] = set()
        for raw in plans:
            if not isinstance(raw, dict):
                raise TemplateValidationError(
                    "TEMPLATE-MAPPING",
                    "mapping_plans items must be mappings",
                )
            pid = raw.get("id")
            if not isinstance(pid, str) or not pid:
                raise TemplateValidationError(
                    "TEMPLATE-MAPPING",
                    "mapping_plans item needs non-empty id",
                )
            if pid in seen:
                raise TemplateValidationError(
                    "TEMPLATE-MAPPING",
                    f"duplicate mapping_plans id {pid!r}",
                )
            seen.add(pid)
    if "default_mapping_plan" in doc:
        dmp = doc["default_mapping_plan"]
        if not isinstance(dmp, str) or not dmp:
            raise TemplateValidationError(
                "TEMPLATE-MAPPING",
                "default_mapping_plan must be non-empty string",
            )


def _validate_event_item(item: Any) -> None:
    if isinstance(item, dict) and "of" in item:
        _validate_of_group(item)
        return
    _validate_event(item)


def _validate_of_group(item: dict[str, Any]) -> None:
    extra = set(item) - {"of"}
    if extra:
        raise TemplateValidationError(
            "TEMPLATE-OF",
            f"unknown of-group fields: {sorted(extra)}",
        )
    branches = item.get("of")
    if not isinstance(branches, list) or len(branches) < 2:
        raise TemplateValidationError(
            "TEMPLATE-OF",
            "of needs ≥2 cadenspaden",
        )
    for raw in branches:
        if not isinstance(raw, dict):
            raise TemplateValidationError("TEMPLATE-OF", "of-item must be a mapping")
        extra_b = set(raw) - {"id", "events"}
        if extra_b:
            raise TemplateValidationError(
                "TEMPLATE-OF",
                f"unknown of-branch fields: {sorted(extra_b)}",
            )
        events = raw.get("events")
        if not isinstance(events, list) or not events:
            raise TemplateValidationError(
                "TEMPLATE-OF",
                "of-branch needs a non-empty events list",
            )
        for event in events:
            if isinstance(event, dict) and "of" in event:
                raise TemplateValidationError(
                    "TEMPLATE-OF",
                    "nested of is not supported",
                )
            _validate_event(event)


def _validate_event(event: Any) -> None:
    if not isinstance(event, dict):
        raise TemplateValidationError("TEMPLATE-EVENT", "event must be a mapping")
    role = _require(event, "role", str)
    if role not in ROLES:
        raise TemplateValidationError("TEMPLATE-ROLE", f"invalid role {role!r}")
    duration = _require(event, "duration", str)
    if duration not in DURATIONS:
        raise TemplateValidationError(
            "TEMPLATE-DURATION",
            f"invalid duration {duration!r}; use VSA ELM",
        )
    if "optional" in event and not isinstance(event["optional"], bool):
        raise TemplateValidationError("TEMPLATE-OPTIONAL", "optional must be bool")
    if "anchor" in event:
        canon = normalize_anchor(str(event["anchor"]))
        if canon not in ANCHORS:
            raise TemplateValidationError(
                "TEMPLATE-ANCHOR",
                f"invalid anchor {event['anchor']!r} (canonical {canon!r})",
            )
        event["anchor"] = canon
    pitches = _require(event, "pitches", dict)
    for voice in VOICES:
        if voice not in pitches:
            raise TemplateValidationError(
                "TEMPLATE-PITCHES",
                f"pitches missing voice {voice}",
            )
        pitch = pitches[voice]
        if not isinstance(pitch, str) or not DEGREE_RE.match(pitch):
            raise TemplateValidationError(
                "TEMPLATE-PITCHES",
                f"invalid degree for {voice}: {pitch!r}",
            )
    extra_voices = set(pitches) - set(VOICES)
    if extra_voices:
        raise TemplateValidationError(
            "TEMPLATE-PITCHES",
            f"unknown voices: {sorted(extra_voices)}",
        )
    allowed = {"role", "duration", "optional", "anchor", "pitches"}
    extra = set(event) - allowed
    if extra:
        raise TemplateValidationError(
            "TEMPLATE-EVENT",
            f"unknown event fields: {sorted(extra)}",
        )


def _require(doc: dict, key: str, typ: type) -> Any:
    if key not in doc:
        raise TemplateValidationError("TEMPLATE-REQUIRED", f"missing {key}")
    value = doc[key]
    if not isinstance(value, typ):
        raise TemplateValidationError(
            "TEMPLATE-TYPE",
            f"{key} must be {typ.__name__}",
        )
    return value
