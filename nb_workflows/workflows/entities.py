from dataclasses import dataclass
from typing import Any, Dict, Optional, List


@dataclass
class ScheduleData:
    """Used as generic structure when querying database"""

    alias: Optional[str] = None
    start_in_min: int = 0
    repeat: Optional[int] = None
    cron: Optional[str] = None
    interval: Optional[str] = None
    enabled: bool = True


@dataclass
class NBTask:
    """
    NBTask is the task definition. It will be executed by papermill.
    This interface is used together with the ScheduleCron or ScheduleInterval
    to define a job.

    :param nb_name: is the name of the notebook to run
    :param params: a dict with the params to run the specific notebook,
    wrapper around papermill.
    :param jobid: jobid from ScheduleModel
    :param timeout: time in secs to wait from the start of the task
    to mark the task as failed.
    :param notificate: by default if the job fails it will send a
    notification though discord,
    but internally the task also send a notification if the user wants.
    """

    nb_name: str
    params: Dict[str, Any]
    description: Optional[str] = None
    jobid: Optional[str] = None
    qname: str = "default"
    timeout: int = 10800  # secs 3h default
    notifications_ok: Optional[List[str]] = None
    notifications_fail: Optional[List[str]] = None
    # notifications: 
    schedule: Optional[ScheduleData] = None


@dataclass
class ExecutionTask:
    """It will be send to task_handler, and it has the
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
    elapsed_secs: float
    created_at: str


@dataclass
class ExecContext:
    jobid: str
    executionid: str
    execution_dt: str
