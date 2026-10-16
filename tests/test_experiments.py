"""实验脚本的参数贯通测试。

回归：``--steps`` 曾被**静默忽略**——``mechanism_validation.py`` 与
``sensitivity_analysis.py`` 的 main 把 ``args.steps`` 原样写进 JSON 报告的
``"steps"`` 字段，但 e2/e3/e4 及各复用函数从未接收它，实际始终跑默认
``STEPS=300``。结构化结果与实际运行不符，直接伤害可复现性（传 ``--steps 600``
时报告说 600、数据是 300），sensitivity 的"步数过短拒绝运行"护栏也因此失效。
"""
from __future__ import annotations

import pytest

import experiments.mechanism_validation as mv
from experiments.mechanism_validation import e2_stage_profile, e3_dose_response, e4_lagged_effect


def _spy_steps(monkeypatch) -> list[int]:
    """记录 run_ensemble 实际收到的 steps，再真实执行（返回值仍要可用）。"""
    recorded: list[int] = []
    real = mv.run_ensemble

    def spy(seeds, params, steps=mv.STEPS):
        recorded.append(steps)
        return real(seeds, params, steps=steps)

    monkeypatch.setattr(mv, "run_ensemble", spy)
    return recorded


def test_e2_honours_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _spy_steps(monkeypatch)
    e2_stage_profile([1000], strength=4.0, steps=40)
    assert recorded, "e2 未调用 run_ensemble"
    assert all(s == 40 for s in recorded), f"e2 未把 steps 传下去，实际收到 {recorded}"


def test_e3_honours_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _spy_steps(monkeypatch)
    e3_dose_response([1000], [0.0, 1.0], steps=40)
    assert recorded, "e3 未调用 run_ensemble"
    assert all(s == 40 for s in recorded), f"e3 未把 steps 传下去，实际收到 {recorded}"


def test_e4_honours_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _spy_steps(monkeypatch)
    e4_lagged_effect([1000], strength=4.0, steps=40)
    assert recorded, "e4 未调用 run_ensemble"
    assert all(s == 40 for s in recorded), f"e4 未把 steps 传下去，实际收到 {recorded}"


def test_sensitivity_helpers_honour_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    """sensitivity 复用 e2/e3/e4，steps 必须贯穿每一层。"""
    from experiments.sensitivity_analysis import p2_p3_stage_ratios, p4_dose_response, p5_lagged

    recorded = _spy_steps(monkeypatch)
    p2_p3_stage_ratios([1000], 0.0, 1.0, strength=4.0, steps=40)
    p4_dose_response([1000], 0.0, 1.0, steps=40)
    p5_lagged([1000], 0.0, 1.0, strength=4.0, steps=40)
    assert recorded, "sensitivity 的辅助函数未调用 run_ensemble"
    assert all(s == 40 for s in recorded), (
        f"sensitivity 未把 steps 传下去（护栏按 args.steps 判定、实际跑默认步数），收到 {recorded}"
    )
