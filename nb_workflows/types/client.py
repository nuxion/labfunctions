from typing import List, Optional

from pydantic import BaseModel

from .core import NBTask, ProjectData, SeqPipe


class Pipelines(BaseModel):
    sequences: Optional[List[SeqPipe]] = None


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[List[NBTask]] = None
    pipelines: Optional[Pipelines] = None
