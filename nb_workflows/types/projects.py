from typing import Optional

from pydantic import BaseModel


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
