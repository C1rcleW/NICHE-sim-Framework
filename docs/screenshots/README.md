# 截图目录

本目录保存当前版本的 Web 仪表板截图，README 的「Web 仪表板」章节直接引用：

| 文件名 | 内容 |
|---|---|
| `dashboard.png` | Charts 标签页：时间序列与生境状态提示 |
| `fitting.png` | Fitting 标签页：分状态拟合指标与预测曲线 |
| `network.png` | Network 标签页：家庭关系网络 |

## 生成方式

```bash
pip install -e ".[dev,e2e]"
python -m playwright install chromium
python tools/capture_dashboard_screenshots.py
# 或复用系统 Chrome：
PLAYWRIGHT_CHANNEL=chrome python tools/capture_dashboard_screenshots.py
```

截图使用默认 2 户 5 人、120 步配置，视口宽度 1600px。
当前成员的 `social_capital` 缺失，生境图会如实显示“缺失维度”，不会伪造散点。

Web Network 页由 Plotly 绘制，不需要 `networkx`；`networkx` 只用于 matplotlib
静态图 `plot_family_network()`。截图随仓库版本化，避免外链失效。
