import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, Union

import aiofiles
from smart_open import open as sopen

from labfunctions.utils import mkdir_p

from .kvspec import AsyncKVSpec, GenericKVSpec, KeyReadError, KeyWriteError


class KVLocal(GenericKVSpec):
    """https://googleapis.dev/python/storage/latest/client.html"""

    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket
        self._root = client_opts.get("root", "/tmp/labstore")
        mkdir_p(f"{self._root}/{self._bucket}")

    def uri(self, key):
        return f"{self._root}/{self._bucket}/{key}"

    def put(self, key: str, bdata: bytes):
        # obj = io.BytesIO(bdata)
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            with sopen(uri, "wb") as f:
                f.write(bdata)
        except Exception as e:
            raise KeyWriteError(self._bucket, key, str(e))

    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            with sopen(uri, "wb") as f:
                for chunk in generator:
                    f.write(chunk)
        except Exception as e:
            raise KeyWriteError(self._bucket, key, str(e))

        return True

    def get(self, key: str) -> Union[bytes, None]:
        uri = self.uri(key)
        try:
            with sopen(uri, "rb") as f:
                obj = f.read()
                return obj
        except Exception as e:
            raise KeyReadError(self._bucket, key, str(e))

    def from_file_gen(self, fpath) -> Generator[bytes, None, None]:
        for chunk in sopen(fpath, "rb"):
            yield chunk

    def get_stream(self, key: str) -> Generator[bytes, None, None]:
        uri = self.uri(key)
        try:
            for chunk in sopen(uri, "rb"):
                yield chunk
        except Exception as e:
            raise KeyReadError(self._bucket, key, str(e))


class AsyncKVLocal(AsyncKVSpec):
    """For local usage and testing"""

    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket
        self._root = client_opts.get("root", "/tmp/labstore")
        mkdir_p(f"{self._root}/{self._bucket}")

    def uri(self, key):
        return f"{self._root}/{self._bucket}/{key}"

    async def put(self, key: str, bdata: bytes):
        uri = self.uri(key)
        mkdir_p(Path(uri).parent)
        try:
            async with aiofiles.open(uri, mode="wb") as f:
                await f.write(bdata)
        except Exception as e:
            raise KeyWriteError(self._bucket, key, str(e))

    async def put_stream(
        self, key: str, generator: Generator[bytes, None, None]
    ) -> bool:
        uri = self.uri(key)
        mkdir_p((Path(uri).parent).resolve())
        try:
            async with aiofiles.open(uri, mode="wb") as f:
                async for data in generator:
                    await f.write(data)
        except Exception as e:
            raise KeyWriteError(self._bucket, key, str(e))

        return True

    async def get(self, key: str) -> Union[bytes, str, None]:
        uri = self.uri(key)
        try:
            async with aiofiles.open(uri, mode="rb") as f:
                data = await f.read()
                return data
        except Exception as e:
            raise KeyReadError(self._bucket, key, str(e))

    async def get_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        """PEP 0525 for Asynchronous generators"""
        uri = self.uri(key)
        try:
            async with aiofiles.open(uri, mode="rb") as f:
                while True:
                    data = await f.read(1024)
                    if not data:
                        break
                    yield data

        except Exception as e:
            raise KeyReadError(self._bucket, key, str(e))
