from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel


class ProjectData(BaseModel):
    name: str
    projectid: str
    # username: Optional[str] = None
    owner: Optional[str] = None
    agent: Optional[str] = None  # to deprecate
    users: Optional[List[str]] = None
    description: Optional[str] = None
    repository: Optional[str] = None

    class Config:
        orm_mode = True


@dataclass
class ProjectReq:
    name: str
    private_key: str
    projectid: Optional[str] = None
    description: Optional[str] = None
    repository: Optional[str] = None


class ProjectBuildReq(BaseModel):
    """
    In the future remote path could be offered like S3, GoogleStore...
    and so on, right now is managed by the server.
    """

    name: str
    server_handle: bool = True
    remote_path: Optional[str] = None


class ProjectBuildResp(BaseModel):
    msg: str
    execid: str


class ProjectCreated(BaseModel):
    pd: ProjectData
    private_key: str
