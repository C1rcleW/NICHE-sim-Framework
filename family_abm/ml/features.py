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
        if df.empty:
            return df
        if "agent_id" not in df.columns:
            raise ValueError("状态面板缺少 agent_id 列")
        if agent_id is not None:
            df = df[df["agent_id"] == agent_id]
        return df.sort_values(["agent_id", "time"])

    @staticmethod
    def _validate_lag(lag_steps: int) -> int:
        if isinstance(lag_steps, bool) or not isinstance(lag_steps, (int, np.integer)):
            raise ValueError(f"lag_steps 必须是整数，收到 {lag_steps!r}")
        lag = int(lag_steps)
        if lag < 1:
            raise ValueError(f"lag_steps 必须大于 0，收到 {lag}")
        return lag

    def _resolve_feature_columns(
        self,
        df: pd.DataFrame,
        feature_columns: list[str] | None,
        target_column: str | None,
    ) -> list[str]:
        numeric_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in {"time", "alive"}
        ]
        if feature_columns is None:
            # A supervision target must never be part of its own feature vector.
            candidates = [c for c in numeric_cols if c != target_column]
            if target_column is not None:
                target_rows = df[target_column].notna()
                # A target owned by one agent type should not pull in columns that
                # only another agent type has; those would make every row incomplete.
                candidates = [
                    c for c in candidates
                    if target_rows.any() and df.loc[target_rows, c].notna().any()
                ]
            feature_cols = candidates
        else:
            feature_cols = list(feature_columns)
            if not feature_cols:
                raise ValueError("feature_columns 不能为空；传 None 才表示自动选择")
            duplicates = sorted({c for c in feature_cols if feature_cols.count(c) > 1})
            if duplicates:
                raise ValueError(f"feature_columns 含重复列：{duplicates}")
            missing = [c for c in feature_cols if c not in df.columns]
            if missing:
                raise ValueError(f"feature_columns 含不存在的列：{missing}")
            if target_column is not None and target_column in feature_cols:
                raise ValueError(f"目标列 {target_column!r} 不能同时作为特征列")
            non_numeric = [
                c for c in feature_cols
                if not pd.api.types.is_numeric_dtype(df[c])
            ]
            if non_numeric:
                raise ValueError(f"feature_columns 必须都是数值列，非数值列：{non_numeric}")

        if not feature_cols:
            raise ValueError("没有可用的数值特征列")
        return feature_cols

    def _prepare_supervised(
        self,
        feature_columns: list[str] | None,
        target_column: str | None,
        lag_steps: int,
    ) -> tuple[pd.DataFrame, list[str], pd.Series, pd.Series | None]:
        df = self.build_agent_panel()
        lag = self._validate_lag(lag_steps)
        if df.empty:
            return df, [], pd.Series(dtype=bool), None

        required = {"agent_id", "time"}
        missing_columns = sorted(required - set(df.columns))
        if missing_columns:
            raise ValueError(f"状态面板缺少必需列：{missing_columns}")

        if target_column is not None:
            if target_column in required:
                raise ValueError(f"目标列不能是 {target_column!r}")
            if target_column not in df.columns:
                state_columns = sorted(c for c in df.columns if str(c).startswith("state_"))
                raise ValueError(
                    f"目标列 {target_column!r} 不存在。可用状态列：{state_columns}"
                )
            if not pd.api.types.is_numeric_dtype(df[target_column]):
                raise ValueError(f"目标列 {target_column!r} 必须是数值列")

        feature_cols = self._resolve_feature_columns(df, feature_columns, target_column)
        df = df.sort_values(["agent_id", "time"])
        frame = df.loc[:, feature_cols]
        valid = pd.Series(
            np.isfinite(frame.to_numpy()).all(axis=1),
            index=frame.index,
            dtype=bool,
        )

        y = None
        if target_column is not None:
            y = df.groupby("agent_id", sort=False)[target_column].shift(-lag)
            valid = valid & y.notna() & np.isfinite(y)
        return df, feature_cols, valid, y

    def extract_features(
        self,
        feature_columns: list[str] | None = None,
        target_column: str | None = None,
        lag_steps: int = 1,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """Return aligned X/y arrays; use extract_supervised_frame for traceability.

        Missing values remain missing and are dropped by complete-case filtering.
        When feature_columns is omitted, the target and columns unavailable on
        target-bearing rows are excluded automatically.
        """
        df, feature_cols, valid, y = self._prepare_supervised(
            feature_columns, target_column, lag_steps,
        )
        if df.empty:
            return np.array([]), None

        X = df.loc[valid, feature_cols].to_numpy()
        if y is None:
            return X, None
        return X, y.loc[valid].to_numpy()

    def extract_supervised_frame(
        self,
        feature_columns: list[str] | None = None,
        target_column: str | None = None,
        lag_steps: int = 1,
    ) -> pd.DataFrame:
        """Supervised dataset with agent_id/time retained for auditable splits."""
        if target_column is None:
            raise ValueError("extract_supervised_frame 需要 target_column")
        df, feature_cols, valid, y = self._prepare_supervised(
            feature_columns, target_column, lag_steps,
        )
        if df.empty:
            return pd.DataFrame(
                columns=["agent_id", "time", "target_time", *feature_cols, target_column],
            )
        assert y is not None
        lag = self._validate_lag(lag_steps)
        target_time = df.groupby("agent_id", sort=False)["time"].shift(-lag)
        result = df.loc[valid, ["agent_id", "time"]].copy()
        result["target_time"] = target_time.loc[valid].to_numpy()
        for column in feature_cols:
            result[column] = df.loc[valid, column].to_numpy()
        result[target_column] = y.loc[valid].to_numpy()
        return result.reset_index(drop=True)

    def build_transition_dataset(
        self,
        state_columns: list[str] | None = None,
        lag: int = 1,
    ) -> pd.DataFrame:
        df = self.build_agent_panel()
        lag = self._validate_lag(lag)
        if df.empty:
            return pd.DataFrame()
        missing_required = sorted({"agent_id", "time"} - set(df.columns))
        if missing_required:
            raise ValueError(f"状态面板缺少必需列：{missing_required}")

        state_cols = (
            [c for c in df.columns if c.startswith("state_")]
            if state_columns is None
            else list(state_columns)
        )
        if not state_cols:
            raise ValueError("没有可用的状态列")
        duplicates = sorted({c for c in state_cols if state_cols.count(c) > 1})
        if duplicates:
            raise ValueError(f"state_columns 含重复列：{duplicates}")
        missing = [c for c in state_cols if c not in df.columns]
        if missing:
            raise ValueError(f"state_columns 含不存在的列：{missing}")
        non_numeric = [
            c for c in state_cols
            if not pd.api.types.is_numeric_dtype(df[c])
        ]
        if non_numeric:
            raise ValueError(f"state_columns 必须都是数值列，非数值列：{non_numeric}")

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
                row["target_time"] = target["time"]
                records.append(row)
        return pd.DataFrame(records)

    def build_network_features(
        self,
        agent_id: str | None = None,
        up_to_time: float | None = None,
    ) -> pd.DataFrame:
        """Descriptive per-agent aggregates; pass up_to_time for predictive use."""
        df = self.build_agent_panel()
        if df.empty:
            return pd.DataFrame()
        if "agent_id" not in df.columns:
            raise ValueError("状态面板缺少 agent_id 列")
        if agent_id is not None:
            df = df[df["agent_id"] == agent_id]
            if df.empty:
                raise ValueError(f"没有 agent_id={agent_id!r} 的记录")
        if up_to_time is not None:
            if "time" not in df.columns:
                raise ValueError("按时间截断需要 time 列")
            df = df[df["time"] <= up_to_time]
        if df.empty:
            return pd.DataFrame()

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if "time" in numeric_cols:
            numeric_cols.remove("time")
        grouped = df.groupby("agent_id")[numeric_cols].agg(["mean", "std", "min", "max"])
        grouped.columns = ["_".join(col).strip() for col in grouped.columns.values]
        return grouped.reset_index()

    @staticmethod
    def split_by_time(
        frame: pd.DataFrame,
        test_start_time: float,
        time_column: str = "time",
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Deterministic row split; forward-looking labels also need purge."""
        if time_column not in frame.columns:
            raise ValueError(f"数据缺少时间列 {time_column!r}")
        train = frame[frame[time_column] < test_start_time].copy()
        test = frame[frame[time_column] >= test_start_time].copy()
        return train, test

    @staticmethod
    def split_supervised_by_time(
        frame: pd.DataFrame,
        test_start_time: float,
        time_column: str = "time",
        target_time_column: str = "target_time",
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Time split with purging of training labels that reach the test window."""
        missing = [
            column for column in (time_column, target_time_column)
            if column not in frame.columns
        ]
        if missing:
            raise ValueError(f"数据缺少时间列：{missing}")
        train = frame[
            (frame[time_column] < test_start_time)
            & (frame[target_time_column] < test_start_time)
        ].copy()
        test = frame[frame[time_column] >= test_start_time].copy()
        return train, test
