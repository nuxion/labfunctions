import os
import sys
import time

# from multiprocessing import Pool from db.sync import SQL
from multiprocessing import Pool

from loky import get_reusable_executor, process_executor
from redis import Redis
from rq import Connection, Worker

from nb_workflows.conf import Config

sys.path.append(Config.BASE_PATH)


def worker(params):

    cfg = Config.rq2dict()
    redis = Redis(**cfg)
    pid = os.getpid()

    with Connection(connection=redis):
        print("Running in pid ", pid)
        # qs = sys.argv[1:] or ['default']

        w = Worker(params)
        w.work()


def error():
    print("Executing error")
    time.sleep(6)
    raise TypeError("Error")


def run_workers(qnames, workers):

    _executor = get_reusable_executor(max_workers=workers, kill_workers=True)
    _results = [_executor.submit(worker, qnames) for _ in range(workers)]
    print(len(_results))


if __name__ == "__main__":
    # Provide queue names to listen to as arguments to this script,
    # similar to rq worker

    qs = sys.argv[1:] or ["default"]
    executor = get_reusable_executor(max_workers=3, timeout=2, kill_workers=True)
    results = [executor.submit(worker, qs) for _ in range(3)]
