from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from labfunctions import defaults

from .docker import DockerfileImage
from .projects import ProjectData


class ScheduleData(BaseModel):
    """Used as generic structure when querying database"""

    start_in_min: int = 0
    repeat: Optional[int] = None
    cron: Optional[str] = None
    interval: Optional[str] = None


class NBTask(BaseModel):
    """
    NBTask is the task definition. It will be executed by papermill.
    This interface is used together with the ScheduleCron or ScheduleInterval
    to define a job.

    :param nb_name: is the name of the notebook to run
    :param params: a dict with the params to run the specific notebook,
    wrapper around papermill.
    :param remote_input: optional to get a remote notebook (not implemented)
    :param remote_output: optional to put in a remote place (not implemented)
    :param runtime: name of the runtime (`runtime_name`)
    :param version: Version of the runtime
    :param machine: where to run
    :param gpu_support: if it needs gpu support
    :param timeout: time in secs to wait from the start of the task
    to mark the task as failed.
    :param notifications_ok: If ok send a notification to discord or slack.
    :param notifications_fail: If not ok, send notification to discord or slack.
    but internally the task also send a notification if the user wants.
    """

    nb_name: str
    params: Dict[str, Any]
    remote_input: Optional[str] = None
    remote_output: Optional[str] = None
    runtime: Optional[str] = None
    version: Optional[str] = None
    machine: str = defaults.MACHINE_TYPE
    cluster: str = defaults.CLUSTER_NAME
    gpu_support: bool = False
    description: Optional[str] = None
    timeout: int = 10800  # secs 3h default
    notifications_ok: Optional[List[str]] = None
    notifications_fail: Optional[List[str]] = None
    # schedule: Optional[ScheduleData] = None


class ExecutionNBTask(BaseModel):
    """It will be send to task_handler, and it has the
    configuration needed for papermill to run a specific notebook.
    """

    projectid: str
    wfid: str
    execid: str
    nb_name: str
    params: Dict[str, Any]
    runtime: str
    # folders:
    pm_input: str
    pm_output: str
    output_name: str

    output_dir: str
    error_dir: str

    today: str
    timeout: int
    created_at: str
    gpu_support: bool = False
    cluster: str = defaults.CLUSTER_NAME
    machine: str = defaults.MACHINE_TYPE
    remote_input: Optional[str]
    remote_output: Optional[str]
    notifications_ok: Optional[List[str]] = None
    notifications_fail: Optional[List[str]] = None


class ExecutionResult(BaseModel):
    """
    Is the result of a ExecutionTask execution.
    """

    projectid: str
    execid: str
    wfid: str

    name: str
    params: Dict[str, Any]
    input_: str
    error: bool
    elapsed_secs: float
    created_at: str
    cluster: Optional[str] = None
    machine: Optional[str] = None
    runtime: Optional[str] = None
    docker_name: Optional[str] = None
    output_name: Optional[str] = None
    output_dir: Optional[str] = None
    error_dir: Optional[str] = None
    error_msg: Optional[str] = None


@dataclass
class SimpleExecCtx:
    wfid: str
    execid: str
    execution_dt: str


class HistoryResult(BaseModel):
    wfid: str
    # posible status: queued, started, deferred,
    # finished, stopped, scheduled, canceled, failed.
    status: int
    result: Optional[ExecutionResult] = None
    execid: Optional[str] = None
    created_at: Optional[str] = None


class HistoryRequest(BaseModel):
    task: NBTask
    result: ExecutionResult


class HistoryLastResponse(BaseModel):
    rows: List[HistoryResult]


class WorkflowData(BaseModel):
    wfid: str
    alias: str
    nbtask: Dict[str, Any]
    enabled: bool = True
    schedule: Optional[ScheduleData] = None


class WorkflowDataWeb(BaseModel):
    alias: str
    nbtask: NBTask
    enabled: bool = True
    wfid: Optional[str] = None
    schedule: Optional[ScheduleData] = None


@dataclass
class WorkflowsList:
    rows: List[WorkflowData]


class Labfile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[Dict[str, WorkflowDataWeb]] = {}


class TaskStatus(BaseModel):
    execid: str
    status: str
    queue: str
    retries: int
