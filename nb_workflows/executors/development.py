import json
import os
from typing import Union

from nb_workflows import client
from nb_workflows.client.diskclient import DiskClient
from nb_workflows.client.state import WorkflowsState
from nb_workflows.conf import defaults
from nb_workflows.conf.client_settings import settings
from nb_workflows.secrets import load
from nb_workflows.types import ExecutionNBTask, ExecutionResult, NBTask, ScheduleData
from nb_workflows.utils import set_logger

from .context import (
    ExecID,
    create_notebook_ctx,
    create_notebook_ctx_ondemand,
    generate_execid,
)
from .docker import docker_exec
from .local import local_exec_env, notebook_executor


def context_from_local_state(
    state: WorkflowsState, wfid: str
) -> Union[ExecutionNBTask, None]:
    for _, w in state.workflows.items():
        if w.wfid == wfid:
            _execid = f"loc.{generate_execid(4)}"
            ctx = create_notebook_ctx(state.project, w, _execid)
            return ctx
    return None


def local_dev_exec(wfid) -> Union[ExecutionResult, None]:
    """Without server interaction
    wfid will be searched in the workflows file
    """
    logger = set_logger("local_exec", level=settings.LOGLEVEL)
    logger.info(f"Runing {wfid}")
    # nb_client = client.from_file("workflows.yaml")

    dc = client.from_file()
    ctx = context_from_local_state(dc, wfid)
    if ctx:
        exec_res = notebook_executor(ctx)
        return exec_res
    return None


def local_nb_dev_exec(task: NBTask) -> Union[ExecutionResult, None]:
    dc = client.from_file()

    nb_ctx = create_notebook_ctx_ondemand(dc.state.project, task)
    os.environ[defaults.EXECUTIONTASK_VAR] = json.dumps(nb_ctx.dict())
    os.environ["DEBUG"] = "true"
    res = local_exec_env()
    return res


def local_docker(url_service, from_file, wfid):
    c = client.from_file(from_file, url_service=url_service)
    ctx = context_from_local_state(c.state, wfid)
    if ctx:
        nbvars = load(base_path=settings.BASE_PATH)
        os.environ["NB_AGENT_TOKEN"] = nbvars["AGENT_TOKEN"]
        os.environ["NB_AGENT_REFRESH_TOKEN"] = nbvars["AGENT_REFRESH_TOKEN"]
        os.environ["NB_WORKFLOW_SERVICE"] = url_service
        docker_exec(ctx)
