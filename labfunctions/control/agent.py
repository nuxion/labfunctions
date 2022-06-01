import os
import sys
from datetime import datetime
from typing import List

from libq.job_store import RedisJobStore
from libq.scheduler import Scheduler

# from .heartbeat import HeartbeatThread
# from .register import AgentRegister
# from .worker import start_worker
from libq.worker import AsyncWorker

from labfunctions.hashes import generate_random
from labfunctions.redis_conn import create_pool
from labfunctions.types import ServerSettings
from labfunctions.types.agent import AgentConfig, AgentNode


def set_env(settings: ServerSettings):
    sys.path.append(settings.BASE_PATH)
    os.environ["LF_AGENT_TOKEN"] = settings.AGENT_TOKEN
    os.environ["LF_AGENT_REFRESH_TOKEN"] = settings.AGENT_REFRESH_TOKEN
    os.environ["LF_WORKFLOW_SERVICE"] = settings.WORKFLOW_SERVICE


def run(conf: AgentConfig):
    """
    This is the main function which start workers by agent by machine.

    To ack:
    qnames: will be prepended with the name of the cluster, for instance:
    qnames = ["default", "control"]; cluster = "gpu"
    qnames_fit = ["gpu.default", "gpu.control"]

    :param redis_dsn: redis url connection like redis://localhost:6379/0
    :param qnames: a list of queues to listen to
    :param name: a custom name for this worker
    :param ip_address: the ip as worker that will advertise to Redis.
    :param workers_n: how many worker to run
    """

    name = conf.agent_name or conf.machine_id.rsplit("/", maxsplit=1)[1]
    cluster_queues = [f"{conf.cluster}.{q}" for q in conf.qnames]

    conn = create_pool(conf.redis_dsn)
    _now = int(datetime.utcnow().timestamp())
    pid = os.getpid()
    node = AgentNode(
        ip_address=conf.ip_address,
        name=name,
        machine_id=conf.machine_id,
        cluster=conf.cluster,
        pid=pid,
        qnames=conf.qnames,
        workers=[],
        birthday=_now,
    )
    store = RedisJobStore()
    scheduler = Scheduler(store, conn=conn)
    worker = AsyncWorker(
        queues=",".join(cluster_queues),
        conn=conn,
        id=name,
        heartbeat_secs=conf.heartbeat_check_every,
        metadata=node.dict(),
    )

    worker.run()
