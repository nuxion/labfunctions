from typing import List, Optional

from pydantic import BaseModel

from nb_workflows.types import ProjectData


class UserData(BaseModel):
    user_id: int
    username: str
    scopes: List[str]
    is_superuser: bool = False
    is_active: bool = True
    projects: Optional[List[str]] = None

    # class Config:
    #     orm_mode = True

    def to_dict(self):
        return self.dict()

    @classmethod
    def from_model(cls, user):
        projects = [p.projectid for p in user.projects]

        ud = cls(
            user_id=user.id,
            username=user.username,
            scopes=user.scopes.split(","),
            is_superuser=user.is_superuser,
            is_active=user.is_active,
            projects=projects,
        )
        return ud


class AgentReq(BaseModel):
    agent_name: str
