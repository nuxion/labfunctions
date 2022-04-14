import threading
import time

from redis import Redis


class HeartbeatThread(threading.Thread):

    PREFIX = "nb.ag.heart"

    def __init__(self, rdb: Redis, name: str, ttl_secs=15, check_every_secs=10):
        threading.Thread.__init__(self)

        self.rdb = rdb
        self.name = name
        self.ttl_secs = ttl_secs
        self.check_every = check_every_secs

    def run(self):
        key = f"{self.PREFIX}.{self.name}"
        while True:
            print(f"Heartbeat: I'm alive on key {key}")
            self.rdb.set(key, "alive", ex=self.ttl_secs)
            time.sleep(self.check_every)
