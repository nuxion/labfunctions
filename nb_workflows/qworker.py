import os
import socket
import sys
import time
from datetime import datetime
from typing import List

from loky import get_reusable_executor
from redis import Redis
from rq import Connection, Worker

from nb_workflows.conf import load_server

# from multiprocessing import Pool from db.sync import SQL
# from multiprocessing import Pool

settings = load_server()

sys.path.append(settings.BASE_PATH)
os.environ["NB_AGENT_TOKEN"] = settings.AGENT_TOKEN
os.environ["NB_AGENT_REFRESH_TOKEN"] = settings.AGENT_REFRESH_TOKEN
os.environ["NB_WORKFLOW_SERVICE"] = settings.WORKFLOW_SERVICE


def get_external_ip(dns="8.8.8.8"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((dns, 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


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


def worker(queues: List[str], name=None, ip_address=None):

    cfg = settings.rq2dict()
    redis = Redis(**cfg)
    pid = os.getpid()
    ip_address = ip_address or get_external_ip(dns=settings.DNS_IP_ADDRESS)

    with Connection(connection=redis):
        print(f"Running in {pid} with ip {ip_address}", pid)
        # qs = sys.argv[1:] or ['default']
        w = NBWorker(queues, name=name)
        w.set_ip_addres(ip_address)
        w.work()


def run_workers(qnames: List[str], name=None, ip_address=None, workers_n=1):

    if workers_n > 1:
        _executor = get_reusable_executor(max_workers=workers_n, kill_workers=True)
        _results = [_executor.submit(worker, qnames) for _ in range(workers_n)]
        print(len(_results))
    else:
        worker(qnames)


if __name__ == "__main__":
    # Provide queue names to listen to as arguments to this script,
    # similar to rq worker

    qs = sys.argv[1:] or ["default"]
    executor = get_reusable_executor(max_workers=3, timeout=2, kill_workers=True)
    results = [executor.submit(worker, qs) for _ in range(3)]
