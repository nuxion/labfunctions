from typing import Optional

from pydantic import BaseModel


class DockerBuildLowLog(BaseModel):
    logs: str
    error: bool


class DockerPushLog(BaseModel):
    logs: str
    error: bool


class DockerBuildLog(BaseModel):
    build_log: DockerBuildLowLog
    push_log: Optional[DockerPushLog] = None
    error: bool
