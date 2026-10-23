"""Unit tests for import-.mscz.mvsa herkomststempels."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vsa.mvsa_partituur_stamp import (
    FIELD_PARTITUUR_SHA,
    is_mscz_import_mvsa,
    partituur_sha256,
    stamp_mscz_import_mvsa,
)


class MvsaPartituurStampTests(unittest.TestCase):
    def test_name_detect(self) -> None:
        self.assertTrue(is_mscz_import_mvsa(Path("a/lied.mscz.mvsa")))
        self.assertFalse(is_mscz_import_mvsa(Path("a/lied.mvsa")))

    def test_stamp_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mscz = root / "lied.mscz"
            mscz.write_bytes(b"fake-bytes")
            mvsa = root / "lied.mscz.mvsa"
            mvsa.write_text("L: a\nS: c\n", encoding="utf-8")
            stamp_mscz_import_mvsa(mvsa, mscz)
            text = mvsa.read_text(encoding="utf-8")
            digest = partituur_sha256(mscz)
            self.assertTrue(text.startswith(f"# {FIELD_PARTITUUR_SHA}: {digest}"))
            self.assertIn("L: a", text)
            self.assertEqual(text.count("vsa-partituur-sha256"), 1)


if __name__ == "__main__":
    unittest.main()
