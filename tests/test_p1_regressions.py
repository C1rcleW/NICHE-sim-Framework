"""0.1.3 工程补丁回归：关系种子独立、成员注销对称、生境维度对齐、Plotly 本地化。

这些测试只验证缺陷修复，不改变默认模型行为;默认基线由
tools/baseline.py --check 单独守卫。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from family_abm import Environment, FamilyMember, Household, Simulation
from family_abm.niche.micro_niche import MicroNiche

REPO = Path(__file__).resolve().parent.parent


def _household_with_members(seed: int = 42):
    env = Environment()
    Simulation(env, seed=seed)
    hh = Household(name="H", environment=env)
    env.add_agent(hh)
    members = [
        FamilyMember(name=n, age=a, environment=env)
        for n, a in [("A", 30), ("B", 28), ("C", 6)]
    ]
    for m in members:
        hh.add_member(m)
    return env, hh, members


def _sample(rel, n: int = 5):
    return [rel.rng.random() for _ in range(n)]


def test_relationship_streams_stay_independent_after_remove_and_readd() -> None:
    env, hh, (a, b, c) = _household_with_members()
    rel_ac = hh.get_relationship(a.id, c.id)

    hh.remove_member(b.id)
    d = FamilyMember(name="D", age=4, environment=env)
    hh.add_member(d)

    rel_ad = hh.get_relationship(a.id, d.id)
    rel_cd = hh.get_relationship(c.id, d.id)
    assert rel_ad is not None and rel_cd is not None and rel_ac is not None
    # 三条不同关系必须持有互不相同的随机流（修复前重加成员会复用旧序号导致串流）。
    assert _sample(rel_ad) != _sample(rel_cd)
    assert _sample(rel_ad) != _sample(rel_ac)
    assert _sample(rel_cd) != _sample(rel_ac)
    # 被移除成员的关系应已清理。
    assert hh.get_relationship(a.id, b.id) is None


def test_default_member_labels_unchanged() -> None:
    # 无移除/重加时，固定序号与旧的“当前加入序号”一致，保证默认基线不变。
    _, hh, (a, b, c) = _household_with_members()
    assert hh._member_label(a.id) == "H#0"
    assert hh._member_label(b.id) == "H#1"
    assert hh._member_label(c.id) == "H#2"


def test_environment_remove_member_cleans_household() -> None:
    env, hh, (a, _b, _c) = _household_with_members()
    env.remove_agent(a.id)
    assert a.id not in env.agents
    assert a.id not in hh.members
    assert all(a.id not in key for key in hh.relationships)
    # 家庭聚合不再包含已注销成员。
    hh.step()
    assert hh.get_state_value("total_income") == pytest.approx(
        sum(m.get_state_value("income", 0.0) for m in hh.members.values())
    )


def test_niche_distance_aligns_by_dimension_name() -> None:
    dims = ["economic", "cultural", "social", "emotional"]
    values = {"economic": 0.2, "cultural": 0.4, "social": 0.6, "emotional": 0.8}
    n1 = MicroNiche("x", dims)
    n2 = MicroNiche("y", list(reversed(dims)))
    for d, v in values.items():
        n1.set_position(d, v)
        n2.set_position(d, v)
    # 坐标相同、仅声明顺序不同 -> 距离必须为 0。
    assert n1.distance_to(n2) == pytest.approx(0.0)
    assert n1.overlap(n2) == pytest.approx(1.0)


def test_niche_distance_rejects_mismatched_dimension_sets() -> None:
    n1 = MicroNiche("x", ["economic", "cultural"])
    n2 = MicroNiche("y", ["economic"])
    with pytest.raises(ValueError, match="维度集不同"):
        n1.distance_to(n2)


def test_plotly_is_self_hosted() -> None:
    index = (REPO / "family_abm" / "web" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/static/vendor/plotly-2.32.0.min.js" in index
    assert "cdn.plot.ly" not in index
    vendor = REPO / "family_abm" / "web" / "static" / "vendor" / "plotly-2.32.0.min.js"
    assert vendor.is_file() and vendor.stat().st_size > 1_000_000
    # 校验版本头，防止损坏/错版文件假绿。
    head = vendor.read_text(encoding="utf-8", errors="replace")[:2000]
    assert "2.32.0" in head
    # MIT 要求捆绑许可随副本分发。
    license_file = vendor.with_name(vendor.name + ".LICENSE.txt")
    assert license_file.is_file() and license_file.stat().st_size > 0


def test_remove_member_cleans_all_referencing_households() -> None:
    env = Environment()
    Simulation(env, seed=1)
    h1 = Household(name="H1", environment=env)
    h2 = Household(name="H2", environment=env)
    env.add_agent(h1)
    env.add_agent(h2)
    m = FamilyMember(name="M", age=30, environment=env)
    h1.add_member(m)
    h2.add_member(m)
    env.remove_agent(m.id)
    assert m.id not in env.agents
    assert m.id not in h1.members
    assert m.id not in h2.members
    assert all(m.id not in key for key in h1.relationships)
    assert all(m.id not in key for key in h2.relationships)
