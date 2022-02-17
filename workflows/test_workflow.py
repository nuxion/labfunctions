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
SLEEP=5
NOW=None
TASKID=None
ERROR=False

# + tags=[]
import time
print("="*10)
print(f"TASKID: {TASKID} starting")
print("="*10)
print(f"SLEEP: {SLEEP}")
print(f"ERROR: {ERROR}")

time.sleep(SLEEP)
# -

if ERROR:
    raise IndexError("Error was requested for this task")
    # 10 / 0
print("Error?", ERROR)

print(f"Task {TASKID} finished")
