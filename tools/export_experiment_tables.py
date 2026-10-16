"""从实验结果 JSON 生成 Markdown 表格（单一真源 → 机械派生）。

动机：README 与 docs/研究设计.md 里的实验数字此前是手写的，代码一改就过期——
round-2 审查实测发现 E2/E3/E4 的随机量、可约性的 C1、敏感性分析的 P2 tally
全部与当前代码不一致（`README.md` 的"五条结论全部成立"在当前代码下为假），
而且没有任何测试会因此失败。

本工具把"数字"变成派生物：

    experiments/results/*.json  ──►  带标记的 Markdown 块

用法：
    python tools/export_experiment_tables.py            # 打印到 stdout
    python tools/export_experiment_tables.py --out FILE # 写入文件
    python tools/export_experiment_tables.py --check    # 与已提交的派生文件比对

配套 `tests/test_experiment_numbers.py` 强制 README 与文档里引用的数字与
结果 JSON 一致，使"改了代码忘了更新文档"立刻失败。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "experiments" / "results"

HEADER = """<!-- 本文件由 tools/export_experiment_tables.py 从 experiments/results/*.json 派生，请勿手工编辑。 -->
<!-- 数字的唯一真源是结果 JSON；要更新请重跑实验后执行本工具。 -->
"""


def _load(name: str) -> dict:
    path = RESULTS / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"缺少结果文件：{path}\n请先运行 experiments/{name}.py 生成。")
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def _e2_rows(e2: dict) -> list[tuple[str, float, float, float, float | None]]:
    """把 E2 的 per_stage 与 amplification 按阶段连接起来。

    两者在结果 JSON 中是并列的两个列表（`per_stage` 与 `amplification`），
    用 stage 名连接——不要假设 per_stage 里带放大倍数。
    """
    amp_by_stage = {a["stage"]: a.get("amplification_factor") for a in e2.get("amplification", [])}
    rows = []
    for stage in e2["per_stage"]:
        amp = amp_by_stage.get(stage["stage"])
        rows.append((
            stage["stage"],
            stage["staged_openness"],
            stage["openness_ratio"],
            stage["observed_ratio"],
            amp if isinstance(amp, (int, float)) else None,
        ))
    return rows


def mechanism_section(data: dict) -> str:
    e1, e2, e3, e4 = data["e1"], data["e2"], data["e3"], data["e4"]
    lines: list[str] = []
    lines.append(f"结果基线：seeds={len(data['seeds'])}、steps={data['steps']}（种子 "
                 f"{data['seeds'][0]}–{data['seeds'][-1]}）。\n")

    # E1
    lines.append("### E1 易感性阶段结构\n")
    lines.append(f"- 单调性违例：**{e1['monotone_violations']}** 次")
    lines.append(f"- 阶段边界最大跳变：**{_fmt(e1['max_boundary_jump'], 8)}**（远小于阶段内变化，曲线连续）\n")
    lines.append("| 阶段 | 年龄中点 | 期望易感性 | 实际易感性 |")
    lines.append("|---|---|---|---|")
    for p in e1["plateaus"]:
        lines.append(f"| {p['stage']} | {p['age_mid']:.1f} | {_fmt(p['expected'])} | {_fmt(p['actual'])} |")
    lines.append("")

    # E2
    lines.append("### E2 效力随发展阶段递减\n")
    lines.append("| 阶段 | 阶段化易感性 | 恒定易感性 | 效力比 | 放大倍数 |")
    lines.append("|---|---|---|---|---|")
    for stage, staged, constant, ratio, amp in _e2_rows(e2):
        amp_text = _fmt(amp, 2) if amp is not None else "—"
        lines.append(
            f"| {stage} | {_fmt(staged)} | {_fmt(constant)} | **{_fmt(ratio, 3)}** | {amp_text} |"
        )
    lines.append("")
    ratios = " → ".join(_fmt(r, 3) for r in e2["ratios"])
    lines.append(f"- 效力比序列：**{ratios}**")
    lines.append(f"- 单调递减：{e2['ratio_decreasing']}；易感性低于基准的阶段影响更弱："
                 f"{e2['weaker_when_openness_below_half']}\n")

    # E3
    lines.append("### E3 剂量—反应与适用边界\n")
    lines.append("| 影响强度 | 均值偏离 | 配对噪声 | 信噪比 | 触界比例 |")
    lines.append("|---|---|---|---|---|")
    for p in e3["points"]:
        lines.append(
            f"| {p['strength']} | {_fmt(p['mean_abs_deviation'])} | {_fmt(p['paired_noise'])} "
            f"| {_fmt(p['snr'], 2)} | {p['clamped_fraction']:.2%} |"
        )
    lines.append("")
    lines.append(f"- 无钳位区间内单调：{e3['monotone']}")
    lines.append(f"- **可信强度上限：{e3['clean_upper_bound']}**（超过后状态大量触及取值边界，"
                 f"剂量—反应不再可信）\n")

    # E4
    lines.append("### E4 成年后的滞后效应\n")
    lines.append("| 窗口 | 样本数 | 均值偏离 | 配对噪声 | 信噪比 |")
    lines.append("|---|---|---|---|---|")
    for key, label in (("childhood", "童年期"), ("adulthood", "成年后")):
        w = e4[key]
        lines.append(
            f"| {label} | {w['n']} | {_fmt(w['mean_deviation'])} | {_fmt(w['paired_noise'])} "
            f"| **{_fmt(w['snr'], 2)}** |"
        )
    lines.append("")
    lines.append(f"- 成年后仍可分辨：{e4['persists_into_adulthood']}")
    lines.append(f"- 效应衰减比（成年后/童年期）：**{e4['decay_ratio']:.1%}**\n")

    lines.append("### 判定\n")
    lines.append("| 检验 | 结果 |")
    lines.append("|---|---|")
    for v in data["verdicts"]:
        lines.append(f"| {v['claim']} | {'通过' if v['passed'] else '未通过'} |")
    lines.append("")
    return "\n".join(lines)


def sensitivity_section(data: dict) -> str:
    summary = data["summary"]
    lines: list[str] = []
    lines.append(f"结果基线：每个参数组合 {len(data['seeds'])} 个种子、steps={data['steps']}。\n")
    lines.append("| 结论 | 稳健组合数 | 判定 |")
    lines.append("|---|---|---|")
    robustness = summary["robustness"]
    keys = {"P1": "p1_all_pass", "P2": "p2_all_pass", "P3": "p3_all_pass", "P4": "p4_all_pass"}
    for claim, tally in summary["tallies"].items():
        code = claim.split()[0]
        ok = (robustness.get(keys[code]) if code in keys
              else robustness.get("p5_pass_rate") == 1.0)
        lines.append(f"| {claim} | {tally} | {'稳健' if ok else '**不稳健**'} |")
    lines.append("")
    rng = summary.get("clean_upper_bound_range") or []
    if rng:
        lines.append(f"- 可信强度上限随参数取值在 **{rng[0]} – {rng[-1]}** 之间移动")
    lines.append(f"- 强度网格：{sorted({p['strength'] for p in data['p5']})}")
    lines.append("")
    return "\n".join(lines)


def reducibility_section(data: dict) -> str:
    lines: list[str] = []
    lines.append(f"结果基线：seed={data['seed']}、steps={data['steps']}。\n")
    # 取分阶段窗口名（各条件一致）
    any_cond = next(iter(data["conditions"].values()))
    stage_names = list(any_cond["reducibility"]["stages"].keys())

    header = "| 条件 | 说明 | 全窗口 R² | " + " | ".join(stage_names) + " |"
    lines.append(header)
    lines.append("|---|---|---|" + "---|" * len(stage_names))
    for code, cond in data["conditions"].items():
        red = cond["reducibility"]
        cells = []
        for stage in stage_names:
            value = red["stages"].get(stage, {}).get("r_squared")
            cells.append(_fmt(value) if isinstance(value, (int, float)) else "—")
        full = red["full"].get("r_squared")
        lines.append(
            f"| {code} | {cond['label']} | {_fmt(full) if isinstance(full, (int, float)) else '—'} "
            f"| " + " | ".join(cells) + " |"
        )
    lines.append("")
    return "\n".join(lines)


def build() -> str:
    parts = [HEADER]
    parts.append("## 实验结果（自动派生）\n")
    parts.append("> 下列表格由 `tools/export_experiment_tables.py` 从 "
                 "`experiments/results/*.json` 生成。\n")
    parts.append("# 机制验证\n")
    parts.append(mechanism_section(_load("mechanism_validation")))
    parts.append("\n# 参数敏感性\n")
    parts.append(sensitivity_section(_load("sensitivity_analysis")))
    parts.append("\n# 生命阶段可约性\n")
    parts.append(reducibility_section(_load("life_stage_reducibility")))
    return "\n".join(parts).rstrip() + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="从实验结果 JSON 派生 Markdown 表格")
    parser.add_argument("--out", type=Path, help="写入文件")
    parser.add_argument("--check", action="store_true", help="与已提交的派生文件比对")
    args = parser.parse_args(argv[1:])

    text = build()
    target = args.out
    if args.check:
        target = target or (REPO / "docs" / "experiments.md")
        if not target.exists():
            print(f"[FAIL] 缺少派生文件：{target}")
            return 1
        current = target.read_text(encoding="utf-8")
        if current.replace("\r\n", "\n") != text.replace("\r\n", "\n"):
            print(f"[FAIL] {target} 与结果 JSON 不一致")
            print("        请重跑实验后执行：python tools/export_experiment_tables.py --out " + str(target))
            import difflib

            diff = difflib.unified_diff(
                current.splitlines(), text.splitlines(),
                fromfile="已提交", tofile="重新生成", lineterm="", n=1,
            )
            for line in list(diff)[:40]:
                print("        " + line)
            return 1
        print(f"[OK] {target} 与结果 JSON 一致")
        return 0

    if target:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"[OK] 已写入 {target}（{len(text.splitlines())} 行）")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
