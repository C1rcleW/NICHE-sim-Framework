"""examples/ 冒烟测试：模块可导入、核心入口可调用。

回归：``fitting_viz_demo.py`` 缺 ``import pandas as pd``（Python <3.14 下
函数注解 ``df: pd.DataFrame`` 在定义时求值 → 模块导入即 NameError），
且 ``make_fitter("influence", ...)`` 只给 2 个初值而模型有 4 个参数
（gamma/delta/target1/target2）→ 拟合段 ValueError。示例从未被 CI 触达。
"""
from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize("module_name", [
    "examples.simple_family",
    "examples.ml_ready",
    "examples.fitting_viz_demo",
])
def test_example_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "main"), f"{module_name} 缺少 main() 入口"


def test_fitting_viz_demo_short_simulation() -> None:
    """fitting_viz_demo.run_simulation 短步数可跑通并产出 DataFrame。"""
    mod = importlib.import_module("examples.fitting_viz_demo")
    sim, recorder = mod.run_simulation(steps=5)
    df = recorder.to_dataframe()
    assert len(df) > 0
    assert {"agent_id", "time"} <= set(df.columns)
    assert sim.environment.get_agents(), "仿真后环境为空"


def test_fitting_viz_demo_fitting_section(tmp_path, monkeypatch) -> None:
    """demo_fitting 跑通：曾因 influence p0 少 2 个参数而 ValueError。"""
    mod = importlib.import_module("examples.fitting_viz_demo")
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)

    _, recorder = mod.run_simulation(steps=30)
    mod.demo_fitting(recorder.to_dataframe())

    assert (tmp_path / "08_fit_wellbeing.png").exists()
    assert (tmp_path / "09_fit_influence.png").exists()
