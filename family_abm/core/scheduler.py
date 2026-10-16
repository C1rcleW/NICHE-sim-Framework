from __future__ import annotations

import random
from typing import Any

from .agent import Agent
from .environment import Environment


class Scheduler:
    """决定每个时间步"哪些 agent、以什么顺序"被更新。

    ``rng`` 由 :class:`Simulation` 注入，与智能体共享同一条随机流；
    单独使用本类时回退到全局 ``random``。
    """

    def __init__(self, method: str = "sequential", rng: Any = None):
        self.method = method
        self.time = 0
        self.rng = rng if rng is not None else random

    def schedule(self, environment: Environment) -> list[Agent]:
        agents = environment.get_agents()
        if self.method == "sequential":
            return agents
        elif self.method == "random":
            shuffled = list(agents)
            self.rng.shuffle(shuffled)
            return shuffled
        elif self.method == "random_activation":
            shuffled = list(agents)
            self.rng.shuffle(shuffled)
            n = self.rng.randint(1, max(1, len(shuffled)))
            return shuffled[:n]
        else:
            raise ValueError(f"Unknown scheduler method: {self.method}")

    def step(self, environment: Environment) -> None:
        """推进一个时间步。

        分两个互相独立的阶段：

        1. **时间推进**：对*所有存活智能体*调用 ``advance_time()``。放在选择之前，
           使"时间在谁身上流逝"不受本步激活集合影响——``random_activation``
           只激活一部分智能体，但没被激活的人一样会变老。
        2. **行动**：对调度选出的子集调用 ``step()``。
        """
        for agent in environment.get_agents():
            if agent.alive:
                agent.advance_time()
        for agent in self.schedule(environment):
            if agent.alive:
                agent.step()
        self.time += 1
        environment.time = self.time
