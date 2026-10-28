## 研究问题

家庭内部的代际影响强度随子代发展阶段系统性下降。这种变化如何影响子代的长期结果？
含有时变影响系数的家庭动力学，能否被低维方程刻画？

## 验证结果

结果基线：6 个种子（1000–1005）、300 步。
**随机量的数值只在该种子数下成立**——配对噪声用系综内标准差估计，小 n 会低估噪声、放大信噪比。

| 检验 | 结论 |
|---|---|
| E1 易感性阶段结构 | 单调性违例 0 次；阶段边界跳变 2.5e-05（连续） |
| E2 效力随阶段递减 | 1.139 → 0.838 → 0.026 → 0.015（学前期 → 成年早期） |
| E3 剂量-反应 | 无钳位区间内单调，信噪比 3.57–4.61；**可信强度上限为 4**，超过后状态触界使结论失效 |
| E4 成年后滞后效应 | 仍可分辨（信噪比 3.10），但衰减至童年期的 6.6% |

参数敏感性（25–75 个组合）：

| 结论 | 稳健组合数 | 判定 |
|---|---|---|
| P1 易感性阶梯单调且连续 | 25/25 | 稳健 |
| P2 效力比随阶段单调递减 | 19/25 | **不稳健** |
| P3 易感性<0.5 阶段影响更弱 | 24/25 | **不稳健** |
| P4 剂量-反应单调且信噪比>2 | 25/25 | 稳健 |
| P5 成年后留痕 | 75/75 | 稳健 |

扰动参数不改变机制的结构性结论，只改变适用边界的数值位置
（可信强度上限在 2–8 之间移动）。

## 已知限制

本工作是**方法性探索，不是政策效果评估**，不提供因果效应估计。

- 影响是**单向下行**的：只实现"年长成员影响年幼成员"，配偶互影响、同伴影响未建模
- 参数部分来自理论解读而非实证测量；定性结论已通过敏感性分析证明稳健，
  但定量门槛依赖参数
- **一个否定的结果**：含有时变影响系数的家庭聚合动力学，无法被单一常系数
  微分方程刻画

完整清单见 [README 的「说明与限制」](https://github.com/C1rcleW/NICHE-sim-Framework#说明与限制)
与 [CHANGELOG](https://github.com/C1rcleW/NICHE-sim-Framework/blob/main/CHANGELOG.md)。

## 安装

下载下方附件中的 wheel 后：

```bash
pip install family_abm-0.1.1-py3-none-any.whl
python -m family_abm.web      # 启动仪表板 → http://127.0.0.1:8520
```

要求 Python >= 3.10；MIT 许可。

---

## 完整变更

第二个公开发布。本版把 round-2 审查（5 条流水线、93 条发现）中已确认的问题修完，
并修掉了三处「静默产出错误结论」的缺陷。

### 修正

**Web 契约与可用性**

- **`/api/models` 的映射不再不可见**。抽象模型（`square_law`/`logistic`/`lotka_volterra` 等）
  的原生状态名与 ABM 列没有语义对应，此前后端从可用列里**按字母序任取**替代品并自动
  提交给 `/api/fit`：实测 6 个抽象模型全部映射到 `state_economic_pressure` +
  `state_education`，返回 `status=ok` 且 `converged=true`，而 R² 低至 −2368436，
  界面又从不显示究竟拟合了哪两列（后端返回的 `state_columns` 前端 0 处引用）。
  现在：新增 `mapping_kind`（`default`/`auto`/`none`）显式区分原生映射与自动替代；
  选项文案区分两者；结果卡片显示实际使用的状态列；自动映射给出显式告警；
  **R² 非正时不再把 `Converged` 作为独立"通过"指标并排展示**。
- **四个端点补上函数级兜底**（`/api/run`、`/api/data`、`/api/niche`、`/api/network`）。
  此前只有 `/api/fit` 有兜底，其余端点一旦抛异常就返回 FastAPI 默认的
  `text/plain "Internal Server Error"`——前端 `res.json()` 解析失败、HTTP 状态码
  也丢失，用户只看到一句 JSON 语法错误。现与 `/api/fit` 同一契约：
  `ValueError → 400 {'error','status':'invalid_input'}`、其它异常 →
  `500 {'error','status':'internal_error'}` 并把完整 traceback 写进 logging。
- **`/api/fit` 不再阻塞整个服务**。此前 CPU 密集的拟合在事件循环内同步执行，
  实测一次 `wellbeing robust=True` 拟合耗时 38.39 秒，期间 `GET /api/params`
  延迟 **37.39 秒**（整个单进程不可用）。现改为 `asyncio.to_thread` 执行并加超时保护
  （默认 120 秒，可用 `FAMILY_ABM_FIT_TIMEOUT_SECONDS` 覆盖），超时返回结构化 504。
  实测：拟合 30.3 秒期间轮询 `/api/params` 572 次全部 200，**最大延迟 0.029 秒**。

**输入校验（把错误从"仿真深处"前移到"请求入口"）**

- `SimConfig.families` 由 `list[dict]` 改为类型化的 `FamilyConfig`/`MemberConfig`，
  `params` 由 `dict` 改为 `dict[str, float]`，并启用 `allow_inf_nan=False`。
  此前 `age=NaN` 会被接受（`json.loads` 允许 NaN 字面量，而 `allow_inf_nan`
  对 `dict` 字段不递归），一路进仿真，10 步之后才表现为 `/api/data` 的错误；
  实测 6 个反例现在全部在校验层返回 **422**（而不是 500/400 或 text/plain）。
- 新增 422 处理器：Pydantic 的校验详情会回显输入值与异常对象，含 `nan`/`inf`
  或 `ValueError` 对象时**无法序列化**，会让 FastAPI 在生成响应时自己抛错
  （错误处理变成故障）。现对每个字段做试探性序列化，不可序列化的降级为字符串。
- 拒绝必然导致崩溃的参数：`income_age_spread <= 0`（收入年龄曲线的分母）、
  `steps < 0`、`age` 超出 0–120。

**其它**

- `/openapi.json` 报告的版本号由硬编码的 `0.2.0` 改为从包元数据读取（与
  `pyproject.toml` 单一真源一致）。
- 拟合器补齐数值入口校验：`p0` 含 NaN/Inf 或长度不符、bounds 非有限或下界>上界、
  数据含非有限值，均返回明确错误而不是让 `solve_ivp` 挂死或产出非法 JSON。

**实验结果与文档数字重新固化**

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
  发布时非 packaging 测试 160 项，另有 16 项 packaging 测试。
- `experiments/mechanism_validation.py` 与 `sensitivity_analysis.py` 的
  `e2`/`e3`/`e4` 及敏感性函数接受 `steps` 参数，可经 `--steps` 覆盖
  （含 `MIN_STEPS_FOR_STAGE_COVERAGE` 守卫），便于快速复算。
- `docs/experiments.md`：从结果 JSON 派生的实验数据表（单一真源）。
- `tools/export_experiment_tables.py`：上述派生工具，支持 `--out` / `--check`。
- `tests/test_experiment_numbers.py`：8 项数字一致性检验，含"防回退到
  '全部成立'表述"的回归守卫。
