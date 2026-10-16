"""注册链路的回归测试。

回归：``Household`` 在被 ``Environment.add_agent()`` 注册**之前**就 ``add_member()``
时（家庭未传 environment），成员不会进入 ``env.agents`` —— 于是**静默地永不步进**
（年龄不变、状态冻结、家庭压力源恒为初始值），且全程无任何报错。
正确性此前只靠"恰好先 add_agent 再 add_member"这条未声明的调用顺序维系。

由此引出两条必须钉住的性质：
1. 两种构建顺序都必须让成员真正步进；
2. 两种构建顺序必须产生**逐点一致**的结果——否则"修好了能跑"却引入了
   第二种隐式语义，可复现性承诺就形同虚设。
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
