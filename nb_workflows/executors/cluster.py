import random
from enum import Enum
from importlib import import_module
from typing import Any, Dict, List, Optional, Set

import redis
from pydantic import BaseModel
from rq import Queue

from nb_workflows import defaults
from nb_workflows.cluster.context import machine_from_settings
from nb_workflows.cluster.local_provider import LocalProvider
from nb_workflows.control_plane.register import AgentRegister
from nb_workflows.control_plane.worker import NBWorker
from nb_workflows.hashes import generate_random

# from nb_workflows.conf.server_settings import settings
from nb_workflows.types import ServerSettings
from nb_workflows.types.cluster import AgentNode, ExecMachineResult, ExecutionMachine


class ScaleItems(BaseModel):
    items_gt: int
    items_lt: int = -1
    increase_by: int = 1
    decrease_by: int = 1
    name: str = "items"


class ScaleIdle(BaseModel):
    """idle_time in minutes"""

    idle_time_gt: int
    idle_time_lt: Optional[int] = None
    name: str = "idle"


class ClusterState(BaseModel):
    agents_n: int
    agents: Set[str]
    queue_items: int
    idle_by_agent: Dict[str, int]
    # machines:


class ClusterPolicy(BaseModel):
    min_nodes: int
    max_nodes: int
    strategies: List[Any] = None
    default_nodes: Optional[int] = None


class ClusterDiff(BaseModel):
    to_delete: List[str]
    to_create: int


class ClusterSpec(BaseModel):
    name: str
    machine: str
    provider: str
    policy: ClusterPolicy
    location: str = "test"


def workers2dict(workers: List[NBWorker]) -> Dict[str, List[NBWorker]]:
    workers_dict: Dict[str, List[NBWorker]] = {}
    for w in workers:
        agt = w.name.split(".")[0]
        if workers_dict.get(agt):
            workers_dict[agt].append(w)
        else:
            workers_dict[agt] = [w]
    return workers_dict


def apply_scale_items(state: ClusterState, scale: ScaleItems) -> ClusterState:
    new_state = state.copy()
    if state.queue_items >= scale.items_gt:
        new_state.agents_n += scale.increase_by
    elif state.queue_items <= scale.items_lt:
        new_state.agents_n -= scale.decrease_by
        new_state.agents.pop()

    return new_state


def apply_idle(state: ClusterState, idle: ScaleIdle) -> ClusterState:
    new_state = state.copy()
    shutdown_agents = set()
    for agt in state.agents:
        if state.idle_by_agent[agt] >= idle.idle_time_gt:
            shutdown_agents.add(agt)
    agents = state.agents - shutdown_agents

    new_state.agents = agents
    new_state.agents_n = len(agents)
    return new_state


def apply_minmax(state: ClusterState, policy: ClusterPolicy) -> ClusterState:
    new_state = state.copy()
    if state.agents_n < policy.min_nodes:
        new_state.agents_n = policy.min_nodes
    elif state.agents_n > policy.max_nodes:
        new_state.agents_n = policy.max_nodes

    return new_state


class ClusterControl:

    POLICIES = {
        "items": apply_scale_items,
        "idle": apply_idle,
        # "minmax": apply_minmax
    }

    def __init__(self, rdb: redis.Redis, cluster_name: str):
        self.rdb = rdb
        self.name = cluster_name
        self.spec = clusters.get(cluster_name)
        self.agents: List[AgentNode] = []
        self.register = AgentRegister(rdb)
        self.state = self.build_state()

    def refresh(self):
        self.state = self.build_state()

    def get_queue(self, qname) -> Queue:
        return Queue(qname, connection=self.rdb)

    def build_state(self) -> ClusterState:
        agents = self.register.list_agents(self.name)
        # agents_obj = {self.register.get(a) for a in agents}
        agents_n = len(agents)
        q = self.get_queue(self.name)
        queue_items = len(q)
        workers = NBWorker.all(queue=q)
        workers_dict = workers2dict(workers)
        idle_by_agent = {}
        for agt in agents:
            _workers = workers_dict[agt]
            _inactive = [w.inactive_time() for w in _workers]
            minimun = sorted(_inactive)[0]
            idle_by_agent[agt] = minimun / 60
        return ClusterState(
            agents_n=agents_n,
            agents=set(agents),
            queue_items=queue_items,
            idle_by_agent=idle_by_agent,
        )

    @property
    def policy(self) -> ClusterPolicy:
        return self.spec.policy

    def apply_policies(self):
        new_state = self.state.copy()
        for scale in self.policy.strategies:
            new_state = self.POLICIES[scale.name](new_state, scale)

        new_state = apply_minmax(new_state, self.policy)

        return new_state

    def difference(self, new_state: ClusterState) -> ClusterDiff:

        to_delete = self.state.agents - new_state.agents

        to_create = 0
        if new_state.agents_n > self.state.agents_n:
            to_create = new_state.agents_n - self.state.agents_n

        if len(new_state.agents) < self.policy.min_nodes:
            to_create = self.policy.min_nodes - len(new_state.agents)

        return ClusterDiff(to_create=to_create, to_delete=list(to_delete))


REDIS_PREFIX = "nb.mch."
CONTROL_QUEUES = {"rq:queue:control"}

clusters = {
    "default": ClusterSpec(
        name="default",
        machine="local",
        provider="local",
        policy=ClusterPolicy(
            min_nodes=0,
            max_nodes=2,
            strategies=[
                ScaleIdle(idle_time_gt=1),
                ScaleItems(items_gt=1),
            ],
        ),
    ),
    "control": ClusterSpec(
        name="control",
        machine="local",
        provider="local",
        policy=ClusterPolicy(min_nodes=1, max_nodes=1, strategies=[]),
    ),
}


def scale_control2(settings: ServerSettings):
    rdb = redis.from_url(settings.RQ_REDIS, decode_responses=True)
    register = AgentRegister(rdb)
    provider = LocalProvider("/tmp/test")
    for cluster_name in clusters.keys():
        print(f"Evaluating cluster: {cluster_name}")
        cc = ClusterControl(rdb, cluster_name)
        new_state = cc.apply_policies()
        diff = cc.difference(new_state)
        print(f"To create: {diff.to_create}")
        for _ in range(diff.to_create):
            ctx = machine_from_settings(cc.spec.machine, [cc.spec.name], settings)
            print(f"Creating machine: {ctx.node.name}")
            instance = provider.create_machine(ctx.node)
            provider.deploy(instance, ctx)
        for agt in diff.to_delete:
            agent = cc.register.get(agt)
            print(f"Deleting agent {agt}")
            # cc.register.unregister(agent)
            cc.register.kill_workers_from_agent(agent.name)
            # provider.destroy_machine(agent.pid)
        print("=" * 10)


if __name__ == "__main__":
    from nb_workflows.conf.server_settings import settings

    scale_control2(settings)
