import os
import time


def wait_for(minutes=10):
    pid = os.getpid()
    print(f"Waiting for: {minutes} in pid {pid}")
    time.sleep(60 * minutes)
    print(f"Finished {pid}")
    return pid
