# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# + tags=["parameters"]
SLEEP = 5
ERROR = False

NOW = None
JOBID = "test_job"
EXECUTIONID = "test_exec"

import time

# + tags=[]
from datetime import datetime

print("=" * 10)
print(f"JOBID: {JOBID} starting")
print(f"EXECUTIONID: {EXECUTIONID} starting")
print("=" * 10)
print(f"SLEEP: {SLEEP}")
print(f"ERROR: {ERROR}")

NOW = datetime.utcnow().isoformat()

time.sleep(SLEEP)

if ERROR:
    raise IndexError("Error was requested for this task")
    # 10 / 0
print("Error?", ERROR)

print(f"Task {JOBID} finished")
