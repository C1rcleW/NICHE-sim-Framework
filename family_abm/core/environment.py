from __future__ import annotations

import random
from typing import Any

from .agent import Agent


class Environment:
    """智能体的容器与共享上下文。

    除注册智能体外，它还承载两类共享状态：

    - ``params``：动力学参数（`FamilyMember._p()` 会读取，缺省时回退到 DEFAULT_PARAMS）
    - ``rng``：随机数发生器。默认是全局 ``random`` 模块；当由 :class:`Simulation`
      以 ``seed`` 创建时会换成独立实例，使仿真可复现且不影响进程内的其它随机数使用。
      智能体应通过 ``environment.rng`` 取随机数，而不是直接调用全局 ``random``。
    - ``seed``：仿真种子。需要"按身份派生独立随机流"的组件（如 ``Relationship``）
      用它获得确定性种子，从而摆脱对对象迭代顺序的依赖。
    """

    def __init__(self, width: int = 100, height: int = 100):
        self.agents: dict[str, Agent] = {}
        self.time: int = 0
        self.width = width
        self.height = height
        self.properties: dict[str, Any] = {}
        self.params: dict[str, float] = {}
        self.rng: Any = random
        self.seed: int | None = None
        # 容器型智能体（Household 等）的确定性序号分配计数器，见 container_seq()
        self._container_seq = 0

    def container_seq(self, agent: Agent) -> int:
        """返回容器型智能体在本环境中的确定性序号（首次调用时按到达顺序分配）。

        用于给容器一个**跨运行稳定、环境内唯一**的标识，供按身份派生随机流
        （如 ``Relationship`` 的种子）使用。不能用 agent.id——那是每次运行都
        变的 uuid，会让同一 seed 的结果不可复现；也不能只用显示名——同名容器
        （包括默认名）会拿到完全相同的随机流，使不同家庭的状态系统性相关。
        序号只由**构建顺序**决定，因此构建顺序确定即可复现。
        """
        seq = getattr(agent, "_env_container_seq", None)
        if seq is None:
            seq = self._container_seq
            self._container_seq += 1
            agent._env_container_seq = seq
        return seq

    def add_agent(self, agent: Agent, x: float | None = None, y: float | None = None) -> None:
        """注册智能体；若它是容器型智能体（如 ``Household``），一并收养其成员。

        成员可能在家庭被注册之前就通过 ``Household.add_member()`` 加入——那时家庭
        还没有 environment，成员无法自我注册。若这里不收养，成员会**静默地永不
        步进**（年龄不变、状态冻结），且没有任何报错。收养后，"先 add_member
        后 add_agent" 与 "先 add_agent 后 add_member" 两种构建顺序等价：
        环境中的插入顺序都是 [家庭, 成员...]。
        """
        self.agents[agent.id] = agent
        agent.environment = self
        members = getattr(agent, "members", None)
        if isinstance(members, dict):
            # 提前分配确定性序号（add_member 可能已经分配过；重复调用返回同一值）
            self.container_seq(agent)
            for member in members.values():
                if member.id not in self.agents:
                    self.agents[member.id] = member
                    member.environment = self
        if x is not None:
            agent.set_attribute("x", x)
        if y is not None:
            agent.set_attribute("y", y)

    def remove_agent(self, agent_id: str) -> None:
        """注销智能体；容器型智能体的成员随之一并注销（与收养对称）。

        只移除家庭而留下其成员，会让成员继续被调度但已脱离家庭（压力源丢失），
        产生一个既不属于任何家庭、又照常步进的中间状态。
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            members = getattr(agent, "members", None)
            if isinstance(members, dict):
                for member_id in list(members):
                    member = self.agents.get(member_id)
                    if member is not None:
                        member.environment = None
                        del self.agents[member_id]
            agent.environment = None
            del self.agents[agent_id]

    def get_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def get_agent_by_id(self, agent_id: str) -> Agent | None:
        return self.agents.get(agent_id)

    def get_agents_by_type(self, agent_type: type) -> list[Agent]:
        return [a for a in self.agents.values() if isinstance(a, agent_type)]

    def step(self) -> None:
        """步进所有智能体一次（不经过 Scheduler 的直连入口）。

        与 ``Scheduler.step`` 保持同一阶段语义：先对所有存活智能体推进时间，
        再让它们行动。
        """
        for agent in self.get_agents():
            if agent.alive:
                agent.advance_time()
        for agent in self.get_agents():
            if agent.alive:
                agent.step()
        self.time += 1

    def get_global_state(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "population": len(self.agents),
            "properties": dict(self.properties),
        }
