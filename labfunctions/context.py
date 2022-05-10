from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from labfunctions import defaults, errors
from labfunctions.executors.execid import ExecID
from labfunctions.types import ExecutionNBTask, ExecutionResult, NBTask
from labfunctions.types.runtimes import RuntimeData
from labfunctions.utils import get_version, today_string

WFID_TMP = "tmp"


def _dummy_wfid():
    wfid = ExecID(size=defaults.WFID_LEN - len(WFID_TMP))
    return f"{WFID_TMP}{wfid}"


def create_dummy_ctx(
    projectid: str, nb_name: str, params: Dict[str, Any] = {}, execid=None
) -> ExecutionNBTask:
    dummy_id = execid or _dummy_wfid()
    task = NBTask(nb_name=nb_name, params=params)

    ctx = create_notebook_ctx(projectid, task, execid=dummy_id)
    return ctx


def prepare_runtime(runtime: Optional[RuntimeData] = None) -> str:
    if not runtime:
        version = get_version()
        _runtime = f"{defaults.DOCKERFILE_IMAGE}:{version}"
    else:
        _runtime = f"{runtime.docker_name}:{runtime.version}"
        if runtime.registry:
            _runtime = f"{runtime.registry}/{runtime}"
    return _runtime


def create_notebook_ctx(
    projectid: str,
    task: NBTask,
    execid: Optional[str] = None,
    runtime: Optional[RuntimeData] = None,
    wfid: Optional[str] = None,
) -> ExecutionNBTask:
    """It creates the execution context of a notebook based on project and workflow data"""
    # root = Path.cwd()
    root = Path(defaults.NOTEBOOKS_DIR)
    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()

    wfid = wfid or _dummy_wfid()
    execid = execid or str(ExecID())

    _params = deepcopy(task.params)
    _params["WFID"] = wfid
    _params["EXECID"] = execid
    _params["NOW"] = _now

    nb_filename = f"{task.nb_name}.ipynb"

    papermill_input = str(root / nb_filename)

    output_dir = f"{defaults.NB_OUTPUTS}/ok/{today}"
    error_dir = f"{defaults.NB_OUTPUTS}/errors/{today}"

    output_name = f"{wfid}.{task.nb_name}.{execid}.ipynb"
    _runtime = prepare_runtime(runtime)
    machine = task.machine or defaults.MACHINE_TYPE

    return ExecutionNBTask(
        projectid=projectid,
        wfid=wfid,
        execid=execid,
        nb_name=task.nb_name,
        runtime=_runtime,
        machine=task.machine,
        params=_params,
        pm_input=str(papermill_input),
        pm_output=f"{output_dir}/{output_name}",
        output_name=output_name,
        output_dir=output_dir,
        error_dir=error_dir,
        today=today,
        timeout=task.timeout,
        created_at=_now,
        notifications_ok=task.notifications_ok,
        notifications_fail=task.notifications_fail,
    )
