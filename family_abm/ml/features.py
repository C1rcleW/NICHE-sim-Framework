from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .recorder import StateRecorder


class FeatureExtractor:
    def __init__(self, recorder: StateRecorder):
        self.recorder = recorder

    def build_agent_panel(self) -> pd.DataFrame:
        return self.recorder.to_dataframe()

    def build_agent_trajectories(self, agent_id: str | None = None) -> pd.DataFrame:
        df = self.build_agent_panel()
        if agent_id is not None:
            df = df[df["agent_id"] == agent_id]
        return df.sort_values(["agent_id", "time"])

    def extract_features(
        self,
        feature_columns: list[str] | None = None,
        target_column: str | None = None,
        lag_steps: int = 1,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """构造监督学习用的 (X, y)。

        **缺失值契约**：不填 0。宽表里的 ``NaN`` 表达"该 agent 类型没有这个状态"
        （Household 没有 ``state_happiness``，FamilyMember 没有 ``state_total_income``），
        填 0 会把"不存在"伪造成真实观测值——这正是 recorder 在 ``to_dataframe``
        中刻意保留 NaN、fitter 依赖 ``groupby.mean()`` 跳过 NaN 的原因。

        因此这里按 **完整案例** 过滤：任一特征列或目标列为 ``NaN`` 的行被丢弃，
        X 与 y 用同一掩码对齐。附带效果：

        - 选择成员状态列时，Household 行自然被排除（它本就没有这些状态）；
        - 滞后目标（``shift(-lag_steps)``）使每个 agent 轨迹尾部 ``lag_steps`` 行
          的未来值为 ``NaN``，这些行同样被丢弃，而不是伪造成目标 0。

        行序按 ``(agent_id, time)`` 排序，保证 ``groupby('agent_id').shift`` 的
        组内顺序即时间顺序。全部被过滤时返回形状 ``(0, n_features)`` 的空数组。
        """
        df = self.build_agent_panel()
        if df.empty:
            return np.array([]), None

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if "time" in numeric_cols:
            numeric_cols.remove("time")
        feature_cols = feature_columns or numeric_cols

        df = df.sort_values(["agent_id", "time"])
        frame = df.loc[:, feature_cols]
        valid = frame.notna().all(axis=1)
        y = None
        if target_column and target_column in df.columns:
            y = df.groupby("agent_id", sort=False)[target_column].shift(-lag_steps)
            valid = valid & y.notna()
            y_array = y[valid].to_numpy()
        else:
            y_array = None

        X = frame[valid].to_numpy()
        if y_array is None:
            return X, None
        return X, y_array

    def build_transition_dataset(
        self,
        state_columns: list[str] | None = None,
        lag: int = 1,
    ) -> pd.DataFrame:
        df = self.build_agent_panel()
        if df.empty:
            return pd.DataFrame()

        state_cols = state_columns or [c for c in df.columns if c.startswith("state_")]
        records = []
        for agent_id, group in df.groupby("agent_id"):
            group = group.sort_values("time")
            for i in range(len(group) - lag):
                source = group.iloc[i]
                target = group.iloc[i + lag]
                row: dict[str, Any] = {}
                for col in state_cols:
                    row[f"{col}_t"] = source[col]
                    row[f"{col}_t+{lag}"] = target[col]
                row["agent_id"] = agent_id
                row["time"] = source["time"]
                records.append(row)
        return pd.DataFrame(records)

    def build_network_features(self, agent_id: str | None = None) -> pd.DataFrame:
        df = self.build_agent_panel()
        if df.empty:
            return pd.DataFrame()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if "time" in numeric_cols:
            numeric_cols.remove("time")
        grouped = df.groupby("agent_id")[numeric_cols].agg(["mean", "std", "min", "max"])
        grouped.columns = ["_".join(col).strip() for col in grouped.columns.values]
        return grouped.reset_index()
