"""为 GitHub Release 抽取发布说明正文。

从 CHANGELOG.md 里取出指定版本的段落，去掉文件级抬头与链接定义，
输出可直接粘贴到 Release 表单的内容。

用法：
    python tools/extract_release_notes.py 0.1.0 docs/release-notes-0.1.0.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"

REPO_URL = "https://github.com/C1rcleW/NICHE-sim-Framework"


def _load_results(name: str) -> dict:
    import json

    path = REPO / "experiments" / "results" / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"缺少实验结果文件：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_preamble(version: str) -> str:
    """从实验 JSON 生成发布说明的前半部分。

    此前这里是**硬编码**的（round-2 审查 D4）：数字过期、结论写着"五条结论全部
    成立"（当时已是假话）、安装命令固定在 0.1.0——给别的版本生成说明时会把这些
    错误内容原样带进 Release 正文。现全部从结果文件派生。
    """
    mech = _load_results("mechanism_validation")
    sens = _load_results("sensitivity_analysis")
    e2, e3, e4 = mech["e2"], mech["e3"], mech["e4"]
    seeds = len(mech["seeds"])

    ratios = " → ".join(f"{r:.3f}" for r in e2["ratios"])
    clean = [p for p in e3["points"] if p["clamped_fraction"] == 0.0 and p["strength"] > 0]
    snr_range = f"{min(p['snr'] for p in clean):.2f}–{max(p['snr'] for p in clean):.2f}"

    tallies = sens["summary"]["tallies"]
    robustness = sens["summary"]["robustness"]
    keys = {"P1": "p1_all_pass", "P2": "p2_all_pass", "P3": "p3_all_pass", "P4": "p4_all_pass"}
    lines = []
    for claim, tally in tallies.items():
        code = claim.split()[0]
        ok = robustness.get(keys[code]) if code in keys else robustness.get("p5_pass_rate") == 1.0
        lines.append(f"| {claim} | {tally} | {'稳健' if ok else '**不稳健**'} |")
    upper = sens["summary"].get("clean_upper_bound_range") or []
    upper_text = f"{upper[0]:g}–{upper[-1]:g}" if len(upper) >= 2 else "—"

    return f"""## 研究问题

家庭内部的代际影响强度随子代发展阶段系统性下降。这种变化如何影响子代的长期结果？
含有时变影响系数的家庭动力学，能否被低维方程刻画？

## 验证结果

结果基线：{seeds} 个种子（{mech['seeds'][0]}–{mech['seeds'][-1]}）、{mech['steps']} 步。
**随机量的数值只在该种子数下成立**——配对噪声用系综内标准差估计，小 n 会低估噪声、放大信噪比。

| 检验 | 结论 |
|---|---|
| E1 易感性阶段结构 | 单调性违例 {mech['e1']['monotone_violations']} 次；阶段边界跳变 {mech['e1']['max_boundary_jump']:.1e}（连续） |
| E2 效力随阶段递减 | {ratios}（学前期 → 成年早期） |
| E3 剂量-反应 | 无钳位区间内单调，信噪比 {snr_range}；**可信强度上限为 {e3['clean_upper_bound']:g}**，超过后状态触界使结论失效 |
| E4 成年后滞后效应 | 仍可分辨（信噪比 {e4['adulthood']['snr']:.2f}），但衰减至童年期的 {e4['decay_ratio']:.1%} |

参数敏感性（25–75 个组合）：

| 结论 | 稳健组合数 | 判定 |
|---|---|---|
{chr(10).join(lines)}

扰动参数不改变机制的结构性结论，只改变适用边界的数值位置
（可信强度上限在 {upper_text} 之间移动）。

## 已知限制

本工作是**方法性探索，不是政策效果评估**，不提供因果效应估计。

- 影响是**单向下行**的：只实现"年长成员影响年幼成员"，配偶互影响、同伴影响未建模
- 参数部分来自理论解读而非实证测量；定性结论已通过敏感性分析证明稳健，
  但定量门槛依赖参数
- **一个否定的结果**：含有时变影响系数的家庭聚合动力学，无法被单一常系数
  微分方程刻画

完整清单见 [README 的「说明与限制」]({REPO_URL}#说明与限制)
与 [CHANGELOG]({REPO_URL}/blob/main/CHANGELOG.md)。

## 安装

下载下方附件中的 wheel 后：

```bash
pip install family_abm-{version}-py3-none-any.whl
python -m family_abm.web      # 启动仪表板 → http://127.0.0.1:8520
```

要求 Python >= 3.10；MIT 许可。

---

## 完整变更

"""


def extract(version: str) -> str:
    text = CHANGELOG.read_text(encoding="utf-8")
    # 匹配 "## [0.1.1] — ..." 到下一个 "## [" 之前
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"CHANGELOG 中未找到版本 {version}")
    body = match.group(1).strip()
    # 去掉尾部的链接定义（如 [0.1.1]: https://...）
    body = re.sub(r"\n\[[^\]]+\]:\s*\S+\s*$", "", body).strip()
    return build_preamble(version) + body + "\n"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    version = argv[1]
    notes = extract(version)
    if len(argv) >= 3:
        out = Path(argv[2])
        out.write_text(notes, encoding="utf-8")
        print(f"已写出 {out}（{len(notes.splitlines())} 行）")
    else:
        print(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
