"""FeatureExtractor 的缺失值契约测试。

回归对象（P0-7）：``extract_features`` 曾对特征与目标 ``fillna(0)``，
与仓库既定的 NaN 契约（recorder/to_dataframe、fitter、test_data_contract
的 P1-4 修复）直接冲突——

- 特征侧：宽表里 ``NaN`` 表示"该 agent 类型没有这个状态"，填 0 把
  "不存在"伪造成真实观测（Household 的 ``state_happiness`` 会变成 0）；
- 目标侧：``shift(-lag)`` 使每个 agent 轨迹尾部的未来值为 ``NaN``，
  填 0 等于告诉模型"轨迹终点的幸福感是 0"，是伪造的监督信号。

修复策略：完整案例过滤（与 ``to_statistics_dataframe`` 丢弃缺失一致），
X/y 用同一掩码对齐。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from family_abm import StateRecorder
from family_abm.ml.features import FeatureExtractor

MEMBER = "member-1"
HOUSEHOLD = "household-1"


def make_recorder() -> StateRecorder:
    """构造 2 个时间点 × (成员 + 家庭) 的宽表记录。

    成员有 ``state_happiness``/``state_stress``，家庭有 ``state_total_income``；
    对方的状态列一律缺席 → 宽表对齐后为 NaN。
    """
    rec = StateRecorder(record_agents=True, record_environment=False)
    rec.agent_history.extend([
        {"time": 0, "agent_id": MEMBER, "agent_type": "FamilyMember", "alive": True,
         "state_happiness": 0.5, "state_stress": 0.3},
        {"time": 0, "agent_id": HOUSEHOLD, "agent_type": "Household", "alive": True,
         "state_total_income": 1.2},
        {"time": 1, "agent_id": MEMBER, "agent_type": "FamilyMember", "alive": True,
         "state_happiness": 0.6, "state_stress": 0.2},
        {"time": 1, "agent_id": HOUSEHOLD, "agent_type": "Household", "alive": True,
         "state_total_income": 1.3},
    ])
    return rec


def test_empty_panel_returns_empty() -> None:
    X, y = FeatureExtractor(StateRecorder(record_agents=True)).extract_features()
    assert X.size == 0 and y is None


def test_missing_states_are_dropped_not_zero_filled() -> None:
    """Household 没有 state_happiness：行必须被丢弃，不得填 0 混进 X。"""
    extractor = FeatureExtractor(make_recorder())
    X, _y = extractor.extract_features(
        feature_columns=["state_happiness", "state_stress"],
        target_column=None,
    )
    # 4 行里只有 2 行（成员）同时拥有两个特征列
    assert X.shape == (2, 2), f"应只保留完整案例，实际 {X.shape}"
    assert not np.isnan(X).any()
    assert (X[:, 0] > 0).all(), "若出现 0，说明 NaN 又被填成了 0"


def test_household_columns_keep_household_rows() -> None:
    """反向验证：选家庭状态列时保留的是家庭行、丢弃成员行。"""
    extractor = FeatureExtractor(make_recorder())
    X, _ = extractor.extract_features(feature_columns=["state_total_income"])
    assert X.shape == (2, 1)
    np.testing.assert_allclose(X[:, 0], [1.2, 1.3])


def test_lag_target_tail_is_dropped_not_zero() -> None:
    """lag=1 时每个 agent 最后一行没有未来目标：丢弃，不伪造成 y=0。"""
    extractor = FeatureExtractor(make_recorder())
    X, y = extractor.extract_features(
        feature_columns=["state_stress"],
        target_column="state_happiness",
        lag_steps=1,
    )
    # 成员 t=0 → 目标 t=1；成员 t=1 的未来缺失；家庭行全程因特征 NaN 被丢弃
    assert X.shape == (1, 1) and y is not None and y.shape == (1,)
    np.testing.assert_allclose(X[0], [0.3])
    np.testing.assert_allclose(y, [0.6])
    assert not (y == 0).any(), "轨迹尾部不得被伪造成目标 0"


def test_xy_rows_are_aligned() -> None:
    """X/y 必须按同一掩码对齐（同一行的 X 与 y 来自相邻时间点）。"""
    extractor = FeatureExtractor(make_recorder())
    X, y = extractor.extract_features(
        feature_columns=["state_stress"],
        target_column="state_happiness",
        lag_steps=1,
    )
    assert X.shape[0] == y.shape[0] == 1
    # 成员：stress(t=0)=0.3 → happiness(t=1)=0.6
    np.testing.assert_allclose(X[0, 0], 0.3)
    np.testing.assert_allclose(y[0], 0.6)


def test_rows_sorted_by_agent_then_time() -> None:
    """行序按 (agent_id, time) 排序，保证 shift 的组内顺序即时间顺序。"""
    extractor = FeatureExtractor(make_recorder())
    df = extractor.build_agent_panel()
    X, _ = extractor.extract_features(feature_columns=["state_total_income"])
    # 家庭列只出现在 household 行；按 id 排序后 household-1 < member-1
    assert X.shape == (2, 1)
    # 同一 agent 的多行按时间升序
    times = df[df["agent_id"] == HOUSEHOLD].sort_values("time")["time"].tolist()
    assert times == [0, 1]


def test_default_supervised_features_exclude_target_and_other_agent_states() -> None:
    frame = FeatureExtractor(make_recorder()).extract_supervised_frame(
        target_column="state_happiness",
        lag_steps=1,
    )
    assert len(frame) == 1
    assert list(frame[["agent_id", "time"]].iloc[0]) == [MEMBER, 0]
    feature_cols = list(frame.columns[:-1])
    assert "state_happiness" not in feature_cols
    assert "state_total_income" not in feature_cols, "不得混入目标行没有的状态列"
    assert "state_stress" in feature_cols
    assert frame.columns[-1] == "state_happiness"


def test_explicit_feature_columns_reject_target_and_invalid_columns() -> None:
    extractor = FeatureExtractor(make_recorder())
    with pytest.raises(ValueError, match="目标列"):
        extractor.extract_features(
            feature_columns=["state_happiness"],
            target_column="state_happiness",
        )
    with pytest.raises(ValueError, match="不存在"):
        extractor.extract_features(feature_columns=["state_missing"])
    with pytest.raises(ValueError, match="不能为空"):
        extractor.extract_features(feature_columns=[])
    with pytest.raises(ValueError, match="重复列"):
        extractor.extract_features(feature_columns=["state_stress", "state_stress"])


@pytest.mark.parametrize("lag", [0, -1, 1.5, True])
def test_lag_steps_must_be_positive_integer(lag) -> None:
    extractor = FeatureExtractor(make_recorder())
    with pytest.raises(ValueError, match="lag_steps"):
        extractor.extract_features(target_column="state_happiness", lag_steps=lag)
    with pytest.raises(ValueError, match="lag_steps"):
        extractor.build_transition_dataset(lag=lag)


def test_target_column_must_exist_and_be_numeric() -> None:
    extractor = FeatureExtractor(make_recorder())
    with pytest.raises(ValueError, match="不存在"):
        extractor.extract_features(target_column="state_missing")
    with pytest.raises(ValueError, match="必须是数值列"):
        extractor.extract_features(target_column="agent_type")


def test_transition_dataset_has_target_time_and_validates_columns() -> None:
    extractor = FeatureExtractor(make_recorder())
    transitions = extractor.build_transition_dataset(
        state_columns=["state_stress"],
        lag=1,
    )
    assert set(transitions.columns) == {
        "state_stress_t", "state_stress_t+1", "agent_id", "time", "target_time",
    }
    member_row = transitions[transitions["agent_id"] == MEMBER].iloc[0]
    assert member_row["time"] == 0
    assert member_row["target_time"] == 1
    with pytest.raises(ValueError, match="不存在"):
        extractor.build_transition_dataset(state_columns=["state_missing"])


def test_network_features_can_be_limited_to_past_data() -> None:
    recorder = StateRecorder(record_agents=True, record_environment=False)
    recorder.agent_history.extend([
        {"time": t, "agent_id": MEMBER, "agent_type": "FamilyMember", "alive": True,
         "state_happiness": value}
        for t, value in [(0, 0.1), (1, 0.2), (2, 100.0)]
    ])
    extractor = FeatureExtractor(recorder)
    past = extractor.build_network_features(agent_id=MEMBER, up_to_time=1)
    assert len(past) == 1
    assert past["state_happiness_mean"].iloc[0] == pytest.approx(0.15)
    with pytest.raises(ValueError, match="没有 agent_id"):
        extractor.build_network_features(agent_id="missing")


def test_supervised_frame_has_deterministic_time_split() -> None:
    frame = pd.DataFrame({
        "agent_id": ["a"] * 4,
        "time": [0, 1, 2, 3],
        "x": [1, 2, 3, 4],
        "y": [2, 3, 4, 5],
    })
    train, test = FeatureExtractor.split_by_time(frame, test_start_time=2)
    assert train["time"].tolist() == [0, 1]
    assert test["time"].tolist() == [2, 3]
    with pytest.raises(ValueError, match="时间列"):
        FeatureExtractor.split_by_time(frame.drop(columns=["time"]), test_start_time=2)
