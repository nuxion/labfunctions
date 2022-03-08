from dataclasses import asdict, dataclass
from typing import List, Optional

from pydantic import BaseModel

from nb_workflows.types import ProjectData


class GroupData(BaseModel):
    name: str


class UserData(BaseModel):
    user_id: int
    username: str
    is_superuser: bool = False
    is_active: bool = True
    groups: Optional[List[GroupData]] = None
    projects: Optional[List[ProjectData]] = None

    def to_dict(self):
        return self.dict()
