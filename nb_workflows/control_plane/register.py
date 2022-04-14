import json
from typing import List, Optional, Set, Union

import redis
from rq import Queue, Worker
from rq.command import send_shutdown_command

from nb_workflows.types.cluster import AgentNode


class AgentRegister:

    AGENT_PREFIX = "nb.ag"
    AGENT_LIST = "nb.agents"
    CLUSTERS = "nb.clusters"
    CLUSTER_PREFIX = "nb.cluster"

    def __init__(self, rdb: redis.Redis):
        """
        The AgentRegister keep track of the agent activity:
        mainly: it register Machine data like ip address, name and workers running.

        It uses the same redis connection of RQ.

        :param rdb: redis.Redis
        """
        self.rdb = rdb

    def register(self, node: AgentNode):
        """
        Register a `AgentNode`
        """
        key = f"{self.AGENT_PREFIX}.{node.name}"
        pipe = self.rdb.pipeline()
        for q in node.qnames:
            pipe.sadd(self.CLUSTERS, q)
            pipe.sadd(f"{self.CLUSTER_PREFIX}.{q}", node.name)
        pipe.set(key, node.json())
        pipe.sadd(self.AGENT_LIST, node.name)
        pipe.execute()

    def unregister(self, node: AgentNode):
        key = f"{self.AGENT_PREFIX}.{node.name}"
        pipe = self.rdb.pipeline()
        for q in node.qnames:
            # pipe.sadd(self.CLUSTERS, q)
            pipe.srem(f"{self.CLUSTER_PREFIX}.{q}", node.name)
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

    def remove(self, agent: str):
        """It removes agent by name from redis"""
        key = f"{self.AGENT_PREFIX}.{agent}"
        pipe = self.rdb.pipeline()
        pipe.srem(self.AGENT_LIST, agent)
        pipe.delete(key)
        pipe.execute()

    def list_agents(self, from_cluster=None) -> List[str]:
        """Return a list of the keys of all the agent registered"""
        query = self.AGENT_LIST
        if from_cluster:
            query = f"{self.CLUSTER_PREFIX}.{from_cluster}"
        rsp = list(self.rdb.sinter(query))

        if rsp and isinstance(rsp[0], str):
            return rsp
        else:
            return [i.decode("utf-8") for i in rsp]

    def list_agents_by_queue(self, qname: str) -> Set[str]:
        """
        Get agents keys belonging to a queue
        """
        q = Queue(qname, connection=self.rdb)
        workers = Worker.all(queue=q)
        data = set()
        for w in workers:
            data.add(w.name.rsplit(".", maxsplit=1)[0])
        return data

    def kill_workers_from_agent(self, agent_name):
        """
        It sends a shutdown command to RQ Workers from an agent
        """
        node = self.get(agent_name)
        for w in node.workers:
            send_shutdown_command(self.rdb, w)
            # self.remove_worker(w)

    def kill_workers_from_queue(self, qname: str):
        q = Queue(qname, connection=self.rdb)
        workers = Worker.all(queue=q)
        for w in workers:
            send_shutdown_command(self.rdb, w.name)
