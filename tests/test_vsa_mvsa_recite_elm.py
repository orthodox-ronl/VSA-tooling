"""``hoor_`` in een recite-groep: ELM hoort ná ``)``, niet erbinnen."""

from __future__ import annotations

from pathlib import Path

from vsa.mvsa_validate import validate_mvsa_text
from vsa.vsa_mvsa import convert_vsa_to_mvsa

VSA = """\
---
titel: Heer ik roep - Toon 6 (couplet 1)
taal: nl
soort: stichier
toon: 6
formule: stichier
do: F4
mode: major
tempo: 181
---

[:] Heer ik roep tot U ver{\\hoor_} {/mij_},
{/ver}hoor_ {\\mij} o {/Heer_},
{/Heer} ik roep tot U ver{\\&\\hoor_&~} {\\mij_},
{/sla} acht op de stem van mijn {\\sme_}{/king_},
{/wan}neer ik tot_ {\\U_} {\\roep_}, //
{/&/ver}{/&\\hoor_.&-} {\\mij_} {\\o_} {/Heer__}. [:]
"""


def test_recite_trailing_elm_after_paren(tmp_path: Path) -> None:
    src = tmp_path / "stichier-heer-ik-roep-toon-6-groningen-1.vsa"
    src.write_text(VSA, encoding="utf-8")
    text = convert_vsa_to_mvsa(src, write=False).text
    assert "(ver-hoor)_" in text
    assert "(wan-neer ik tot)_" in text
    assert "hoor_)" not in text and "tot_)" not in text
    errors = [
        d
        for d in validate_mvsa_text(text)
        if d.severity == "error"
    ]
    assert not errors, errors
