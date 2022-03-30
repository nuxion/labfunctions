from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .docker import DockerfileImage


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
    :param wfid: wfid from WorkflowModel
    :param timeout: time in secs to wait from the start of the task
    to mark the task as failed.
    :param notifications_ok: If ok send a notification to discord or slack.
    :param notifications_fail: If not ok, send notification to discord or slack.
    but internally the task also send a notification if the user wants.
    """

    nb_name: str
    params: Dict[str, Any]
    # output_ok: str "fileserver://outputs/ok"
    # output_fail = "fileserver://outputs/errors"

    machine: str = "default"
    docker_version: Optional[str] = "latest"

    enabled: bool = True
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
    machine: str
    docker_name: str
    # folders:
    pm_input: str
    pm_output: str
    output_name: str

    output_dir: str
    error_dir: str

    today: str
    timeout: int
    created_at: str


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
    output_name: str
    output_dir: str
    error_dir: str
    error: bool
    elapsed_secs: float
    created_at: str


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


class ProjectData(BaseModel):
    name: str
    projectid: str
    # username: Optional[str] = None
    owner: Optional[str] = None
    agent: Optional[str] = None
    users: Optional[List[str]] = None
    description: Optional[str] = None
    repository: Optional[str] = None

    class Config:
        orm_mode = True


@dataclass
class ProjectReq:
    name: str
    private_key: str
    projectid: Optional[str] = None
    description: Optional[str] = None
    repository: Optional[str] = None


@dataclass
class ProjectWebRsp:
    name: str
    created_at: str
    updated_at: str
    username: Optional[str] = None
    description: Optional[str] = None
    repository: Optional[str] = None


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
