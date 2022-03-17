from typing import Dict, List, Optional

from pydantic import BaseModel

from .core import NBTask, ProjectData, SeqPipe


class Pipelines(BaseModel):
    sequences: Optional[List[SeqPipe]] = []


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[Dict[str, NBTask]] = {}
    pipelines: Optional[Pipelines] = Pipelines()
