import json
from typing import Dict, List, Optional, Set, Union

import redis
from rq import Queue
from rq.command import send_shutdown_command

from labfunctions.control_plane.worker import NBWorker
from labfunctions.types.agent import AgentNode
from labfunctions.types.machine import MachineInstance


def workers2dict(workers: List[NBWorker]) -> Dict[str, List[NBWorker]]:
    workers_dict: Dict[str, List[NBWorker]] = {}
    for w in workers:
        agt = w.name.split(".")[0]
        if workers_dict.get(agt):
            workers_dict[agt].append(w)
        else:
            workers_dict[agt] = [w]
    return workers_dict


class AgentRegister:

    AGENT_PREFIX = "nb.ag"
    AGENT_LIST = "nb.agents"
    AGENT_CLUSTERS = "nb.clusters"
    AGENT_CLUSTER_PREFIX = "nb.cluster"
    MACHINE_PREFIX = "nb.mch"
    MACHINE_CLUSTERS = "nb.mch.clusters"
    MACHINE_CLUSTER_PREFIX = "nb.mch.cluster"

    def __init__(self, rdb: redis.Redis, cluster: str):
        """
        The AgentRegister keep track of the agent activity:
        mainly: it register Machine data like ip address, name and workers running.

        It uses the same redis connection of RQ.

        :param rdb: redis.Redis
        """
        self.rdb = rdb
        self.cluster = cluster

    def qname(self, qname):
        return f"{self.cluster}.{qname}"

    def register(self, node: AgentNode):
        """
        Register a `AgentNode`
        """
        key = f"{self.AGENT_PREFIX}.{node.name}"
        pipe = self.rdb.pipeline()
        # for q in node.qnames:
        pipe.sadd(self.AGENT_CLUSTERS, node.cluster)
        pipe.sadd(f"{self.AGENT_CLUSTER_PREFIX}.{node.cluster}", node.name)
        pipe.set(key, node.json())
        pipe.sadd(self.AGENT_LIST, node.name)
        pipe.execute()

    def unregister(self, node: AgentNode):
        key = f"{self.AGENT_PREFIX}.{node.name}"
        pipe = self.rdb.pipeline()
        # for q in node.qnames:
        # pipe.srem(f"{self.CLUSTER_PREFIX}.{q}", node.name)
        pipe.srem(f"{self.AGENT_CLUSTER_PREFIX}.{node.cluster}", node.name)
        pipe.delete(key)
        pipe.srem(self.AGENT_LIST, node.name)
        pipe.execute()

    def get(self, name) -> Union[AgentNode, None]:
        """Get at an agent by name"""

        key = f"{self.AGENT_PREFIX}.{name}"
        jdata = self.rdb.get(key)
        if jdata:
            data = json.loads(jdata)
            return AgentNode(**data)
        return None

    def register_machine(self, node: MachineInstance):
        key = f"{self.MACHINE_PREFIX}.{self.cluster}.{node.machine_id}"
        self.rdb.set(key, node.json())

    def unregister_machine(self, machine_id: str):
        key = f"{self.MACHINE_PREFIX}.{self.cluster}.{machine_id}"
        self.rdb.delete(key)

    def get_machine(self, machine_id: str) -> MachineInstance:
        key = f"{self.MACHINE_PREFIX}.{self.cluster}.{machine_id}"
        data = self.rdb.get(key)
        return MachineInstance(**json.loads(data))

    def get_queue(self, qname) -> Queue:
        return Queue(self.qname(qname), connection=self.rdb)

    def remove(self, agent: str):
        """It removes agent by name from redis"""
        key = f"{self.AGENT_PREFIX}.{agent}"
        pipe = self.rdb.pipeline()
        pipe.srem(self.AGENT_LIST, agent)
        pipe.delete(key)
        pipe.execute()

    def list_clusters(self) -> Set[str]:
        return self.rdb.sinter(self.AGENT_CLUSTERS)

    def list_agents(self, from_cluster=None) -> List[str]:
        """Return a list of the keys of all the agent registered"""
        query = self.AGENT_LIST
        if from_cluster:
            query = f"{self.AGENT_CLUSTER_PREFIX}.{from_cluster}"
        rsp = list(self.rdb.sinter(query))

        if rsp and isinstance(rsp[0], str):
            return rsp
        else:
            return [i.decode("utf-8") for i in rsp]

    def list_agents_by_queue(self, qname: str) -> Set[str]:
        """
        Get agents keys belonging to a queue
        """
        data = set()
        workers = self.get_workers_from_q(self.qname(qname))
        for w in workers:
            data.add(w.name.rsplit(".", maxsplit=1)[0])
        return data

    def get_workers_from_q(self, qname) -> List[NBWorker]:
        q = Queue(self.qname(qname), connection=self.rdb)
        workers = NBWorker.all(queue=q)
        return workers

    def idle_agents_from_cluster(
        self, cluster: str, qnames: List[str]
    ) -> Dict[str, float]:
        """It calculates the idle time from each worker, and then choose the
        lowest by agent. The idle time is returned in minutes
        """
        _qnames = [self.qname(q) for q in qnames]

        queues: List[Queue] = [self.get_queue(q) for q in _qnames]
        agents = self.list_agents(cluster)
        idle_agents = self.idle_agents(agents, queues)
        return idle_agents

    def idle_agents(self, agents: List[str], queues: List[Queue]) -> Dict[str, float]:
        """It calculates the idle time from each worker, and then choose the
        lowest by agent. The idle time is returned in minutes
        if for some reason a workers any worker is found in an agent it will fail
        """
        workers = []
        for q in queues:
            _workers = NBWorker.all(queue=q)
            workers.extend(_workers)

        workers_dict = workers2dict(workers)
        idle_by_agent = {}
        for agt in agents:
            _workers = workers_dict[agt]
            _inactive = [w.inactive_time() for w in _workers]
            minimun = sorted(_inactive)[0]
            idle_by_agent[agt] = minimun / 60
        return idle_by_agent

    def kill_workers_from_agent(self, agent_name) -> bool:
        """
        It sends a shutdown command to RQ Workers from an agent
        """
        node = self.get(agent_name)
        try:
            for w in node.workers:
                send_shutdown_command(self.rdb, w)
            return True
        except AttributeError:
            return False

    def kill_workers_from_queue(self, qname: str):

        q = Queue(self.qname(qname), connection=self.rdb)
        workers = NBWorker.all(queue=q)
        for w in workers:
            send_shutdown_command(self.rdb, w.name)
