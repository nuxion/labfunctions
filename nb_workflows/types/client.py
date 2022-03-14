from typing import List, Optional

from pydantic import BaseModel

from .core import NBTask, ProjectData


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.1"
    workflows: Optional[List[NBTask]] = None
