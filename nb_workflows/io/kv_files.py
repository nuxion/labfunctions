from typing import Any, AsyncGenerator, Dict, Generator, Union

import httpx

from .kvspec import AsyncKVSpec, GenericKVSpec


class KVFiles(GenericKVSpec):
    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket

    @property
    def url(self):
        return f"{self._opts['url']}/{self._bucket}"

    def put(self, key: str, bdata: bytes):
        ts = self._opts.get("timeout", 60)
        with httpx.Client(timeout=ts) as client:
            r = client.put(f"{self.url}/{key}", content=bdata)
        if r.status_code == 201:
            return True
        return False

    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        ts = self._opts.get("timeout", 60)
        with httpx.Client(timeout=ts) as client:
            r = client.put(f"{self.url}/{key}", content=generator())
        if r.status_code == 201:
            return True
        return False

    def get(self, key: str) -> Union[bytes, None]:
        with httpx.Client() as client:
            r = client.get(f"{self.url}/{key}")
        if r.status_code == 200:
            return r.content
        return None

    def get_stream(self, key: str) -> Generator[bytes, None, None]:

        with httpx.Client() as client:
            with client.stream("GET", f"{self.url}/{key}") as r:
                for raw in r.iter_raw():
                    yield raw


class AsyncKVFiles(AsyncKVSpec):
    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket

    @property
    def url(self):
        return f"{self._opts['url']}/{self._bucket}"

    async def put(self, key: str, bdata: bytes):
        async with httpx.AsyncClient() as client:
            r = await client.put(f"{self.url}/{key}", content=bdata)
            if r.status_code == 201:
                return True
        return False

    async def put_stream(
        self, key: str, generator: Generator[bytes, None, None]
    ) -> bool:
        ts = self._opts.get("timeout", 60)
        async with httpx.AsyncClient(timeout=ts) as client:
            r = await client.put(f"{self.url}/{key}", content=generator)
            if r.status_code == 201:
                return True
        return False

    async def get(self, key: str) -> Union[bytes, None]:
        ts = self._opts.get("timeout", 60)
        async with httpx.AsyncClient(timeout=ts) as client:
            r = await client.get(f"{self.url}/{key}")
            return r.content

    async def get_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        u = f"{self.url}/{key}"
        ts = self._opts.get("timeout", 60)
        async with httpx.AsyncClient(timeout=ts) as client:
            async with client.stream("GET", u) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk
