# 变更日志

本项目的所有重要变更都记录在此文件。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。
`0.x` 阶段的次版本号可能包含不兼容改动。

## [Unreleased]

### 修正

**实验结果与文档数字重新固化（round-2 审查 E-01）**

审查发现三份结果文件全部与当前代码不一致：以各脚本默认参数重跑，E2/E3/E4 的
随机量逐点偏移、可约性的 C1 由 0.674 掉到 0.518、敏感性分析的 **P2 tally 由
25/25 变为 24/25**。README 与设计文档引用的每一个数字都无法由当前代码复现，
其中「五条结论在 25–75 个组合下全部成立」当时已是假话——而且没有任何测试会
因此失败。现已全部重跑固化，并把数字改为**派生**：

- 新增 `tools/export_experiment_tables.py`：从 `experiments/results/*.json` 生成
  `docs/experiments.md`（含 E1–E4 明细、敏感性 tally、可约性对照），带 `--check`。
- `tools/build_research_doc.py` 第六、七、八章的数字改为从结果 JSON 读取，
  不再手写。设计文档据此重建。
- 新增 `tests/test_experiment_numbers.py`（8 项）：强制派生文件与结果 JSON 一致、
  README 引用的关键数字与结果一致、**存在未满 tally 时必须如实说明"并非全部成立"**、
  结果文件必须记录 seeds/steps。已用 4 个突变体验证判别力（4/4 被抓住）。

**受此影响，以下结论的表述被修正**：

- **敏感性分析**：P2「效力比随阶段单调递减」在 6 种子下为 **19/25**、
  P3 为 **24/25**——并非全部成立。此前文档写的 25/25 是 3 种子采样不足造成的虚高
  （`paired_noise` 用系综内标准差，小 n 低估噪声、放大信噪比）。P1/P4/P5 仍为
  25/25、25/25、75/75。
- **结果基线现在显式声明种子数与步数**（机制验证与敏感性分析均为 6 种子、300 步）。
  随机量的数值只在该种子数下成立。
- E2 效力比 `1.139 → 0.838 → 0.026 → 0.015`（原文档 1.128/0.833/0.026/0.017）；
  E3 无钳位区信噪比 4.61–3.57（原 4.81–3.73）；
  E4 成年后信噪比 3.10、衰减比 6.6%（原 3.53、6.7%）；
  可约性全窗口 R² 0.383–0.897（原 0.378/0.674）。

**时间与调度语义**

- **年龄推进与调度激活解耦**。此前 `age_increment` 写在 `FamilyMember.step()` 末尾，
  而 `step()` 只在被调度器激活时调用——`random_activation` 下未被激活的成员**连年龄
  都停滞**：60 步（名义 5 年）后各成员只长了 2.0–2.7 岁，而且**每个人都不一样**，
  同一仿真内成员的"生命时间"彼此失同步；记录的时间轴却仍按 `Environment.time`
  逐格递增，以时间为轴的拟合与图表因此失去可比性。
  现新增 `Agent.advance_time()`（默认空实现，`FamilyMember` 覆写为按 `dt_months`
  推进年龄），由调度器在**选择激活子集之前**对每个存活智能体调用。修复后三种
  调度器下 N 步的年龄增量都恰好是 `N/12` 年，且时间轴与年龄推进严格相等。
  附带影响：`sequential`/`random` 会激活全部智能体，其行为不变，仅年龄时序前移
  一个月（状态统计量的漂移约 1e-4 量级），基线已相应重固化。

**可复现性**

- `influence.py` 去掉 `float(x.get(k, d) or d)` 的 `or` 零值兜底：它会把显式设为 0
  的参数静默改写回默认值——`susceptibility_scale=0`（完全关闭易感性的消融条件）
  被改成 1.0，来源 `health=0` 被 `or 1.0` 当作满血使能量约束失效。
- 关系随机流的派生元组由 `(seed, 双方身份, 关系类型)` 改为
  `(seed, 所属容器的环境内序号, 双方标签, 关系类型)`：原名只用家庭显示名，导致
  **同名家庭（含默认名）拿到完全相同的随机流**，跨家庭状态系统性相关、污染家庭
  层面的方差分析；同时 `relation_type` 此前并未真正参与派生（与 docstring 不符）。
- `Environment.add_agent()` 收养容器型智能体已持有的成员，`remove_agent()` 对称注销。
  此前成员若在家庭注册前 `add_member()`，会**静默地永不步进**（年龄不变、状态冻结）
  且无任何报错。

**语义正确性**

- `FamilyMember` 分离"声明的家庭角色"与"按年龄推导的生命阶段"：`role_name`
  （`parent`/`child`/…，UI 与文档的词表）此前被直接置入 `role`，而收入乘数的词表是
  生命阶段（`preschool`/`child`/…），声明 `"parent"` 的成员第一步落进 `.get(role, 0.2)`
  兜底乘数、第二步又被年龄派生值静默覆盖。现 `role` 仅作声明值，动力学按 `age`
  实时推导阶段，且改为**直接索引**——词表漂移会立刻报错而非静默兜底。
- `FeatureExtractor.extract_features()` 不再用 0 填充缺失。宽表中的 `NaN` 表示
  "该 agent 类型没有这个状态"（`Household` 无 `state_happiness`，`FamilyMember` 无
  `state_total_income`），`fillna(0)` 把"不存在"伪造成真实观测：实测 847 条标签中
  247 条（29.16%）是伪造的 0，且全部是"没有下一步"的行。现按完整案例过滤，
  X/y 用同一掩码对齐，滞后目标尾部同样丢弃。
- `Household.add_member()` 在家庭尚未接入环境时退回**成员自己的** `environment`
  取随机流，避免退回全局 `random` 而破坏带 seed 的可复现性。

### 新增

- `Agent.advance_time()`：智能体自身的"生命时间"推进契约，与 `step()` 的激活选择独立。
- 测试：`tests/test_registration.py` 新增 5 项生命周期用例（年龄增量在三种调度器下
  一致、时间轴与年龄推进相等、无生命周期智能体继承空实现不报错）；
  `test_features_nan.py`（缺失值不再填 0）、`test_experiments.py`
  （实验函数尊重 `--steps`）、`test_examples_smoke.py`（示例可跑）；
  `test_influence.py` / `test_simulation_and_fitting.py` 新增 9 项。
  测试总数 108 → 141。
- `experiments/mechanism_validation.py` 与 `sensitivity_analysis.py` 的
  `e2`/`e3`/`e4` 及敏感性函数接受 `steps` 参数，可经 `--steps` 覆盖
  （含 `MIN_STEPS_FOR_STAGE_COVERAGE` 守卫），便于快速复算。
- `docs/experiments.md`：从结果 JSON 派生的实验数据表（单一真源）。
- `tools/export_experiment_tables.py`：上述派生工具，支持 `--out` / `--check`。
- `tests/test_experiment_numbers.py`：8 项数字一致性检验，含"防回退到
  '全部成立'表述"的回归守卫。

## [0.1.0] — 首个公开版本

首个公开发布。此前仓库内的 `0.2.0` 是开发期版本号，从未对外发布；
`0.1.0` 涵盖全部已完成的工作。

### 新增

**框架核心**

- `Agent` / `Environment` / `Scheduler` / `Simulation` 四层结构，支持顺序、随机与随机激活三种调度
- `StateRecorder` 状态记录，输出宽表 DataFrame；提供 `to_statistics_dataframe()` 分组统计与多级 `to_csv(level=...)`
- 家庭层：`FamilyMember`（成员）、`Household`（家庭）、`Relationship`（关系）、`roles`（角色）
- 小生境层：四维社会空间（经济 / 文化 / 社会 / 情感），支持生境距离与重叠度计算
- ML 接口：状态记录 → 特征提取，输出可直接对接 sklearn / PyTorch

**代际影响机制（`family_abm/family/influence.py`）**

- 影响量 = 影响强度 × 易感性(年龄) × Σ(关系权重 × 来源养育能力 × 来源健康) × 状态差距
- 易感性随埃里克森心理社会发展阶段阶梯下降，阶段边界线性过渡（避免人为的动力学间断）
- 子代跨过成年阈值后由"接受影响"转为"施加影响"，并获得初始养育能力——代际更新内生发生
- 关系权重复用 `Relationship.influence_weight()`（信任 / 权力 / 情感）并扣除冲突
- 来源健康作为能量约束；影响按受影响的未成年成员数分摊

**家庭经济压力**

- `Household.total_income` 从"只写不读"变为共同压力源：人均收入低于基准时产生压力，成员各自读取
- 年幼成员对家庭处境更敏感（对应家庭压力模型的核心预测）

**可复现性**

- `Simulation(seed=...)` 注入独立随机流；默认 `seed=42`，**不传 seed 也可复现**
- 关系变量的随机流按 `(seed, 双方身份, 关系类型)` 派生，关系之间互不干扰、不依赖迭代顺序
- 实测：同一 seed 跨进程逐点一致；全局 `random` 被污染后结果不变

**ODE 拟合**

- 7 种兰彻斯特型社会动力学模型：`square_law`、`linear_law`、`influence`、`wellbeing`、`logistic`、`lotka_volterra`、`resource_competition`
- 多起点鲁棒优化（`fit_robust`）与差分进化全局搜索（`fit_global`）
- 失败路径显式化：哨兵解、参数贴边、R² 为负均有结构化输出与告警

**Web 仪表板**

- FastAPI + Plotly.js，中英双语，覆盖仿真配置 / 运行 / 拟合 / 可视化的全流程
- `GET /api/models` 提供状态列方差报告（可用 / 常量 / 不可验证），避免把常量列当拟合目标
- 页面可调 27 个动力学参数，含两个政策杠杆（`influence_strength`、`income_support`）

**研究实验（`experiments/`）**

- `mechanism_validation.py` 四项可证伪检验：E1 易感性阶段结构、E2 效力随阶段递减、E3 剂量-反应与适用边界、E4 成年后滞后效应
- `sensitivity_analysis.py` 参数敏感性：五条结论在 25–75 个参数组合下全部成立
- `life_stage_reducibility.py` 可约性实验（结果是否定的，见下）

**文档与工程**

- `README.md`（使用指南与限制）、`CONTRIBUTING.md`、`LICENSE`（MIT）
- `docs/研究设计文档.docx` 与派生的 `docs/研究设计.md`：理论框架、检验设计、政策意涵
- GitHub Actions CI：lint、测试（3.10 / 3.12 / 3.13 / Windows）、打包与安装冒烟
- 基线快照 `baseline/default_seed42.json`：默认行为的任何改动都会显式暴露
- 106+ 项自动化检验，含可复现性、数据契约、打包、文档一致性

### 修正

**仿真语义**

- 时间轴由 `[1..n]` 改为 `[0..n]`：在首次步进前记录 t=0 基线，使 ODE 拟合的初值正确（此前整条轨迹相差一步）
- 健康衰减由无下界的线性衰减（40 岁时约 7.8%/年，十余年触底 0.01）改为朝下限渐近并受年龄加速
- 教育对健康的作用此前只乘在年龄项上，对基础衰减无效；现作用于总衰减
- 压力平衡点此前算出 > 1 被钳位饱和，导致神经质人格在高区间完全失效；下调基础值后稳态约 0.31–0.37

**正确性**

- 关系状态此前依赖迭代顺序（排序键是 `uuid4()`），导致同一 seed 不可复现
- `apply_influence` 在 `sigma=0` 时仍调用 `rng.gauss`，无效消耗随机数状态并使关系随机游走错位
- 养育存量衰减曾误乘 `strength`，使强度 ≥2 时衰减因子变负、机制实际未生效
- `income_support` 曾加到"收入基准"上，导致支持越多、测得的压力越大（方向相反）

**错误契约与界面**

- `wellbeing` 等抽象模型的状态名与 ABM 列名无默认对应；改为显式 `state_mapping` 并给出候选提示
- 哨兵解判定移到 `predict` 之前：此前返回 500 `prediction_failed`，现返回 200 + `model_not_applicable`
- 恢复函数级兜底 `except`：此前异常逃逸为 `text/plain`，前端无法解析
- 前端 `|| 0` 把缺失值伪造成 0；改为保留 `null`
- 前端补 `_modelInfoSeq` 竞态防护与切换 agent 时的重新加载

**打包**

- wheel 曾缺少 `web/templates` 与 `web/static`，非 editable 安装后 `import family_abm.web` 抛 `RuntimeError`
- 依赖声明曾分散在 `setup.py` / `requirements.txt` / `pyproject.toml` 三处且不一致；现以 `pyproject.toml` 为唯一真源
- 从索引中移除误纳入的 `__pycache__/*.pyc` 与 `egg-info`

### 已知限制

**方法层面**

- 本研究是方法性探索，**不是政策效果评估**，不提供任何因果效应估计
- 模型行为未与家庭追踪数据比对，输出的绝对水平没有经验意义，只有结构性对比有意义
- 易感性的阶段取值、阶段年龄边界、影响强度均来自理论解读而非实证测量；定性结论已通过敏感性分析证明稳健，但定量门槛依赖参数

**模型层面**

- 影响是**单向下行**的：只实现"年长成员影响年幼成员"；成年子代虽转为施加影响一方，但缺乏作用对象；配偶互影响、同伴影响均未建模
- 高影响强度下机制失效：强度 ≥ 8 时子代幸福有超过一半时间步触及取值边界，剂量-反应关系不再可信（实测可信上限为 4）
- 健康动态缺乏实证标定；家庭结构同质（主要实验为三代同堂的完整家庭）
- 小生境空间维度不完整：`social` 依赖 `social_capital`（仅 `Household` 拥有），`economic` 未归一化
- `FeatureExtractor` 的缺失值处理用 0 填充，用于监督学习前需自行处理

**一个否定的结果**

- 含有时变影响系数的家庭聚合动力学**无法**被单一常系数微分方程刻画。已排除工具问题（拟合器对自生成数据 R²=1.00000），差距来自模型结构与动力学的错配而非机制效应

### 移除

- **Python 3.9 支持**：Pydantic 在类创建时求值注解，`X | None` 需要运行时的 `|` 支持。Python 3.9 已于 2025-10 终止支持，因此最低版本提升至 3.10

### 工程与 CI 修正

首次 CI 运行有 3 个 job 失败，均已修复：

- **静态检查**：ruff 使用了浮动版本且规则集为隐式默认。0.15→0.17 让本项目多出 179 项告警。现钉 `ruff==0.17.0` 并显式声明 `[tool.ruff.lint] select`
- **打包冒烟**：CI 调用 `verify_install.py` 时缺少 `--import-only`，脚本直接退出 2
- **Windows 测试**：平台敏感的构建/安装测试加 `packaging` 标记，由专门的 package job 执行

---

## 版本说明

- `0.1.0` 的 API 尚未稳定，次版本号可能包含不兼容改动
- 报告问题请附操作系统与依赖版本、最小复现脚本（含随机种子）；数值问题请附 `python tools/baseline.py --check` 的差异输出

[0.1.0]: https://github.com/C1rcleW/NICHE-sim-Framework/releases/tag/v0.1.0
