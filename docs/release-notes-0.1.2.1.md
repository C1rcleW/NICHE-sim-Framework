## 0.1.2.1：工程补丁

0.1.2 之后的缺陷修复补丁。**不改变影响公式、经济压力、收入归一化或默认模型参数**；
默认行为基线保持不变。研究语义争议仍记录在 [R0 研究决策记录](R0-研究决策记录.md)，
D1–D6 保持 OPEN，签署前不得称"已修复"。

## 修正

- **关系种子碰撞**：成员标签改为首次加入时固定序号，移除/重加成员不再复用旧序号，
  避免新关系与现存关系派生同一条随机流（动态家庭实验的复现性前提）。
- **成员注销对称**：注销单个成员时对称清理其所属家庭（含多家庭引用），
  家庭收入/压力聚合不再残留已注销成员。
- **生境距离维度对齐**：`distance_to` 按维度名对齐;维度集不同显式报错，
  不再静默产出错误距离/重叠度。
- **Plotly 自托管**：随包钉版 `plotly-2.32.0.min.js` 并附 MIT 许可文本，
  消除 CDN 单点，离线可用;失败文案改为本地资源口径。

## 验证

- 非 packaging 198 项、packaging 16 项、Playwright 浏览器冒烟 1 项、
  Node 前端行为与 Ruff 全部通过。
- `tools/baseline.py --check baseline/default_seed42.json` 与基线一致。
- 新增 `tests/test_p1_regressions.py` 覆盖上述修复与默认标签基线守卫。

## 已知限制（沿用 0.1.2）

- 影响公式归一化、经济压力时点、收入归一化、成年易感性记录、reset 语义、
  `resource_competition` 默认边界等仍为 R0 待决项。
- 关系 identity 对"重加顺序"敏感（确定、无碰撞）；R0 冻结期不做排序规范化，
  以免改变默认随机流。

## 安装

下载 Release 附件中的 wheel 后：

```bash
pip install family_abm-0.1.2.1-py3-none-any.whl
python -m family_abm.web      # http://127.0.0.1:8520
```

要求 Python >= 3.10；MIT 许可。

完整变更见 [CHANGELOG](https://github.com/C1rcleW/NICHE-sim-Framework/blob/main/CHANGELOG.md)。
