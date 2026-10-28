"""Thread-safe storage for the latest immutable simulation run."""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


class UnknownRunError(LookupError):
    def __init__(self, run_id: str):
        super().__init__(f"未知运行 {run_id!r}")
        self.run_id = run_id


@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    env: Any
    df: Any
    recorder: Any


class RunStore:
    """Keep one completed run; a bounded store is enough for the local dashboard."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._latest: RunSnapshot | None = None

    def publish(self, snapshot: RunSnapshot) -> None:
        with self._lock:
            self._latest = snapshot

    def get(self, run_id: str | None = None) -> RunSnapshot | None:
        with self._lock:
            snapshot = self._latest
            if snapshot is None:
                return None
            if run_id is not None and run_id != snapshot.run_id:
                raise UnknownRunError(run_id)
            return snapshot

    def clear(self) -> None:
        with self._lock:
            self._latest = None
