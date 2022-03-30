from typing import Optional

from pydantic import BaseModel


class EventSSE(BaseModel):
    data: str
    event: Optional[str] = None
    id: Optional[str] = None
