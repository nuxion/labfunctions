from typing import List

import httpx

from nb_workflows.io.types import FileFileserver


class Fileserver:
    def __init__(self, addr: str, bucket=None):
        self._addr = addr
        self.bucket = bucket

    def _set_fullurl(self, rpath):
        if self.bucket:
            return f"{self._addr}/{self.bucket}/{rpath}"
        return f"{self._addr}/{rpath}"

    def get(self, rpath) -> bytes:
        with httpx.Client() as client:
            r = client.get(self._set_fullurl(rpath))

        return r.content

    def put(self, rpath: str, data: bytes):
        with httpx.Client() as client:
            r = client.put(self._set_fullurl(rpath), content=data)

        return r.content

    def delete(self, rpath):
        with httpx.Client() as client:
            r = client.delete(self._set_fullurl(rpath))

    def list_object(self, rpath):
        pass


class AsyncFileserver:
    def __init__(self, addr: str, bucket=None):
        self._addr = addr
        self.bucket = bucket

    def _set_fullurl(self, rpath):
        if self.bucket:
            return f"{self._addr}/{self.bucket}/{rpath}"
        return f"{self._addr}/{rpath}"

    async def get(self, rpath) -> bytes:
        async with httpx.AsyncClient() as client:
            r = await client.get(self._set_fullurl(rpath))

        return r.content

    async def put(self, rpath: str, data: bytes):
        async with httpx.AsyncClient() as client:
            r = await client.put(self._set_fullurl(rpath), content=data)

    async def delete(self, rpath: str):
        async with httpx.AsyncClient() as client:
            r = await client.delete(f"{self._addr}/{rpath}")

    async def list_objects(self, rpath) -> List[FileFileserver]:
        async with httpx.AsyncClient() as client:
            r = await client.get(self._set_fullurl(rpath), follow_redirects=True)
        return [FileFileserver(**f) for f in r.json()]
