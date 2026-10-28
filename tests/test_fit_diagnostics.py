"""拟合诊断、边界防护和预测输入的回归测试。"""
from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from scipy.integrate import solve_ivp
from scipy.optimize import Bounds

from family_abm.fitting.fitter import make_fitter
from family_abm.fitting.lanchester import resource_competition, wellbeing_balance


@pytest.fixture(scope="module")
def wellbeing_df() -> pd.DataFrame:
    true_params = [0.8, 0.4, 0.3, 0.2, 0.5]
    t = np.arange(0.0, 41.0, 1.0)
    solution = solve_ivp(
        lambda tt, y: wellbeing_balance(tt, y, *true_params),
        [t[0], t[-1]], [0.5, 0.3], t_eval=t, method="RK45",
        rtol=1e-10, atol=1e-12,
    )
    assert solution.success
    return pd.DataFrame({
        "time": t,
        "agent_id": "synthetic",
        "state_synthetic_happiness": solution.y[0],
        "state_synthetic_stress": solution.y[1],
    })


def _wellbeing_mapping() -> dict[str, str]:
    return {
        "happiness": "state_synthetic_happiness",
        "stress": "state_synthetic_stress",
    }


def test_summary_reports_per_state_metrics(wellbeing_df: pd.DataFrame) -> None:
    fitter = make_fitter("wellbeing", state_mapping=_wellbeing_mapping())
    fitter.fit_from_dataframe(wellbeing_df, bounds=[(1e-4, 5.0)] * 5)
    summary = fitter.summary_json()

    per_state = summary["per_state"]
    assert set(per_state) == {"happiness", "stress"}
    for state, metric in per_state.items():
        assert metric["column"] == _wellbeing_mapping()[state]
        assert metric["n"] == len(wellbeing_df)
        assert metric["r_squared"] > 0.95
        assert metric["rmse"] >= 0.0
        assert isinstance(metric["mean"], float)
    json.dumps(summary, allow_nan=False)


def test_scipy_bounds_validate_size_finiteness_and_order(wellbeing_df: pd.DataFrame) -> None:
    cases = [
        (SimpleNamespace(lb=[1e-4] * 3, ub=[5.0] * 5), "下界数量"),
        (SimpleNamespace(lb=[1e-4] * 5, ub=[5.0] * 3), "上界数量"),
        (Bounds(lb=[1e-4, 1e-4, float("nan"), 1e-4, 1e-4], ub=[5.0] * 5), "非有限值"),
        (Bounds(lb=[0.2, 1e-4, 1e-4, 1e-4, 1e-4], ub=[0.1, 5.0, 5.0, 5.0, 5.0]), "下界大于上界"),
    ]
    for bounds, pattern in cases:
        with pytest.raises(ValueError, match=pattern):
            make_fitter("wellbeing", state_mapping=_wellbeing_mapping()).fit_from_dataframe(
                wellbeing_df, bounds=bounds,
            )


def test_predict_rejects_invalid_inputs_and_returns_state_by_time(
    wellbeing_df: pd.DataFrame,
) -> None:
    fitter = make_fitter("wellbeing", state_mapping=_wellbeing_mapping())
    fitter.fit_from_dataframe(wellbeing_df, bounds=[(1e-4, 5.0)] * 5)
    y0 = wellbeing_df[["state_synthetic_happiness", "state_synthetic_stress"]].iloc[0].to_numpy()

    t_pred = np.linspace(0.0, 5.0, 11)
    t_out, y_out = fitter.predict(t_pred, y0)
    assert np.array_equal(t_out, t_pred)
    assert y_out.shape == (fitter.n_states, t_pred.size)
    assert np.all(np.isfinite(y_out))

    with pytest.raises(ValueError, match="形状"):
        fitter.predict(t_pred, np.array([0.5]))
    with pytest.raises(ValueError, match="严格递增"):
        fitter.predict(np.array([1.0, 0.0]), y0)
    with pytest.raises(ValueError, match="有限值"):
        fitter.predict(np.array([0.0, float("nan")]), y0)
    with pytest.raises(ValueError, match="初值包含非有限值"):
        fitter.predict(t_pred, np.array([0.5, float("nan")]))


def test_resource_competition_can_recover_its_own_parameters() -> None:
    true_params = [0.4, 1.0, 0.35, 1.2, 0.05, 0.04]
    t = np.arange(0.0, 31.0, 1.0)
    solution = solve_ivp(
        lambda tt, y: resource_competition(tt, y, *true_params),
        [t[0], t[-1]], [0.3, 0.25], t_eval=t, method="RK45",
        rtol=1e-10, atol=1e-12,
    )
    assert solution.success
    frame = pd.DataFrame({
        "time": t,
        "agent_id": "synthetic",
        "state_r1": solution.y[0],
        "state_r2": solution.y[1],
    })
    fitter = make_fitter(
        "resource_competition",
        state_mapping={"R1": "state_r1", "R2": "state_r2"},
        alpha=0.05,
        beta=0.04,
    )
    fitter.fit_from_dataframe(frame)
    summary = fitter.summary_json()
    assert summary["r_squared"] > 0.99, summary
    assert set(summary["per_state"]) == {"R1", "R2"}
    assert fitter.fitted_param_dict["r1"] == pytest.approx(0.4, rel=0.01)
    assert fitter.fitted_param_dict["k1"] == pytest.approx(1.0, rel=0.01)
    assert fitter.fitted_param_dict["r2"] == pytest.approx(0.35, rel=0.01)
    assert fitter.fitted_param_dict["k2"] == pytest.approx(1.2, rel=0.01)
