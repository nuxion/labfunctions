from datetime import datetime
from typing import Any, Dict, Optional

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


class DockerResources(BaseModel):
    mem_limit: Optional[int] = None
    mem_reservation: Optional[int] = None


class DockerVolume(BaseModel):
    orig_mount: str
    dst_mount: str
    extra: Dict[str, Any] = {}


class DockerRunResult(BaseModel):
    msg: str
    status: int


class DockerfileImage(BaseModel):
    maintener: str
    image: str
    user: Dict[str, int] = {"uid": 1089, "gid": 1090}
    build_packages: str = "build-essential libopenblas-dev git"
    final_packages: Optional[str] = None


class RuntimeVersionOrm(BaseModel):
    docker_name: str
    version: str
    project_id: str
    created_at: datetime
    id: Optional[int] = None

    class Config:
        orm_mode = True


class RuntimeVersionData(BaseModel):
    docker_name: str
    version: str
    projectid: str
    id: Optional[int] = None
