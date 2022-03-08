import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import papermill as pm

from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.hashes import Hash96
from nb_workflows.types import ExecutionResult, ExecutionTask, ExecutionTask2, NBTask
from nb_workflows.utils import get_parent_folder, today_string

# from nb_workflows import client
# from nb_workflows.workflows.registers import job_history_register

_NB_OUTPUT = f"{settings.BASE_PATH}/{settings.NB_OUTPUT}"
_NB_WORKFLOWS = f"{settings.BASE_PATH}/{settings.NB_WORKFLOWS}"


def build_workflow_name_path(workflow_dir, workflow_name):
    return f"{workflow_dir}/{workflow_name}.ipynb"


def make_dir(dirpath):
    Path(dirpath).mkdir(parents=True, exist_ok=True)


def make_workflow_task(
    jobid: str,
    name: str,
    params: Dict[str, Any],
    executionid: Optional[str] = None,
    inject_task=True,
    nb_output=_NB_OUTPUT,
    nb_workflows=_NB_WORKFLOWS,
) -> ExecutionTask:
    """
    Taskid could be generate inside the task or from external, when using
    rq scheduling system.
    inject_task param will injects inside of the notebook execution,
    date and taskid
    """
    if not executionid:
        _hash = Hash96.time_random_string()
        executionid = _hash.id_hex
    _now = datetime.utcnow().isoformat()
    _params = params.copy()
    if inject_task:
        _params["JOBID"] = jobid
        _params["EXECUTIONID"] = _hash.id_hex
        _params["NOW"] = _now

    return ExecutionTask(
        jobid=jobid,
        executionid=executionid,
        name=name,
        params=_params,
        workflow=nb_workflows,
        output=nb_output,
        created_at=_now,
    )


def create_agent_exec_ctx(
    projectid, jobid, task: NBTask, execid=None
) -> ExecutionTask2:

    root = Path.cwd()
    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()

    if not execid:
        _hash = Hash96.time_random_string()
        execid = _hash.id_hex

    _params = task.params.copy()
    _params["JOBID"] = jobid
    _params["EXECUTIONID"] = _hash.id_hex
    _params["NOW"] = _now

    nb_filename = f"{task.nb_name}.ipynb"

    papermill_input = root / defaults.WORKFLOWS_FOLDER_NAME / nb_filename

    output_dir = f"{defaults.NB_OUTPUTS}/ok/{today}"
    error_dir = f"{defaults.NB_OUTPUTS}/errors/{today}"

    output_name = f"{task.nb_name}.{execid}.ipynb"

    return ExecutionTask2(
        projectid=projectid,
        jobid=jobid,
        executionid=execid,
        nb_name=task.nb_name,
        params=_params,
        pm_input=str(papermill_input),
        pm_output=f"{output_dir}/{output_name}",
        output_name=output_name,
        output_dir=output_dir,
        error_dir=error_dir,
        today=today,
        created_at=_now,
    )


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
        error_handler2(etask)

    elapsed = time.time() - _started
    return ExecutionResult(
        jobid=etask.jobid,
        executionid=etask.executionid,
        name=etask.name,
        params=etask.params,
        input_=etask.pm_input,
        output_dir=etask.output_dir,
        output_name=etask.output_name,
        error_dir=etask.error_dir,
        error=_error,
        elapsed_secs=round(elapsed, 2),
        created_at=etask.created_at,
    )


def error_handler2(etask: ExecutionTask2):

    error_output = f"{etask.error_dir}/{etask.output_name}"
    Path(error_output).mkdir(parents=True, exist_ok=True)
    shutil.move(etask.pm_output, error_output)


def workflow_executor(projectid, jobid, task: NBTask):
    pass


def task_handler(etask: ExecutionTask) -> ExecutionResult:
    """task_handler is a generic wrapper to execute notebooks
    using papermill. This could be used from dask or standalone.
    """

    _error = False
    _started = time.time()
    today = today_string(format_="day")

    nb_input = build_workflow_name_path(etask.workflow, etask.name)
    output_name = f"{etask.name}.{etask.executionid}.ipynb"
    output_dir = f"{etask.output}/{today}"
    error_dir = f"{etask.output}/errors/{today}"
    print(output_dir)
    make_dir(output_dir)

    nb_output = f"{output_dir}/{output_name}"

    print("Running..", etask.name, etask.jobid)
    try:

        pm.execute_notebook(nb_input, nb_output, parameters=etask.params)
    except pm.exceptions.PapermillExecutionError as e:
        print(f"Task {etask.executionid} failed", e)
        make_dir(error_dir)

        _error = True
        error_handler(nb_output, output_name, error_dir)

    elapsed = time.time() - _started
    return ExecutionResult(
        jobid=etask.jobid,
        executionid=etask.executionid,
        name=etask.name,
        params=etask.params,
        input_=nb_input,
        output_dir=output_dir,
        output_name=output_name,
        error_dir=error_dir,
        error=_error,
        elapsed_secs=round(elapsed, 2),
        created_at=etask.created_at,
    )


def error_handler(nb_output, output_name, error_dir):
    shutil.move(nb_output, f"{error_dir}/{output_name}")


def nb_job_executor(nb_task: NBTask) -> ExecutionResult:
    """This is a top level executor for nb workflows.
    This function is called by RQ Worker.
    First it will prepare the ExecutionTask, then the task will be
    executed by papermill in the task_handler function.

    Finally the task_result is stored in the database.

    TODO: what happens if the JOB RQ dies?
    """

    wt = make_workflow_task(nb_task.jobid, nb_task.nb_name, nb_task.params)

    execution_result: ExecutionResult = task_handler(wt)

    # client = client.from_settings()

    # job_history_register(execution_result, nb_task)

    return execution_result
