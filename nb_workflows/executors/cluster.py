from importlib import import_module
from typing import List

import redis
from rq import Queue

from nb_workflows import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.hashes import generate_random
from nb_workflows.types.cluster import ExecMachineResult, ExecutionMachine

REDIS_PREFIX = "nb.mch."
CONTROL_QUEUES = {"rq:queue:control"}


def create_machine_exec(ctx: ExecutionMachine):

    if ctx.provider == "local":
        from nb_workflows.cluster.local_provider import LocalProvider

        provider = LocalProvider("/tmp/test")

    rdb = redis.from_url(settings.WEB_REDIS)
    # rdb.set(f"{REDIS_PREFIX}.{exec_result.node.name}", exec_result.json())


def destroy_machine(name: str):
    pass


def get_queues(rdb: redis.Redis):
    queues = rdb.sinter("rq:queues")
    data_plane = queues - CONTROL_QUEUES
    for name in data_plane:
        qname = name.rsplit(":", maxsplit=1)[1]
        q = Queue(qname, connection=rdb)
        waiting = len(q)


def scale_control(redis_dsn):
    rdb = redis.from_url(redis_dsn, decode_responses=True)
