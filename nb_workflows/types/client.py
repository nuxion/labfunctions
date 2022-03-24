from typing import Dict, List, Optional

from pydantic import BaseModel

from .core import NBTask, ProjectData, WorkflowDataWeb
from .docker import DockerfileImage


class WorkflowsFile(BaseModel):
    project: ProjectData
    version: str = "0.2"
    workflows: Optional[Dict[str, WorkflowDataWeb]] = {}
    runtime: Optional[DockerfileImage] = None
