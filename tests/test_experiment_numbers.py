"""实验数字的防漂移测试。

背景（round-2 审查发现）：README 与 docs/研究设计.md 里的实验数字是手写的。
代码改动后结果文件过期，而**没有任何测试会失败**——实测 E2/E3/E4 的随机量、
可约性的 C1、敏感性分析的 P2 tally 全部与当前代码不一致，README 里
"五条结论全部成立"在当时已是假话。

本测试建立两条守卫：

1. `docs/experiments.md` 必须与 `experiments/results/*.json` 一致
   （即派生文件不能过期）；
2. README 中**引用**的关键数字必须能在结果 JSON 中找到（容差 0.001），
   并按 README 的书写惯例允许两种格式（原始精度 / 4 位小数）。

这样"改了代码没重跑实验"或"重跑了没更新 README"都会立刻失败。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "experiments" / "results"
DERIVED = REPO / "docs" / "experiments.md"
README = REPO / "README.md"

TOLERANCE = 0.001


def _load(name: str) -> dict:
    path = RESULTS / f"{name}.json"
    if not path.exists():
        pytest.fail(f"缺少结果文件 {path}；请先运行 experiments/{name}.py")
    return json.loads(path.read_text(encoding="utf-8"))


def _render(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


# ── 1. 派生文件与结果 JSON 一致 ──────────────────────────────────────────


def test_derived_experiment_doc_matches_result_json() -> None:
    """docs/experiments.md 必须可由当前结果 JSON 重新生成（防止派生文件过期）。"""
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "tools/export_experiment_tables.py", "--check"],
        cwd=str(REPO), capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, (
        "docs/experiments.md 与 experiments/results/*.json 不一致——"
        "请重跑实验后执行 python tools/export_experiment_tables.py --out docs/experiments.md\n"
        f"{proc.stdout}\n{proc.stderr}"
    )


# ── 2. README 引用的数字必须存在于结果 JSON ──────────────────────────────


def _readme_numbers(section: str) -> str:
    """取出 README 中「实验结果」一节。"""
    text = README.read_text(encoding="utf-8")
    match = re.search(rf"^## {section}\n(.*?)^---", text, re.MULTILINE | re.DOTALL)
    assert match, f"README 中找不到「{section}」一节"
    return match.group(1)


def _assert_cited(readme_text: str, value: float, label: str, digits: int = 4) -> None:
    """断言 README 以原始精度或 4 位小数引用了 value。"""
    candidates = {_render(value, digits)}
    if abs(value) < 1000:
        candidates.add(_render(value, 3))
        candidates.add(_render(value, 2))
    hit = any(c in readme_text for c in candidates)
    assert hit, (
        f"README 未引用 {label} 的当前值 {value:.6f}"
        f"（可接受的写法：{'、'.join(sorted(candidates))}）"
        "——请同步 README 的「实验结果」一节"
    )


def test_readme_cites_current_e2_ratios() -> None:
    """E2 效力比序列必须与结果一致（README 曾写 1.128/0.833/0.026/0.017，已过时）。"""
    data = _load("mechanism_validation")
    readme = _readme_numbers("实验结果")
    ratios = data["e2"]["ratios"]
    assert len(ratios) >= 4, "E2 阶段数少于 4"
    for index, value in enumerate(ratios, start=1):
        _assert_cited(readme, value, f"E2 第 {index} 阶段效力比", digits=3)


def test_readme_cites_current_e3_bound_and_snr() -> None:
    """E3 的可信强度上限与无钳位区信噪比必须与结果一致。"""
    data = _load("mechanism_validation")
    readme = _readme_numbers("实验结果")
    bound = data["e3"]["clean_upper_bound"]
    assert f"上限为 {bound:g}" in readme or f"上限：{bound:g}" in readme, (
        f"README 未声明 E3 的可信强度上限 {bound:g}"
    )
    clean = [p for p in data["e3"]["points"] if p["clamped_fraction"] == 0.0 and p["strength"] > 0]
    assert clean, "E3 没有无钳位的强度点"
    for point in (clean[0], clean[-1]):
        _assert_cited(readme, point["snr"], f"E3 强度 {point['strength']:g} 的信噪比", digits=2)


def test_readme_cites_current_e4_snr_and_decay() -> None:
    """E4 的成年后信噪比与衰减比必须与结果一致。"""
    data = _load("mechanism_validation")
    readme = _readme_numbers("实验结果")
    _assert_cited(readme, data["e4"]["adulthood"]["snr"], "E4 成年后信噪比", digits=2)
    decay_pct = data["e4"]["decay_ratio"] * 100
    assert f"{decay_pct:.1f}%" in readme, (
        f"README 未引用 E4 的衰减比 {decay_pct:.1f}%（当前结果 {data['e4']['decay_ratio']:.6f}）"
    )


def test_readme_sensitivity_tallies_match_results() -> None:
    """README 的敏感性 tally 必须与结果一致——**包括不稳健的项**。

    round-2 审查前 README 声称"五条结论全部成立"，而 P2 在当时已是 24/25。
    本测试要求 README 如实写出每个 tally，且"不稳健/并非全部成立"的说明
    必须与 tally 相符。
    """
    data = _load("sensitivity_analysis")
    readme = _readme_numbers("实验结果")
    tallies = data["summary"]["tallies"]
    for claim, tally in tallies.items():
        code = claim.split()[0]
        assert tally in readme, (
            f"README 未引用 {code} 的当前 tally {tally}（结果文件：{tally}）"
        )
    # 若存在未满的 tally，README 必须明确说明并非全部成立
    total_expected = {"P1": 25, "P2": 25, "P3": 25, "P4": 25, "P5": 75}
    imperfect = [
        claim for claim, tally in tallies.items()
        if int(tally.split("/")[0]) < total_expected.get(claim.split()[0], 10**9)
    ]
    if imperfect:
        assert "并非在所有参数组合下成立" in readme or "不稳健" in readme, (
            f"存在未满的 tally（{imperfect}），README 必须说明结论并非全部成立，"
            "而不是声称'全部成立'"
        )


def test_readme_does_not_claim_all_conclusions_hold_unconditionally() -> None:
    """回归守卫：防回退到"五条结论全部成立"这种与证据不符的表述。"""
    text = README.read_text(encoding="utf-8")
    forbidden = re.compile(r"五条结论[^。\n]*全部成立")
    assert not forbidden.search(text), (
        "README 出现「五条结论…全部成立」的表述。当前敏感性分析存在未满的 tally，"
        "该表述与证据不符——请改为给出具体组合数。"
    )


def test_result_files_record_their_seed_count() -> None:
    """结果文件必须记录 seeds，且数字只在该种子数下成立（审查 E-02）。"""
    for name in ("mechanism_validation", "sensitivity_analysis"):
        data = _load(name)
        seeds = data.get("seeds")
        assert isinstance(seeds, list) and len(seeds) >= 2, (
            f"{name}.json 必须记录 seeds 列表（收到 {seeds!r}）；"
            "单一 seed 的结果无法区分信号与噪声"
        )
        assert data.get("steps"), f"{name}.json 必须记录 steps"


def test_readme_declares_result_baseline() -> None:
    """README 必须声明结果所用的种子数与步数——否则数字不可复核。"""
    data = _load("mechanism_validation")
    readme = _readme_numbers("实验结果")
    n_seeds = len(data["seeds"])
    assert f"{n_seeds} 个种子" in readme, (
        f"README 未声明机制验证用了 {n_seeds} 个种子（结果 baseline 的一部分）"
    )
    assert str(data["steps"]) in readme, f"README 未声明步数 {data['steps']}"
