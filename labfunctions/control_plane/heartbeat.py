import signal
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
        self.shutdown_flag = threading.Event()

    def run(self):
        key = f"{self.PREFIX}.{self.name}"
        while not self.shutdown_flag.is_set():
            print(f"Heartbeat: I'm alive on key {key}")
            self.rdb.set(key, "alive", ex=self.ttl_secs)
            time.sleep(self.check_every)

    def unregister(self):
        print("Calling unregister")
        key = f"{self.PREFIX}.{self.name}"
        self.rdb.delete(key)
        self.shutdown_flag.set()
