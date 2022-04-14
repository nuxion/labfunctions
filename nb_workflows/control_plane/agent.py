from datetime import datetime
from typing import List

import redis
from loky import get_reusable_executor

from nb_workflows.hashes import generate_random
from nb_workflows.types.cluster import AgentConfig, AgentNode

from .heartbeat import HeartbeatThread
from .register import AgentRegister
from .worker import start_worker


def run(conf: AgentConfig):
    """
    :param redis_dsn: redis url connection like redis://localhost:6379/0
    :param qnames: a list of queues to listen to
    :param name: a custom name for this worker
    :param ip_address: the ip as worker that will advertise to Redis.
    :param workers_n: how many worker to run
    """

    name = conf.name or generate_random(size=9)
    rdb = redis.from_url(conf.redis_dsn)

    heart = HeartbeatThread(
        rdb,
        name,
        ttl_secs=conf.heartbeat_ttl,
        check_every_secs=conf.heartbeat_check_every,
    )
    heart.setDaemon(True)
    heart.start()

    workers_names = [f"{name}.{x}" for x in range(conf.workers_n)]

    _now = int(datetime.utcnow().timestamp())
    node = AgentNode(
        ip_address=conf.ip_address,
        name=name,
        qnames=conf.qnames,
        workers=workers_names,
        birthday=_now,
    )
    ag = AgentRegister(rdb)
    ag.register(node)

    if conf.workers_n > 1:
        _executor = get_reusable_executor(max_workers=conf.workers_n, kill_workers=True)
        _results = [
            _executor.submit(
                start_worker, conf.redis_dsn, conf.qnames, conf.ip_address, name_i
            )
            for name_i in workers_names
        ]
    else:
        start_worker(
            conf.redis_dsn,
            conf.qnames,
            name=workers_names[0],
            ip_address=conf.ip_address,
        )
