"""Library template.mxl/.mscz blijven synchroon met template.yaml."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "sync_library_templates.py"

# Toon-4 formules die we actief bijhouden (Hemelum + Groningen).
TOON4_IDS = ("tropaar-toon-4", "groningen-tropaar-toon-4")


def test_toon4_template_artefacts_in_sync() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", *TOON4_IDS],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
