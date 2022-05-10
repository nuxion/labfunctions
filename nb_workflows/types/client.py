from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel

from .core import NBTask, WorkflowDataWeb
from .projects import ProjectData


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[Dict[str, WorkflowDataWeb]] = {}


@dataclass
class WFCreateRsp:
    status_code: int
    msg: Optional[str] = None
    wfid: Optional[str] = None


@dataclass
class ScheduleExecRsp:
    status_code: int
    msg: Optional[str] = None
    execid: Optional[str] = None


@dataclass
class ScheduleListRsp:
    nb_name: str
    wfid: str
    enabled: bool
    description: Optional[str] = None


@dataclass
class WorkflowRsp:
    enabled: bool
    task: NBTask
