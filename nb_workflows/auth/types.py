from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class GroupData:
    name: str


@dataclass
class UserData:
    user_id: int
    username: str
    is_superuser: bool = False
    is_active: bool = True
    groups: Optional[List[GroupData]] = None

    def to_dict(self):
        return asdict(self)
