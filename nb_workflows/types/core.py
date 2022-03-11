from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class ScheduleData:
    """Used as generic structure when querying database"""

    start_in_min: int = 0
    repeat: Optional[int] = None
    cron: Optional[str] = None
    interval: Optional[str] = None


@dataclass
class NBTask:
    """
    NBTask is the task definition. It will be executed by papermill.
    This interface is used together with the ScheduleCron or ScheduleInterval
    to define a job.

    :param nb_name: is the name of the notebook to run
    :param params: a dict with the params to run the specific notebook,
    wrapper around papermill.
    :param jobid: jobid from WorkflowModel
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
    alias: Optional[str] = None
    description: Optional[str] = None
    jobid: Optional[str] = None
    timeout: int = 10800  # secs 3h default
    notifications_ok: Optional[List[str]] = None
    notifications_fail: Optional[List[str]] = None
    schedule: Optional[ScheduleData] = None


class ExecutionNBTask(BaseModel):
    """It will be send to task_handler, and it has the
    configuration needed for papermill to run a specific notebook.
    """

    projectid: str
    jobid: str
    executionid: str
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
    executionid: str
    jobid: str
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
    jobid: str
    executionid: str
    execution_dt: str


@dataclass
class HistoryResult:
    jobid: str
    # posible status: queued, started, deferred,
    # finished, stopped, scheduled, canceled, failed.
    status: int
    result: Optional[ExecutionResult] = None
    executionid: Optional[str] = None
    created_at: Optional[str] = None


class HistoryRequest(BaseModel):
    task: NBTask
    result: ExecutionResult


class ProjectData(BaseModel):
    name: str
    projectid: str
    username: Optional[str] = None
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


@dataclass
class WorkflowData:
    jobid: str
    nb_name: str
    job_detail: Dict[str, Any]
    enabled: bool
    alias: Optional[str] = None


@dataclass
class WorkflowsList:
    rows: List[WorkflowData]
