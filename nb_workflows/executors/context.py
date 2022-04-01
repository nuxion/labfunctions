from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from nb_workflows import errors
from nb_workflows.conf import defaults
from nb_workflows.hashes import Hash96, generate_random
from nb_workflows.types import (
    ExecutionNBTask,
    ExecutionResult,
    NBTask,
    ProjectData,
    ScheduleData,
    WorkflowDataWeb,
)
from nb_workflows.types.docker import DockerBuildCtx
from nb_workflows.utils import secure_filename, today_string

WFID_PREFIX = "tmp"


class ExecutionFirms(NamedTuple):
    start: str = "0"
    build: str = "bld"
    dispatcher: str = "dsp"
    docker: str = "dck"
    web: str = "web"
    local: str = "loc"


class ExecID:

    firms = ExecutionFirms()

    def __init__(self, execid=None, size=defaults.EXECID_LEN):
        self._id = execid or generate_random(size=size)
        self._signed = self.firm("start")

    def firm(self, firm) -> str:
        _name = getattr(self.firms, firm)
        self.signed = f"{_name}.{self._id}"
        return self.signed

    def pure(self):
        return self._id

    @classmethod
    def from_str(cls, execid: str):
        try:
            _pure = pure_execid(execid)
        except IndexError:
            _pure = execid
        return cls(_pure)

    def __str__(self):
        return self._id

    def __repr__(self):
        return self._id


def execid_from_str(execid) -> ExecID:
    return ExecID(pure_execid(execid))


def generate_execid(size=defaults.EXECID_LEN) -> str:
    """
    execid refers to an unique id randomly generated for each execution
    of a workflow. It can be thought of as the id of an instance
    of the NB Workflow definition.

    NanoID is used behind, the default len for this is 10 characters
    using a urlsafe alphabet.

    By default:
    EXECID_LEN = 14
    ~20 years needed for %1 collision at 1000 execs per second
    """
    return generate_random(size=size)


def pure_execid(execid):
    """clean any NS added to the id"""

    return execid.split(".", maxsplit=1)[1]


def execid_for_build(size=defaults.EXECID_LEN):
    return f"{ExecID.firms.build}.{generate_random(size)}"


def generate_docker_name(pd: ProjectData, docker_version: str):
    return f"{defaults.DOCKER_AUTHOR}/{pd.name}:{docker_version}".lower()


def dummy_wf_from_nbtask(pd: ProjectData, nbtask: NBTask) -> WorkflowDataWeb:
    alias = generate_random(size=10)

    wfid = f"{WFID_PREFIX}.{generate_random(defaults.WFID_LEN)}"
    return WorkflowDataWeb(alias=alias, nbtask=nbtask, wfid=wfid)


def create_dummy_ctx(projectid, pname, execid=None) -> ExecutionNBTask:
    dummy_id = execid or f"{WFID_PREFIX}.{generate_random(defaults.WFID_LEN)}"
    pd = ProjectData(name=pname, projectid=projectid)
    task = NBTask(nb_name="welcome", params={})
    wd = dummy_wf_from_nbtask(pd, task)
    ctx = create_notebook_ctx(pd, wd, execid=dummy_id)
    return ctx


def create_notebook_ctx_ondemand(pd: ProjectData, task: NBTask) -> ExecutionNBTask:
    wd = dummy_wf_from_nbtask(pd, task)
    _execid = ExecID()
    ctx = create_notebook_ctx(pd, wd, execid=_execid.firm("web"))
    return ctx


def create_notebook_ctx(
    pd: ProjectData, wd: WorkflowDataWeb, execid
) -> ExecutionNBTask:
    """It creates the execution context of a notebook based on project and workflow data"""
    # root = Path.cwd()
    root = Path(defaults.NOTEBOOKS_DIR)
    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()
    wfid = wd.wfid

    task = wd.nbtask

    _execid = pure_execid(execid)

    _params = wd.nbtask.params.copy()
    _params["WFID"] = wfid
    _params["EXECID"] = _execid
    _params["NOW"] = _now

    nb_filename = f"{task.nb_name}.ipynb"

    papermill_input = str(root / nb_filename)

    output_dir = f"{defaults.NB_OUTPUTS}/ok/{today}"
    error_dir = f"{defaults.NB_OUTPUTS}/errors/{today}"

    output_name = f"{task.nb_name}.{_execid}.ipynb"

    docker_name = generate_docker_name(pd, task.docker_version)

    return ExecutionNBTask(
        projectid=pd.projectid,
        wfid=wfid,
        execid=_execid,
        nb_name=task.nb_name,
        machine=task.machine,
        docker_name=docker_name,
        params=_params,
        pm_input=str(papermill_input),
        pm_output=f"{output_dir}/{output_name}",
        output_name=output_name,
        output_dir=output_dir,
        error_dir=error_dir,
        today=today,
        timeout=task.timeout,
        created_at=_now,
    )


def build_upload_uri(pd: ProjectData, version) -> str:
    _name = f"{pd.name}.{version}.zip"
    name = secure_filename(_name)

    root = Path(pd.projectid)

    uri = str(root / "uploads" / name)
    return uri


def create_build_ctx(pd: ProjectData, version) -> DockerBuildCtx:
    _id = execid_for_build()
    uri = build_upload_uri(pd, version)

    zip_name = uri.split("/")[-1]
    _version = secure_filename(version)
    return DockerBuildCtx(
        projectid=pd.projectid,
        zip_name=zip_name,
        project_zip_route=uri,
        version=_version,
        docker_name=f"{defaults.DOCKER_AUTHOR}/{pd.name}",
        execid=_id,
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


# def generate_context(client: Optional[NBClient] = None) -> ExecutionNBTask:
# CTX creation
