from collections import namedtuple
from datetime import datetime
from pathlib import Path

from nb_workflows import errors
from nb_workflows.conf import defaults
from nb_workflows.hashes import Hash96, generate_random
from nb_workflows.types import (
    ExecutionNBTask,
    ExecutionResult,
    NBTask,
    ProjectData,
    ScheduleData,
)
from nb_workflows.utils import today_string

Steps = namedtuple(
    "Steps", ["start", "build", "dispatcher", "docker", "web", "seqpipe"]
)

# steps are used to prepend for each step in a workflow execution as namespace.
steps = Steps(
    start="0", build="bld", dispatcher="dsp", docker="dck", web="web", seqpipe="seq"
)
firms = Steps(
    start="0", build="bld", dispatcher="dsp", docker="dck", web="web", seqpipe="seq"
)


class ExecID:

    firms = firms

    def __init__(self, execid=None, size=defaults.EXECID_LEN):
        self.id_ = execid or generate_random(size=size)
        self._signed = self.firm("start")

    def firm(self, firm) -> str:
        _name = getattr(self.firms, firm)
        self.signed = f"{_name}.{self.id_}"
        return self.signed

    def pure(self):
        return self.id_

    @classmethod
    def from_str(cls, execid: str):
        return cls(pure_execid(execid))

    def __str__(self):
        return self.id_

    def __repr__(self):
        return self.id_


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
    _id = generate_random(size=size)
    return f"{steps.start}.{_id}"


def pure_execid(execid):
    """clean any NS added to the id"""

    return execid.split(".", maxsplit=1)[1]


def move_step_execid(step: str, execid: str) -> str:
    """replace the actual NS for a newone"""
    id_ = execid.split(".", maxsplit=1)[1]
    return f"{step}.{id_}"


def execid_for_build(size=defaults.EXECID_LEN):
    return f"{steps.build}.{generate_random(size)}"


def generate_docker_name(pd: ProjectData, docker_version: str):
    return f"{pd.username}/{pd.name}:{docker_version}"


def create_notebook_ctx(pd: ProjectData, task: NBTask, execid) -> ExecutionNBTask:
    # root = Path.cwd()
    root = Path(defaults.WORKFLOWS_FOLDER_NAME)
    today = today_string(format_="day")
    _now = datetime.utcnow().isoformat()

    _execid = pure_execid(execid)

    _params = task.params.copy()
    _params["JOBID"] = task.jobid
    _params["EXECUTIONID"] = _execid
    _params["NOW"] = _now

    nb_filename = f"{task.nb_name}.ipynb"

    papermill_input = str(root / nb_filename)

    output_dir = f"{defaults.NB_OUTPUTS}/ok/{today}"
    error_dir = f"{defaults.NB_OUTPUTS}/errors/{today}"

    output_name = f"{task.nb_name}.{_execid}.ipynb"

    docker_name = generate_docker_name(pd, task.docker_version)

    return ExecutionNBTask(
        projectid=pd.projectid,
        jobid=task.jobid,
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


def make_error_result(ctx, elapsed) -> ExecutionResult:
    result = ExecutionResult(
        jobid=ctx.jobid,
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
