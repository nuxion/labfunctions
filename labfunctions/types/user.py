from typing import List, Optional

from pydantic import BaseModel

from .security import JWTResponse


class UserOrm(BaseModel):
    username: str
    id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[bytes] = None
    scopes: str = "user:r:w"
    is_superuser: bool = False
    is_active: bool = False
    is_agent: bool = False
    projects: List[str] = []

    class Config:
        orm_mode = True


class AgentReq(BaseModel):
    agent_name: str


class AgentJWTResponse(BaseModel):
    agent_name: str
    creds: JWTResponse
