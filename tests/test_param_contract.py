"""参数规格与服务端输入边界的契约测试。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from family_abm.family.family_member import DEFAULT_PARAMS
from family_abm.parameters import PARAM_GROUPS, PARAM_SPECS
from family_abm.web.app import app

client = TestClient(app)


def test_param_specs_cover_every_default_and_group() -> None:
    assert set(PARAM_SPECS) == set(DEFAULT_PARAMS)
    grouped = [key for keys in PARAM_GROUPS.values() for key in keys]
    assert sorted(grouped) == sorted(DEFAULT_PARAMS)

    response = client.get("/api/params")
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"defaults", "groups", "specs", "limits"}
    assert set(body["specs"]) == set(DEFAULT_PARAMS)
    for key, value in DEFAULT_PARAMS.items():
        spec = body["specs"][key]
        assert spec["min"] <= value <= spec["max"], key


def test_action_controls_reject_extra_member_fields() -> None:
    response = client.post(
        "/api/run",
        json={"steps": 1, "families": [{"name": "A", "members": [{"name": "x", "bogus": 1}]}]},
    )
    assert response.status_code == 422, response.text
    assert response.json()["status"] == "validation_error"


def test_action_controls_reject_unknown_and_out_of_range_params() -> None:
    for params in (
        {"unknown_parameter": 1},
        {"income_age_spread": 0},
        {"stage_shift_years": -11},
        {"use_life_stage_susceptibility": 0.5},
        {"influence_strength": 5.1},
    ):
        response = client.post("/api/run", json={"steps": 1, "params": params})
        assert response.status_code == 422, (params, response.text)
        assert response.json()["status"] == "validation_error"


def test_action_controls_enforce_step_and_population_limits() -> None:
    cases = [
        {"steps": 0},
        {"steps": 5001},
        {"steps": "5"},
        {"steps": True},
        {"steps": 1, "families": [{"name": f"F{i}", "members": []} for i in range(21)]},
        {"steps": 1, "families": [{"name": "A", "members": [{"name": str(i)} for i in range(51)]}]},
    ]
    for payload in cases:
        response = client.post("/api/run", json=payload)
        assert response.status_code == 422, (payload, response.text)
        assert response.json()["status"] == "validation_error"


def test_negative_stage_shift_remains_valid() -> None:
    response = client.post(
        "/api/run",
        json={"steps": 1, "params": {"stage_shift_years": -3}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"
