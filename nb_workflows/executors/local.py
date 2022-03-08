import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Union

import papermill as pm

from nb_workflows import client
from nb_workflows.conf import defaults, load_client
from nb_workflows.notebooks import nb_job_executor
from nb_workflows.types import ExecutionResult, ExecutionTask2, NBTask, ScheduleData


def local_exec(jobid) -> Union[ExecutionResult, None]:
    """
    It will run inside docker
    TODO: executionid should be injected
    """

    logger = logging.getLogger(__name__)
    logger.info(f"Runing {jobid}")
    nb_client = client.nb_from_settings_agent()

    try:
        rsp = nb_client.workflows_get(jobid)
        if rsp and rsp.enabled:
            task = NBTask(**rsp.job_detail)
            if task.schedule:
                task.schedule = ScheduleData(**rsp.job_detail["schedule"])
            exec_res = nb_job_executor(task)

            # nb_client.register_history(exec_res, task)
            return exec_res
        # elif not rsp:
        #    nb_client.rq_cancel_job(jobid)
        else:
            logger.warning(f"{jobid} not enabled")
    except KeyError:
        logger.error("Invalid credentials")
    except TypeError:
        logger.error("Something went wrong")
    return None


def local_exec_env() -> Union[ExecutionResult, None]:
    settings = load_client()
    nb_client = client.nb_from_settings_agent()

    ctx_str = os.getenv(defaults.EXECUTIONTASK_VAR)

    execution_task = ExecutionTask2(**json.loads(ctx_str))
    result = notebook_executor(execution_task)

    # send notifs
    # close task


def notebook_executor(etask: ExecutionTask2) -> ExecutionResult:

    _error = False
    _started = time.time()
    logger = logging.getLogger(__name__)

    Path(etask.output_dir).mkdir(parents=True, exist_ok=True)

    logger.info(f"Running.. {etask.nb_name}  {etask.jobid}")
    try:
        pm.execute_notebook(etask.pm_input, etask.pm_output, parameters=etask.params)
    except pm.exceptions.PapermillExecutionError as e:
        logger.error(f"Task {etask.jobid} {etask.executionid} failed {e}")
        _error = True
        error_handler(etask)

    elapsed = time.time() - _started
    return ExecutionResult(
        jobid=etask.jobid,
        executionid=etask.executionid,
        name=etask.nb_name,
        params=etask.params,
        input_=etask.pm_input,
        output_dir=etask.output_dir,
        output_name=etask.output_name,
        error_dir=etask.error_dir,
        error=_error,
        elapsed_secs=round(elapsed, 2),
        created_at=etask.created_at,
    )


def error_handler(etask: ExecutionTask2):

    error_output = f"{etask.error_dir}/{etask.output_name}"
    Path(error_output).mkdir(parents=True, exist_ok=True)
    shutil.move(etask.pm_output, error_output)
