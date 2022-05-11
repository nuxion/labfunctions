import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Union

from labfunctions import client, defaults
from labfunctions.conf import load_client
from labfunctions.types import ExecutionNBTask, ExecutionResult, NBTask

from .nbtask_base import NBTaskLocal

# from labfunctions.notebooks import nb_job_executor


def local_exec_env() -> ExecutionResult:
    """
    Control the notebook execution.
    TODO: implement notifications
    TODO: base executor class?
    """
    # Init
    nbclient = client.from_env()
    runner = NBTaskLocal(nbclient)
    ctx_str = os.getenv(defaults.EXECUTIONTASK_VAR)

    etask = ExecutionNBTask(**json.loads(ctx_str))
    result = runner.run(etask)

    if not os.getenv("LF_LOCAL"):
        runner.register(result)

    return result
