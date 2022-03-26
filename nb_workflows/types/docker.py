from typing import Dict, Optional

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


class DockerfileImage(BaseModel):
    maintener: str
    image: str
    user: Dict[str, int] = {"uid": 1089, "gid": 1090}
    build_packages: str = "build-essential libopenblas-dev git"
    final_packages: Optional[str] = None
