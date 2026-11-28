"""VSA-tekstregels → template-frase-ids via text_mapping / mapping_plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TemplateMappingError(Exception):
    """Onmogelijke of inconsistente frase-toewijzing."""


@dataclass(frozen=True)
class MappingPlan:
    id: str
    steps: tuple[dict[str, Any], ...]
    label: str | None = None
    when: dict[str, Any] | None = None


def phrase_ids(doc: dict[str, Any]) -> set[str]:
    return {str(p["id"]) for p in doc.get("phrases", [])}


def compile_text_mapping(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Normaliseer legacy cycle/sequence of expliciete text_mapping naar stappen."""
    if "text_mapping" in doc:
        return _normalise_steps(doc["text_mapping"], phrase_ids(doc))
    if "sequence" in doc:
        return [{"sequence": [str(x) for x in doc["sequence"]]}]
    if "cycle" in doc and "final" in doc:
        return [
            {"repeat": [str(x) for x in doc["cycle"]], "until": "final"},
            {"phrase": str(doc["final"])},
        ]
    raise TemplateMappingError("template has no text_mapping, sequence, or cycle+final")


def list_mapping_plans(doc: dict[str, Any]) -> list[MappingPlan]:
    """Alle beschikbare plannen (mapping_plans of één default uit cycle/sequence)."""
    if "mapping_plans" in doc:
        ids = phrase_ids(doc)
        out: list[MappingPlan] = []
        for raw in doc["mapping_plans"]:
            if not isinstance(raw, dict):
                raise TemplateMappingError("mapping_plans items must be mappings")
            pid = str(raw.get("id", ""))
            if not pid:
                raise TemplateMappingError("mapping_plans item needs id")
            steps = _normalise_steps(raw.get("steps", []), ids)
            when = raw.get("when")
            if when is not None and not isinstance(when, dict):
                raise TemplateMappingError(f"plan {pid!r}: when must be a mapping")
            out.append(
                MappingPlan(
                    id=pid,
                    steps=tuple(steps),
                    label=str(raw["label"]) if raw.get("label") else None,
                    when=when,
                )
            )
        return out
    default_id = str(doc.get("default_mapping_plan", "default"))
    steps = compile_text_mapping(doc)
    label = _legacy_label(doc)
    return [MappingPlan(id=default_id, steps=tuple(steps), label=label)]


def select_mapping_plan(
    doc: dict[str, Any],
    stanza_count: int,
    *,
    plan_id: str | None = None,
) -> MappingPlan:
    plans = list_mapping_plans(doc)
    if plan_id is not None:
        for plan in plans:
            if plan.id == plan_id:
                return plan
        raise TemplateMappingError(f"unknown mapping plan id {plan_id!r}")
    specific = [
        p
        for p in plans
        if p.when is not None
        and not p.when.get("default")
        and _when_matches(p.when, stanza_count)
    ]
    if len(specific) > 1:
        raise TemplateMappingError(
            f"ambiguous mapping plans for stanza_count={stanza_count}: "
            f"{[p.id for p in specific]}"
        )
    if len(specific) == 1:
        return specific[0]
    defaults = [
        p for p in plans if p.when is None or (p.when and p.when.get("default"))
    ]
    if defaults:
        return defaults[0]
    if len(plans) == 1:
        return plans[0]
    raise TemplateMappingError(
        f"no mapping plan matches stanza_count={stanza_count}"
    )


def assign_stanzas_to_phrases(
    plan: MappingPlan | list[dict[str, Any]],
    stanza_count: int,
    *,
    phrase_id_set: set[str] | None = None,
) -> list[str]:
    """Wijs n tekstregels (frasen) toe aan template-frase-ids."""
    if stanza_count < 1:
        raise TemplateMappingError("stanza_count must be ≥ 1")
    steps = plan.steps if isinstance(plan, MappingPlan) else plan
    if phrase_id_set is None:
        phrase_id_set = set()
    result: list[str] = []
    idx = 0
    while idx < len(steps):
        step = steps[idx]
        rest = steps[idx + 1 :]
        if "phrase" in step:
            pid = str(step["phrase"])
            _check_phrase(pid, phrase_id_set)
            result.append(pid)
            idx += 1
            continue
        if "sequence" in step:
            seq = [str(x) for x in step["sequence"]]
            for pid in seq:
                _check_phrase(pid, phrase_id_set)
            # Speelplan eindigend op «laatste»: eerste n frasen volgen het
            # prefix van het plan; de allerlaatste frase altijd op «laatste».
            # Kortere VSA → korter speelplan; langer dan het plan → harde fout.
            if seq and seq[-1] == "laatste" and not rest:
                left = stanza_count - len(result)
                max_n = len(seq)
                plan_txt = ", ".join(seq)
                if left > max_n:
                    already = len(result)
                    total = stanza_count
                    raise TemplateMappingError(
                        f"Deze VSA heeft {total} frasen"
                        + (
                            f" ({already} al toegewezen, nog {left} over)"
                            if already
                            else ""
                        )
                        + f", maar het speelplan van dit template heeft maar "
                        f"{max_n} plaatsen: {plan_txt}. "
                        f"Regel: de eerste {max_n - 1} frasen volgen dat "
                        f"speelplan (zonder «laatste»); de allerlaatste frase "
                        f"hoort altijd op «laatste». Meer dan {max_n} frasen "
                        f"past niet bij deze formule — splits of herschrijf "
                        f"de VSA, of kies een ander template."
                    )
                if left < 1:
                    raise TemplateMappingError(
                        f"speelplan eindigt op «laatste» maar er blijven "
                        f"geen frasen over (stanza_count={stanza_count})"
                    )
                if left == 1:
                    result.append("laatste")
                else:
                    prefix = seq[:-1]
                    result.extend(prefix[: left - 1])
                    result.append("laatste")
                idx += 1
                continue
            result.extend(seq)
            idx += 1
            continue
        if "repeat" in step:
            pattern = [str(x) for x in step["repeat"]]
            if not pattern:
                raise TemplateMappingError("repeat pattern must be non-empty")
            for pid in pattern:
                _check_phrase(pid, phrase_id_set)
            until = step.get("until", "final")
            tail = _tail_stanza_cost(rest)
            left = stanza_count - len(result)
            if isinstance(until, str) and until == "final":
                need = left - tail
                if need < 0:
                    raise TemplateMappingError(
                        f"plan needs {tail} tail stanzas but only {left} remain"
                    )
                for j in range(need):
                    result.append(pattern[j % len(pattern)])
                idx += 1
                continue
            if isinstance(until, dict) and "remaining" in until:
                remaining = int(until["remaining"])
                if remaining != tail:
                    raise TemplateMappingError(
                        f"until.remaining={remaining} must match tail cost {tail}"
                    )
                need = left - remaining
                if need < 0:
                    raise TemplateMappingError(
                        f"until.remaining={remaining} exceeds {left} stanzas left"
                    )
                for j in range(need):
                    result.append(pattern[j % len(pattern)])
                idx += 1
                continue
            raise TemplateMappingError(f"unsupported until: {until!r}")
        raise TemplateMappingError(f"unknown mapping step: {step!r}")
    if len(result) != stanza_count:
        raise TemplateMappingError(
            f"plan assigns {len(result)} stanzas, expected {stanza_count}"
        )
    return result


def format_plan_label(plan: MappingPlan) -> str:
    if plan.label:
        return plan.label
    return _format_steps_label(list(plan.steps))


def _legacy_label(doc: dict[str, Any]) -> str | None:
    if "cycle" in doc and "final" in doc:
        body = ", ".join(str(x) for x in doc["cycle"])
        return f"||: {body} :|| {doc['final']}"
    if "sequence" in doc:
        return ", ".join(str(x) for x in doc["sequence"])
    return None


def _format_steps_label(steps: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    i = 0
    while i < len(steps):
        step = steps[i]
        if "phrase" in step:
            parts.append(str(step["phrase"]))
            i += 1
        elif "sequence" in step:
            parts.append(", ".join(str(x) for x in step["sequence"]))
            i += 1
        elif "repeat" in step:
            body = ", ".join(str(x) for x in step["repeat"])
            until = step.get("until", "final")
            if until == "final" and i + 1 < len(steps) and "phrase" in steps[i + 1]:
                parts.append(f"||: {body} :|| {steps[i + 1]['phrase']}")
                i += 2
            elif isinstance(until, dict) and "remaining" in until:
                tail = steps[i + 1 :]
                tail_txt = _format_steps_label(tail) if tail else ""
                parts.append(f"||: {body} :|| {tail_txt}")
                i += 1 + len(tail)
            else:
                parts.append(f"||: {body} :|| …")
                i += 1
        else:
            i += 1
    return ", ".join(p for p in parts if p)


def _tail_stanza_cost(steps: list[dict[str, Any]]) -> int:
    cost = 0
    for step in steps:
        if "phrase" in step:
            cost += 1
        elif "sequence" in step:
            cost += len(step["sequence"])
        elif "repeat" in step:
            raise TemplateMappingError(
                "nested repeat in tail is not supported"
            )
        else:
            raise TemplateMappingError(f"unknown tail step: {step!r}")
    return cost


def _normalise_steps(steps: Any, phrase_id_set: set[str]) -> list[dict[str, Any]]:
    if not isinstance(steps, list) or not steps:
        raise TemplateMappingError("text_mapping steps must be a non-empty list")
    out: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            raise TemplateMappingError("each mapping step must be a mapping")
        if "phrase" in step:
            pid = str(step["phrase"])
            _check_phrase(pid, phrase_id_set)
            out.append({"phrase": pid})
        elif "sequence" in step:
            seq = [str(x) for x in step["sequence"]]
            if not seq:
                raise TemplateMappingError("sequence must be non-empty")
            for pid in seq:
                _check_phrase(pid, phrase_id_set)
            out.append({"sequence": seq})
        elif "repeat" in step:
            pattern = [str(x) for x in step["repeat"]]
            if not pattern:
                raise TemplateMappingError("repeat must be non-empty")
            for pid in pattern:
                _check_phrase(pid, phrase_id_set)
            entry: dict[str, Any] = {"repeat": pattern}
            if "until" in step:
                entry["until"] = step["until"]
            out.append(entry)
        else:
            raise TemplateMappingError(
                "step must contain phrase, sequence, or repeat"
            )
    return out


def _check_phrase(pid: str, phrase_id_set: set[str]) -> None:
    if phrase_id_set and pid not in phrase_id_set:
        raise TemplateMappingError(f"unknown phrase id {pid!r}")


def _when_matches(when: dict[str, Any] | None, stanza_count: int) -> bool:
    if when is None:
        return True
    if when.get("default"):
        return True
    mod_spec = when.get("stanza_count_mod")
    if mod_spec is not None:
        if not isinstance(mod_spec, dict):
            return False
        mod = int(mod_spec.get("mod", 0))
        rem = mod_spec.get("remainder")
        if mod < 1:
            return False
        if rem is not None and stanza_count % mod != int(rem):
            return False
        if rem is None and stanza_count % mod != 0:
            return False
    min_n = when.get("stanza_count_min")
    if min_n is not None and stanza_count < int(min_n):
        return False
    max_n = when.get("stanza_count_max")
    if max_n is not None and stanza_count > int(max_n):
        return False
    eq = when.get("stanza_count")
    if eq is not None and stanza_count != int(eq):
        return False
    if when.keys() <= {"default"}:
        return bool(when.get("default"))
    return True
