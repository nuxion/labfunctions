import os
from datetime import datetime
from typing import List

import redis
from rq import Connection, Worker


class NBWorker(Worker):
    """Extensions of the default Worker class to set ip_address"""

    def set_ip_address(self, ip_address):
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
        w.set_ip_address(ip_address)
        w.work()
