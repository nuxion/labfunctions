from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from labfunctions import defaults, errors
from labfunctions.executors.execid import ExecID
from labfunctions.hashes import generate_random
from labfunctions.types import ExecutionNBTask, ExecutionResult, NBTask, ServerSettings
from labfunctions.types.runtimes import RuntimeData
from labfunctions.utils import get_version, today_string

WFID_PREFIX = "tmp"


def execid_for_build(size=defaults.EXECID_LEN) -> str:
    return ExecID().firm_with(ExecID.types.build)


def dummy_wfid():
    return f"{WFID_PREFIX}{generate_random(defaults.WFID_LEN - len(WFID_PREFIX))}"


def create_dummy_ctx(projectid, execid=None) -> ExecutionNBTask:
    dummy_id = execid or f"{WFID_PREFIX}.{generate_random(defaults.WFID_LEN)}"
    # pd = ProjectData(name=pname, projectid=projectid)
    task = NBTask(nb_name="welcome", params={})

    ctx = create_notebook_ctx(projectid, task, execid=dummy_id)
    return ctx


def prepare_runtime(runtime: Optional[RuntimeData] = None, gpu_support=False) -> str:
    if not runtime:
        version = get_version()
        _runtime = f"{defaults.DOCKERFILE_IMAGE}:{version}-client"
        if gpu_support:
            _runtime = f"{defaults.DOCKERFILE_IMAGE}:{version}-client-gpu"
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

    wfid = wfid or dummy_wfid()
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
    _runtime = prepare_runtime(runtime, task.gpu_support)
    machine = task.machine or defaults.MACHINE_TYPE
    cluster = task.cluster or defaults.CLUSTER_NAME

    return ExecutionNBTask(
        projectid=projectid,
        wfid=wfid,
        execid=execid,
        nb_name=task.nb_name,
        runtime=_runtime,
        machine=task.machine,
        cluster=cluster,
        params=_params,
        pm_input=str(papermill_input),
        pm_output=f"{output_dir}/{output_name}",
        output_name=output_name,
        output_dir=output_dir,
        error_dir=error_dir,
        today=today,
        timeout=task.timeout,
        gpu_support=task.gpu_support,
        created_at=_now,
        notifications_ok=task.notifications_ok,
        notifications_fail=task.notifications_fail,
    )


def make_error_result(ctx: ExecutionNBTask, elapsed) -> ExecutionResult:
    result = ExecutionResult(
        wfid=ctx.wfid,
        execid=ctx.execid,
        projectid=ctx.projectid,
        name=ctx.nb_name,
        params=ctx.params,
        input_=ctx.pm_input,
        output_dir=ctx.output_dir,
        output_name=ctx.output_name,
        error_dir=ctx.error_dir,
        error=True,
        elapsed_secs=round(elapsed, 2),
        created_at=ctx.created_at,
    )
    return result
