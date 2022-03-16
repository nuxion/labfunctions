from typing import List, Optional

from pydantic import BaseModel

from .core import NBTask, ProjectData, SeqPipe


class Pipelines(BaseModel):
    sequences: Optional[List[SeqPipe]] = []


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[List[NBTask]] = []
    pipelines: Optional[Pipelines] = Pipelines()
