from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from nb_workflows.core.entities import (
    ExecutionResult,
    HistoryRequest,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowsList,
)


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.1"
    # workflows: Optional[Dict[str, NBTask]] = None
    workflows: Optional[List[NBTask]] = None


class Credentials(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


@dataclass
class WFCreateRsp:
    status_code: int
    msg: Optional[str] = None
    jobid: Optional[str] = None


@dataclass
class ScheduleExecRsp:
    status_code: int
    msg: Optional[str] = None
    executionid: Optional[str] = None


@dataclass
class ScheduleListRsp:
    nb_name: str
    jobid: str
    enabled: bool
    description: Optional[str] = None


@dataclass
class WorkflowRsp:
    enabled: bool
    task: NBTask


class ProjectZipFile(BaseModel):
    filepath: str
    commit: Optional[str]
    current: Optional[bool] = False
