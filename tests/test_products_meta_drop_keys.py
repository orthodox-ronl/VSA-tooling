"""``drop_product_keys`` haalt alleen de genoemde keys uit de meta."""

from __future__ import annotations

import json

from vsa.products_meta import drop_product_keys, load_meta, meta_path_for


def test_drop_laat_de_rest_staan(tmp_path):
    bron = tmp_path / "lied.mvsa"
    bron.write_text("gewijzigd", encoding="utf-8")
    meta = {
        "schema": 2,
        "bron_sha256": "oud",
        "products": {"svg": {"file": "a"}, "svg-translit-ksl": {"file": "b"}},
    }
    meta_path_for(bron).write_text(json.dumps(meta), encoding="utf-8")
    assert drop_product_keys(bron, {"svg-translit-ksl", "pdf"}) == [
        "svg-translit-ksl"
    ]
    after = load_meta(bron)
    assert after["schema"] == 2
    assert after["bron_sha256"] == "oud"
    assert list(after["products"]) == ["svg"]
