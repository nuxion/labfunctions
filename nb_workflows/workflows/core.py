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
class WorkflowTask:
    taskid: str
    name: str
    params: Dict[str, Any]
    workflow: str
    output: str
    created_at: str


@dataclass
class TaskResult:
    taskid: str
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
    :param name: is the name of the notebook to run
    :param params: a dict with the params to run the specific notebook, wrapper around papermill.
    :param jobid: jobid from ScheduleModel
    :param timeout: time in secs to wait from the start of the task to mark the task as failed.
    :param notificate: by default if the job fails it will send a notification though discord,
    but internally the task also send a notification if the user wants.
    """

    name: str
    params: Dict[str, Any]
    jobid: Optional[str] = None
    timeout: int = 10800  # secs 3h default
    notificate: bool = False


def build_workflow_name_path(workflow_dir, workflow_name):
    return f"{workflow_dir}/{workflow_name}.ipynb"


def make_dir(dirpath):
    Path(dirpath).mkdir(parents=True, exist_ok=True)


def make_workflow_task(
    name,
    params,
    taskid=None,
    inject_task=True,
    nb_output=_NB_OUTPUT,
    nb_workflows=_NB_WORKFLOWS,
) -> WorkflowTask:
    """
    Taskid could be generate inside the task or from external, when using
    rq scheduling system.
    inject_task param will injects inside of the notebook execution,
    date and taskid
    """
    if not taskid:
        _hash = Hash96.time_random_string()
        taskid = _hash.id_hex
    _now = datetime.utcnow().isoformat()
    _params = params.copy()
    if inject_task:
        _params["TASKID"] = _hash.id_hex
        _params["NOW"] = _now

    return WorkflowTask(
        taskid=taskid,
        name=name,
        params=_params,
        workflow=nb_workflows,
        output=nb_output,
        created_at=_now,
    )


def task_handler(task: WorkflowTask) -> TaskResult:
    """task_handler is a generic wrapper to execute notebooks
    using papermill. This could be used from dask or standalone.
    """

    _error = False
    _started = time.time()
    today = today_string(format_="day")

    nb_input = build_workflow_name_path(task.workflow, task.name)
    output_name = f"{task.name}.{task.taskid}.ipynb"
    output_dir = f"{task.output}/{today}"
    error_dir = f"{task.output}/errors/{today}"
    print(output_dir)
    make_dir(output_dir)

    nb_output = f"{output_dir}/{output_name}"

    print("Running..", task.name, task.taskid)
    try:

        pm.execute_notebook(nb_input, nb_output, parameters=task.params)
    except pm.exceptions.PapermillExecutionError as e:
        print(f"Task {task.taskid} failed", e)
        make_dir(error_dir)

        _error = True
        error_handler(nb_output, output_name, error_dir)

    elapsed = time.time() - _started
    return TaskResult(
        taskid=task.taskid,
        name=task.name,
        params=task.params,
        input_=nb_input,
        output_dir=output_dir,
        output_name=output_name,
        error_dir=error_dir,
        error=_error,
        elapsed=round(elapsed, 2),
        created_at=task.created_at,
    )


def error_handler(nb_output, output_name, error_dir):
    shutil.move(nb_output, f"{error_dir}/{output_name}")


def nb_job_executor(nb_task: NBTask) -> TaskResult:
    """This is a top level executor for workflows.
    It will try first to get a dask client from the global scope.
    If anything exists, then it will initilize a dask client,
    send the task.. wait until it finish and then, it release the Dask Future
    and close de dask client connection.


    By default, if the Dask Worker dies, the task will restart endless in the dask cluster.
    Therefore, we have at least two ways to avoid this scenario.
    One is closing the driver conn, and the other one, is releasing
    the dask's task reference (a.k.a the future returned by dask client)

    TODO: what happens if the JOB RQ dies?
    """

    wt = make_workflow_task(nb_task.name, nb_task.params)

    task_result: TaskResult = task_handler(wt)

    job_history_register(task_result, nb_task)

    return task_result
