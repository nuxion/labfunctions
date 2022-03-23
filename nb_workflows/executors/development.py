import json
import os
from typing import Union

from nb_workflows import client
from nb_workflows.conf import defaults
from nb_workflows.conf.client_settings import settings
from nb_workflows.types import ExecutionNBTask, ExecutionResult, NBTask, ScheduleData
from nb_workflows.utils import set_logger

from .context import (
    ExecID,
    create_notebook_ctx,
    create_notebook_ctx_ondemand,
    generate_execid,
)
from .local import local_exec_env, notebook_executor


def local_dev_exec(wfid) -> Union[ExecutionResult, None]:
    """Without server interaction
    wfid will be searched in the workflows file
    """
    logger = set_logger("local_exec", level=settings.LOGLEVEL)
    logger.info(f"Runing {wfid}")
    # nb_client = client.from_file("workflows.yaml")

    dc = client.from_file()
    for _, w in dc.state.workflows.items():
        if w.wfid == wfid:
            _execid = f"loc.{generate_execid(4)}"
            ctx = create_notebook_ctx(dc.state.project, w, _execid)

            exec_res = notebook_executor(ctx)
            # nb_client.register_history(exec_res, task)
            return exec_res
    print(f"{wfid} not found in workflows.yaml")
    return None


def local_nb_dev_exec(task: NBTask) -> Union[ExecutionResult, None]:
    dc = client.from_file()

    nb_ctx = create_notebook_ctx_ondemand(dc.state.project, task)
    os.environ[defaults.EXECUTIONTASK_VAR] = json.dumps(nb_ctx.dict())
    os.environ["DEBUG"] = True
    res = local_exec_env()
    return res
