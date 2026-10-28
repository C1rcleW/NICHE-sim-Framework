"""生境接口的可信输出契约：缺失值不得伪装成坐标。"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from family_abm.niche.micro_niche import MicroNiche
from family_abm.web.app import app


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_set_position_rejects_non_finite_values(value: float) -> None:
    niche = MicroNiche("member")
    with pytest.raises(ValueError, match="有限数值"):
        niche.set_position("economic", value)


def test_default_web_niche_marks_missing_social_dimension() -> None:
    client = TestClient(app)
    run = client.post("/api/run", json={"steps": 3})
    assert run.status_code == 200, run.text

    response = client.get("/api/niche")
    assert response.status_code == 200, response.text
    niches = response.json()["niches"]
    assert len(niches) == 5

    for niche in niches:
        assert niche["position"]["social"] is None
        assert niche["raw_values"]["social"] is None
        assert "social" in niche["missing_dimensions"]
        assert niche["position"]["economic"] is not None
        assert math.isfinite(niche["position"]["economic"])
        assert "economic" in niche["observed_dimensions"]
