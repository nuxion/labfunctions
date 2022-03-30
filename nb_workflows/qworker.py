import os
import sys
import time

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


def worker(params):

    cfg = settings.rq2dict()
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

    if workers > 1:
        _executor = get_reusable_executor(max_workers=workers, kill_workers=True)
        _results = [_executor.submit(worker, qnames) for _ in range(workers)]
        print(len(_results))
    else:
        worker(qnames)


if __name__ == "__main__":
    # Provide queue names to listen to as arguments to this script,
    # similar to rq worker

    qs = sys.argv[1:] or ["default"]
    executor = get_reusable_executor(max_workers=3, timeout=2, kill_workers=True)
    results = [executor.submit(worker, qs) for _ in range(3)]
