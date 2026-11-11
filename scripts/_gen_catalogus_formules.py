"""Genereer bibliotheek content-source/catalogus/formules uit library + aliases."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vsa.template_library import (  # noqa: E402
    clear_alias_cache,
    default_library_root,
    list_template_ids,
    template_aliases,
)

OUT = (
    Path(__file__).resolve().parents[2]
    / "bibliotheek"
    / "content-source"
    / "catalogus"
    / "formules"
)
GH = (
    "https://github.com/orthodox-ronl/VSA-tooling/blob/main/"
    "docs/specification-vsa-templates/library"
)


def main() -> None:
    clear_alias_cache()
    lib = default_library_root()
    ids = list_template_ids(lib)
    aliases = template_aliases(lib)
    rev: dict[str, list[str]] = {}
    for a, c in aliases.items():
        if a != c:
            rev.setdefault(c, []).append(a)

    def load_doc(tid: str) -> dict:
        return yaml.safe_load((lib / tid / "template.yaml").read_text(encoding="utf-8"))

    canon_lines = []
    for tid in ids:
        doc = load_doc(tid)
        genre = doc.get("genre") or ""
        tone = doc.get("tone") or ""
        same = doc.get("same_as")
        bron = tid.rsplit("-", 1)[-1]
        same_s = f"`{same}`" if same else "—"
        canon_lines.append(
            f"| [`{tid}`]({tid}/) | {genre} | {tone} | {bron} | {same_s} |"
        )

    alias_lines = [
        f"| `{a}` | `{aliases[a]}` |"
        for a in sorted(aliases)
        if a != aliases[a]
    ]

    index = "\n".join(
        [
            "---",
            'title: "Formules"',
            'linkTitle: "Formules"',
            "weight: 5",
            "nav_sort: weight",
            "publicatiestatus: concept",
            "automatische_inhoud: false",
            "---",
            "",
            "# Formules (VSA-templates)",
            "",
            "Hier staan de **melodieformules** waarmee een `.vsa` naar een SATB-`.mvsa`",
            "wordt gezet (`vsa mvsa`). Een formule-id heeft de vorm",
            "`{soort}-toon-{n}-{bron}` (bijvoorbeeld `kondak-toon-8-hemelum`).",
            "",
            "De machinebron staat in VSA-tooling",
            "(`docs/specification-vsa-templates/library/` + `aliases.yaml`).",
            "Deze catalogus-pagina’s zijn het **register** voor beheerders.",
            "",
            "## Canonieke formules",
            "",
            "| Id | Soort | Toon | Bron | same_as |",
            "| --- | --- | --- | --- | --- |",
            *canon_lines,
            "",
            "## Aliassen",
            "",
            "Een alias is een andere naam voor dezelfde library-map. Liturgikon telt",
            "vooralsnog als Hemelum. Oude ids zonder bron-suffix blijven werken.",
            "Ontbrekende Hemelum-formules vallen via de aliaslijst terug op Groningen.",
            "",
            "| Alias | Canonieke id |",
            "| --- | --- |",
            *alias_lines,
            "",
            "Zie ook de handleiding [template SATB](../../handleiding/vsa/2-template-satb/).",
            "",
        ]
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_index.md").write_text(index, encoding="utf-8", newline="\n")

    for tid in ids:
        doc = load_doc(tid)
        genre = doc.get("genre") or ""
        tone = doc.get("tone") or ""
        same = doc.get("same_as")
        src = " ".join(str(doc.get("source") or "").split())
        als = sorted(rev.get(tid, []))
        also = doc.get("also_used_as") or []
        bron = tid.rsplit("-", 1)[-1]
        als_md = ", ".join(f"`{x}`" for x in als) if als else "—"
        also_md = ", ".join(f"`{x}`" for x in also) if also else "—"
        same_md = f"`{same}`" if same else "—"
        page = "\n".join(
            [
                "---",
                f'title: "{tid}"',
                f'linkTitle: "{tid}"',
                "weight: 10",
                "publicatiestatus: concept",
                "automatische_inhoud: false",
                f'formule_id: "{tid}"',
                "---",
                "",
                f"# `{tid}`",
                "",
                "| Veld | Waarde |",
                "| --- | --- |",
                f"| Soort | {genre} |",
                f"| Toon | {tone} |",
                f"| Bron (in id) | {bron} |",
                f"| same_as | {same_md} |",
                f"| also_used_as | {also_md} |",
                f"| Aliassen | {als_md} |",
                "",
                f"Bronvermelding in de YAML: {src}",
                "",
                f"Machinebestand: [{tid}/template.yaml]({GH}/{tid}/template.yaml).",
                "",
            ]
        )
        d = OUT / tid
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.md").write_text(page, encoding="utf-8", newline="\n")

    print(f"wrote {OUT / '_index.md'} and {len(ids)} pages")


if __name__ == "__main__":
    main()
