from __future__ import annotations

import uuid
from typing import Any


class Agent:
    def __init__(
        self,
        agent_id: str | None = None,
        attributes: dict[str, Any] | None = None,
        state: dict[str, Any] | None = None,
    ):
        self.id = agent_id or str(uuid.uuid4())
        self.attributes = attributes or {}
        self.state = state or {}
        self.environment: Any = None
        self.alive = True

    def step(self) -> None:
        raise NotImplementedError

    def advance_time(self) -> None:
        """推进智能体自身的"生命时间"（默认不做任何事）。

        由调度器在**每个时间步、对每个存活智能体**调用一次，与
        :meth:`step` 的激活选择**互相独立**：``step`` 回答"这一步谁行动"，
        ``advance_time`` 回答"这一步时间在谁身上流逝"。两者分离是必要的——
        ``random_activation`` 只激活部分智能体，若把时间推进写在 ``step`` 里，
        未被激活者连年龄都停滞，导致同一仿真里不同智能体的"生命时间"互不相同，
        而记录的时间轴却按 ``Environment.time`` 逐格递增，二者失去可比性。

        需要衰老的智能体（如 ``FamilyMember``）覆写本方法；
        不需要生命周期语义的智能体继承此空实现即可。
        """

    def get_state(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": type(self).__name__,
            "attributes": dict(self.attributes),
            "state": dict(self.state),
            "alive": self.alive,
        }

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)

    def set_state_value(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get_state_value(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)
