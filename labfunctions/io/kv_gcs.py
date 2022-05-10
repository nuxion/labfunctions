import io
import os
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, Generator, Union

from google.cloud.storage import Client
from smart_open import open

from labfunctions.utils import run_async

from .kvspec import AsyncKVSpec, GenericKVSpec


class KVGS(GenericKVSpec):
    """https://googleapis.dev/python/storage/latest/client.html"""

    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket
        service_account_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        self.client = Client.from_service_account_json(service_account_path)
        self.bucket = self.client.get_bucket(bucket)
        self.params = {"client": self.client}

    @property
    def uri(self):
        return f"gs://{self._bucket}"

    def put(self, key: str, bdata: bytes):
        # obj = io.BytesIO(bdata)
        blob = self.bucket.blob(key)
        blob.upload_from_string(bdata, content_type="application/octet-stream")

    def _writer(self, key: str, generator: Generator[bytes, None, None]):
        with open(f"{self.uri}/{key}", "wb", transport_params=self.params) as f:
            data = True
            while data:
                try:
                    _data = generator.__next__()
                    f.write(_data)
                except StopIteration:
                    data = False

    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        rsp = True
        try:
            self._writer(key, generator)
        except Exception:
            rsp = False
        return rsp

    def get(self, key: str) -> Union[bytes, None]:
        blob = self.bucket.blob(key)
        obj = None
        try:
            obj = blob.download_as_bytes()
        except Exception:
            pass
        return obj

    def get_stream(self, key: str) -> Generator[bytes, None, None]:
        uri = f"{self.uri}/{key}"
        for chunk in open(uri, "rb", transport_params=self.params):
            yield chunk


class AsyncKVGS(AsyncKVSpec):
    """A hacky solution because thereisn't trustworthy async lib"""

    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket
        self.client = KVGS(bucket, client_opts)

    async def put(self, key: str, bdata: bytes):
        await run_async(self.client.put, key, bdata)

    async def put_stream(
        self, key: str, generator: Generator[bytes, None, None]
    ) -> bool:
        rsp = await run_async(self.client.put_stream, key, generator)
        return rsp

    async def get(self, key: str) -> Union[bytes, str, None]:
        rsp = await run_async(self.client.get, key)
        return rsp

    async def get_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        yield await run_async(self.client.get_stream, key)
