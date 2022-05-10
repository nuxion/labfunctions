from typing import List, Optional

from pydantic import BaseModel


class WFCreateRsp(BaseModel):
    status_code: int
    alias: str
    msg: Optional[str] = None
    wfid: Optional[str] = None


class WFPushRsp(BaseModel):
    created: Optional[List[WFCreateRsp]] = []
    errors: Optional[List[WFCreateRsp]] = []
