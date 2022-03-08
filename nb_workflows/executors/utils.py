from datetime import datetime
from pathlib import Path

from nb_workflows.conf import defaults
from nb_workflows.hashes import Hash96, generate_random
from nb_workflows.types import ExecutionResult, ExecutionTask2, NBTask
from nb_workflows.utils import today_string


def generate_execid(size):
    """
    executionid refers to an unique id randomly generated for each execution
    of a workflow. It can be thought of as the id of an instance
    of the NB Workflow definition.
    """
    # return Hash96.time_random_string().id_hex
    return generate_random(size=size)


def create_exec_ctx(projectid, jobid, task: NBTask, execid_size=10) -> ExecutionTask2:

    # root = Path.cwd()
    root = Path(defaults.WORKFLOWS_FOLDER_NAME)
    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()
    execid = generate_execid(execid_size)

    # if not execid:
    #    _hash = Hash96.time_random_string()
    #    execid = _hash.id_hex

    _params = task.params.copy()
    _params["JOBID"] = jobid
    _params["EXECUTIONID"] = execid
    _params["NOW"] = _now

    nb_filename = f"{task.nb_name}.ipynb"

    papermill_input = str(root / nb_filename)

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
