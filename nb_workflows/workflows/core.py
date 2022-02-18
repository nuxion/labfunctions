import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import papermill as pm
from nb_workflows.conf import Config
from nb_workflows.hashes import Hash96
from nb_workflows.utils import today_string
from nb_workflows.workflows.registers import job_history_register

_NB_OUTPUT = f"{Config.BASE_PATH}/{Config.NB_OUTPUT}"
_NB_WORKFLOWS = f"{Config.BASE_PATH}/{Config.NB_WORKFLOWS}"


@dataclass
class ExecutionTask:
    """ It will be send to task_handler, and it has the
    configuration needed for papermill to run a specific notebook.
    """
    jobid: str
    executionid: str
    name: str
    params: Dict[str, Any]
    workflow: str
    output: str
    created_at: str


@dataclass
class ExecutionResult:
    """
    Is the result of a ExecutionTask execution.
    """
    executionid: str
    jobid: str
    name: str
    params: Dict[str, Any]
    input_: str
    output_name: str
    output_dir: str
    error_dir: str
    error: bool
    elapsed: float
    created_at: str


@dataclass
class NBTask:
    """
    NBTask is the task definition. It will be executed by papermill.
    This interface is used together with the ScheduleCron or ScheduleInterval
    to define a job.

    :param nb_name: is the name of the notebook to run
    :param params: a dict with the params to run the specific notebook, wrapper around papermill.
    :param jobid: jobid from ScheduleModel
    :param timeout: time in secs to wait from the start of the task to mark the task as failed.
    :param notificate: by default if the job fails it will send a notification though discord,
    but internally the task also send a notification if the user wants.
    """

    nb_name: str
    params: Dict[str, Any]
    jobid: Optional[str] = None
    timeout: int = 10800  # secs 3h default
    notificate: bool = False


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
        print(f"Task {etask.taskid} failed", e)
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
        elapsed=round(elapsed, 2),
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

    job_history_register(execution_result, nb_task)

    return execution_result
