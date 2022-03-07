from typing import Optional

from pydantic import BaseModel, Extra


class FileFileserver(BaseModel, extra=Extra.ignore):
    name: str
    mtime: str
    size: Optional[int] = None
