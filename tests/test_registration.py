"""注册链路的回归测试。

回归：``Household`` 在被 ``Environment.add_agent()`` 注册**之前**就 ``add_member()``
时（家庭未传 environment），成员不会进入 ``env.agents`` —— 于是**静默地永不步进**
（年龄不变、状态冻结、家庭压力源恒为初始值），且全程无任何报错。
正确性此前只靠"恰好先 add_agent 再 add_member"这条未声明的调用顺序维系。

由此引出两条必须钉住的性质：
1. 两种构建顺序都必须让成员真正步进；
2. 两种构建顺序必须产生**逐点一致**的结果——否则"修好了能跑"却引入了
   第二种隐式语义，可复现性承诺就形同虚设。

另含**生命周期时间**的回归（见文件末尾）：年龄推进必须与调度器的激活选择
解耦——否则 ``random_activation`` 下未被激活的成员年龄停滞，同一仿真内
不同成员的"生命时间"互不相同，而记录的时间轴仍逐格递增。
"""
from __future__ import annotations

from family_abm import Environment, FamilyMember, Household, Scheduler, Simulation, StateRecorder

STATE_COLS = ["state_health", "state_stress", "state_happiness", "state_income", "state_influence_received"]


def _build(order: str, seed: int = 42, steps: int = 24):
    """按指定顺序构建同一份仿真。order ∈ {"recommended", "legacy"}。"""
    env = Environment()
    sim = Simulation(env, scheduler=Scheduler("sequential"), seed=seed)
    hh = Household(name="Smith", environment=env) if order == "recommended" else Household(name="Smith")
    members = [
        FamilyMember(name="Father", age=40, role_name="parent", environment=env),
        FamilyMember(name="Child", age=10, role_name="child", environment=env),
    ]
    if order == "recommended":
        env.add_agent(hh)
        for m in members:
            hh.add_member(m)
    else:
        # 家庭未接入环境就先加成员：修复前这条路径下成员永不注册
        for m in members:
            hh.add_member(m)
        env.add_agent(hh)

    recorder = StateRecorder(record_agents=True)
    sim.add_recorder(recorder)
    sim.run(steps)
    return env, hh, members, recorder.to_dataframe()


def _signature(df):
    """与 uuid 无关的确定性签名（NaN 规整为 None，否则比较恒为 False）。"""
    ordered = df.sort_values(["time", "attr_name"]).reset_index(drop=True)
    rows = []
    for _, row in ordered.iterrows():
        values = tuple(None if row[c] != row[c] else round(float(row[c]), 12) for c in STATE_COLS)
        rows.append((int(row["time"]), str(row["agent_type"]), str(row.get("attr_name")), *values))
    return rows


def test_members_are_registered_regardless_of_build_order() -> None:
    """先 add_member 后 add_agent，成员也必须进入环境并真正步进。"""
    for order in ("recommended", "legacy"):
        env, hh, members, df = _build(order, steps=24)
        assert hh.id in env.agents, f"[{order}] 家庭未注册进环境"
        for m in members:
            assert m.id in env.agents, f"[{order}] 成员 {m.get_attribute('name')} 未注册进环境，将永不步进"
            assert m.environment is env, f"[{order}] 成员未接入环境"
            assert m.get_attribute("age") > 40 - 30, f"[{order}] 成员年龄未推进"
        father = members[0]
        # 24 步（月）= 2 年：40 岁应长到 42 岁
        assert abs(father.get_attribute("age") - 42.0) < 1e-9, (
            f"[{order}] 成员没有步进：age={father.get_attribute('age')}（修复前该值恒为初始年龄）"
        )
        member_rows = df[(df["agent_type"] == "FamilyMember") & (df["time"] == 24)]
        assert len(member_rows) == len(members), f"[{order}] 成员状态未被记录"


def test_build_order_does_not_change_results() -> None:
    """两种构建顺序必须产生逐点一致的结果（否则修好注册却引入了新语义分叉）。"""
    sig_recommended = _signature(_build("recommended")[3])
    sig_legacy = _signature(_build("legacy")[3])
    assert sig_recommended == sig_legacy, "构建顺序改变了仿真结果——两条路径的随机流或步进顺序仍不一致"


def test_removing_household_also_unregisters_members() -> None:
    """注销家庭时成员必须一并注销（与收养对称），否则会留下脱离家庭却照常步进的成员。"""
    env, hh, members, _ = _build("recommended", steps=1)
    env.remove_agent(hh.id)
    for m in members:
        assert m.id not in env.agents, "家庭注销后其成员仍留在环境中"
        assert m.environment is None, "家庭注销后成员仍挂着 environment"
    assert hh.id not in env.agents


def test_remove_member_still_works_in_isolation() -> None:
    """单个成员的移除路径不受收养逻辑影响。"""
    env, hh, members, _ = _build("recommended", steps=1)
    victim = members[0]
    hh.remove_member(victim.id)
    assert victim.id not in env.agents
    assert victim.id not in hh.members
    assert members[1].id in env.agents, "移除一个成员不应波及其它成员"


# ── 生命周期时间：年龄推进与调度激活解耦 ────────────────────────────────


def _ages_by_name(env):
    return {
        a.get_attribute("name"): a.get_attribute("age")
        for a in env.get_agents()
        if isinstance(a, FamilyMember)
    }


def _build_ages(method: str, steps: int, seed: int = 42):
    """构建一个家庭并跑指定调度器，返回 (初始年龄表, 结束年龄表)。"""
    env = Environment()
    sim = Simulation(env, scheduler=Scheduler(method), seed=seed)
    hh = Household(name="Smith", environment=env)
    env.add_agent(hh)
    hh.add_member(FamilyMember(name="Father", age=40, role_name="parent",
                               agent_id="father", environment=env))
    hh.add_member(FamilyMember(name="Child", age=6, role_name="child",
                               agent_id="child", environment=env))
    before = _ages_by_name(env)
    sim.run(steps)
    return before, _ages_by_name(env)


def test_age_advances_for_every_living_member_under_random_activation() -> None:
    """``random_activation`` 只激活部分智能体，但**所有人都必须变老**。

    修复前年龄在 ``FamilyMember.step()`` 末尾推进，而 step 只在被激活时调用，
    于是 60 步（名义 5 年）后各成员只长了约 2.0–2.7 岁，且**彼此不同**。
    """
    steps = 60
    before, after = _build_ages("random_activation", steps)
    for name, start in before.items():
        gain = after[name] - start
        assert abs(gain - steps / 12) < 1e-9, (
            f"{name} 的年龄增量 {gain:.4f} 年 != {steps / 12:.4f} 年"
            "——年龄推进仍取决于本步是否被激活"
        )


def test_age_gain_is_identical_across_schedulers() -> None:
    """三种调度器下年龄增量必须完全一致：时间流逝不该随调度方式改变。"""
    steps = 60
    expected = steps / 12
    gains = {}
    for method in ("sequential", "random", "random_activation"):
        before, after = _build_ages(method, steps)
        gains[method] = {name: after[name] - before[name] for name in before}
        for name, gain in gains[method].items():
            assert abs(gain - expected) < 1e-9, f"[{method}] {name} 年龄增量 {gain:.6f} != {expected:.6f}"
    assert gains["sequential"] == gains["random_activation"], (
        "不同调度器下年龄增量不同——成员间的生命时间不再同步"
    )


def test_sequential_scheduler_regression_guard() -> None:
    """``sequential`` 与 ``random`` 会激活全部智能体，年龄增量必须**逐位相同**。

    这条锁住一个易犯的错误：把 ``advance_time()`` 误放进"被激活才调用"的分支。
    只要两者出现任何差异，就说明时间推进又被耦合回了激活选择。
    """
    seq = _build_ages("sequential", 24)
    rnd = _build_ages("random", 24)
    seq_gain = {n: seq[1][n] - seq[0][n] for n in seq[0]}
    rnd_gain = {n: rnd[1][n] - rnd[0][n] for n in rnd[0]}
    assert seq_gain == rnd_gain, f"sequential 与 random 的年龄增量不同：{seq_gain} vs {rnd_gain}"


def test_simulation_time_axis_matches_age_progress() -> None:
    """记录的时间轴（月）必须等于年龄推进（月），否则以时间为轴的拟合失去意义。"""
    steps = 36
    env = Environment()
    sim = Simulation(env, scheduler=Scheduler("random_activation"), seed=7)
    hh = Household(name="Smith", environment=env)
    env.add_agent(hh)
    hh.add_member(FamilyMember(name="Child", age=6, role_name="child",
                               agent_id="child", environment=env))
    before = _ages_by_name(env)["Child"]
    recorder = StateRecorder(record_agents=True)
    sim.add_recorder(recorder)
    sim.run(steps)
    df = recorder.to_dataframe()
    child = df[df["attr_name"] == "Child"].sort_values("time")
    last_time = float(child["time"].iloc[-1])
    age_gain_months = (_ages_by_name(env)["Child"] - before) * 12
    assert abs(age_gain_months - last_time) < 1e-9, (
        f"时间轴 {last_time} 个月 != 年龄推进 {age_gain_months:.6f} 个月"
    )


def test_advance_time_is_noop_for_agents_without_lifecycle() -> None:
    """没有生命周期语义的智能体（如 Household）继承空实现，不因新契约报错。"""
    env = Environment()
    sim = Simulation(env, scheduler=Scheduler("sequential"), seed=42)
    hh = Household(name="Smith", environment=env)
    env.add_agent(hh)
    sim.run(5)  # 不应抛 NotImplementedError
    assert hh.get_attribute("name") == "Smith"
