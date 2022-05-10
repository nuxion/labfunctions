import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Union

from nb_workflows import client, defaults
from nb_workflows.conf import load_client
from nb_workflows.types import ExecutionNBTask, ExecutionResult, NBTask

from .nbtask_base import NBTaskLocal

# from nb_workflows.notebooks import nb_job_executor


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

    if not os.getenv("DEBUG"):
        runner.register(result)

    return result
