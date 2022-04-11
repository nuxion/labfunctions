import os
from datetime import datetime
from typing import List

import redis
from loky import get_reusable_executor
from rq import Connection, Worker

from nb_workflows.hashes import generate_random


class NBWorker(Worker):
    """Extensions of the default Worker class to set ip_address"""

    def set_ip_addres(self, ip_address):
        self.ip_address = ip_address

    def inactive_time(self):
        """it calculates in seconds, the total inactive time of a worker"""
        working = self.total_working_time
        now = datetime.utcnow()
        birth_elapsed = (now - self.birth_date).seconds
        return birth_elapsed - working


def start_worker(redis_dsn, queues: List[str], ip_address: str, name: str):

    rdb = redis.from_url(redis_dsn)
    pid = os.getpid()

    with Connection(connection=rdb):
        print(f"Running in {pid} with ip {ip_address}", pid)
        # qs = sys.argv[1:] or ['default']
        w = NBWorker(queues, name=name)
        w.set_ip_addres(ip_address)
        w.work()


def run(redis_dsn: str, qnames: List[str], name=None, ip_address=None, workers_n=1):
    """
    :param redis_dsn: redis url connection like redis://localhost:6379/0
    :param qnames: a list of queues to listen to
    :param name: a custom name for this worker
    :param ip_address: the ip as worker that will advertise to Redis.
    :param workers_n: how many worker to run
    """

    name = name or generate_random(size=9)

    if workers_n > 1:
        _executor = get_reusable_executor(max_workers=workers_n, kill_workers=True)
        _results = [
            _executor.submit(start_worker, redis_dsn, qnames, name, ip_address)
            for _ in range(workers_n)
        ]
        print(len(_results))
    else:
        start_worker(redis_dsn, qnames, name=name, ip_address=ip_address)
