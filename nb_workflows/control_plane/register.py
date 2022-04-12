import json
from typing import List, Optional, Set, Union

import redis
from rq import Queue, Worker
from rq.command import send_shutdown_command

from nb_workflows.types.cluster import AgentNode


class AgentRegister:

    PREFIX = "nb.ag"
    PREFIX_LIST = "nb.ag.set"

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
        key = f"{self.PREFIX}.{node.name}"
        self.rdb.set(key, node.json())
        # self.rdb.zadd(self.PREFIX_LIST, {node.name: now})
        self.rdb.sadd(self.PREFIX_LIST, node.name)

    def get(self, name) -> Union[AgentNode, None]:
        """Get at an agent by name"""

        key = f"{self.PREFIX}.{name}"
        jdata = self.rdb.get(key)
        if jdata:
            data = json.loads(jdata)
            return AgentNode(**data)
        return None

    def remove(self, agent: str):
        """It removes agent by name from redis"""
        key = f"{self.PREFIX}.{agent}"
        pipe = self.rdb.pipeline()
        pipe.srem(self.PREFIX_LIST, agent)
        pipe.delete(key)
        pipe.execute()

    def list_agents(self) -> List[str]:
        """Return a list of the keys of all the agent registered"""
        return [i.decode("utf-8") for i in self.rdb.sinter(self.PREFIX_LIST)]

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
