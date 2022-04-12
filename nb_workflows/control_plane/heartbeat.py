import threading
import time

from redis import Redis


class HeartbeatThread(threading.Thread):

    PREFIX = "nb.ag.heart"

    def __init__(self, rdb: Redis, name: str, ex_secs=15, sleep_secs=10):
        threading.Thread.__init__(self)

        self.rdb = rdb
        self.name = name
        self.ex_secs = ex_secs
        self.sleep = sleep_secs

    def run(self):
        key = f"{self.PREFIX}.{self.name}"
        while True:
            print(f"Heartbeat: I'm alive on key {key}")
            self.rdb.set(key, "alive", ex=self.ex_secs)
            time.sleep(self.sleep)
