import os
from datetime import datetime
from typing import List

import redis
from loky import get_reusable_executor

from labfunctions.hashes import generate_random
from labfunctions.types.agent import AgentConfig, AgentNode

from .heartbeat import HeartbeatThread
from .register import AgentRegister
from .worker import start_worker


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
    rdb = redis.from_url(conf.redis_dsn, decode_responses=True)

    heart = HeartbeatThread(
        rdb,
        name,
        ttl_secs=conf.heartbeat_ttl,
        check_every_secs=conf.heartbeat_check_every,
    )
    heart.setDaemon(True)
    heart.start()

    workers_names = [f"{name}.{x}" for x in range(conf.workers_n)]
    cluster_queues = [f"{conf.cluster}.{q}" for q in conf.qnames]

    _now = int(datetime.utcnow().timestamp())
    pid = os.getpid()
    node = AgentNode(
        ip_address=conf.ip_address,
        name=name,
        machine_id=conf.machine_id,
        cluster=conf.cluster,
        pid=pid,
        qnames=conf.qnames,
        workers=workers_names,
        birthday=_now,
    )
    ag = AgentRegister(rdb, cluster=conf.cluster)
    ag.register(node)

    if conf.workers_n > 1:
        _executor = get_reusable_executor(max_workers=conf.workers_n, kill_workers=True)
        _results = [
            _executor.submit(
                start_worker, conf.redis_dsn, cluster_queues, conf.ip_address, name_i
            )
            for name_i in workers_names
        ]
    else:
        start_worker(
            conf.redis_dsn,
            cluster_queues,
            name=workers_names[0],
            ip_address=conf.ip_address,
        )
    ag.unregister(node)
    heart.unregister()
