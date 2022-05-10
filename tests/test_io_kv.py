import tempfile
from io import BytesIO

import pytest

from labfunctions.io.kv_local import AsyncKVLocal, KVLocal
from labfunctions.io.kvspec import AsyncKVSpec, GenericKVSpec


def write_stream():
    for x in range(10):
        yield str(x).encode()


def test_io_kv_factory():
    kv = GenericKVSpec.create("labfunctions.io.kv_local.KVLocal", "test")
    kv_async = AsyncKVLocal.create("labfunctions.io.kv_local.AsyncKVLocal", "test")

    assert isinstance(kv, KVLocal)
    assert isinstance(kv_async, AsyncKVLocal)


def test_io_kv_local_rw():
    with tempfile.TemporaryDirectory() as f:
        kv = KVLocal(f)
        kv.put("test", b"hello world")
        res = kv.get("test")

    assert res == b"hello world"


def test_io_kv_local_stream_rw():

    with tempfile.TemporaryDirectory() as f:
        kv = KVLocal(f)
        kv.put_stream("test", write_stream())
        obj = BytesIO()
        for chunk in kv.get_stream("test"):
            obj.write(chunk)
        value = obj.getvalue().decode()

    assert "0" in value


@pytest.mark.asyncio
async def test_io_kv_local_async_rw():
    with tempfile.TemporaryDirectory() as f:
        kv = AsyncKVLocal(f)
        await kv.put("test", b"hello world")
        res = await kv.get("test")

    assert res == b"hello world"


@pytest.mark.asyncio
async def test_io_kv_local_async_stream_rw():
    with tempfile.TemporaryDirectory() as f:
        kv = AsyncKVLocal(f)
        await kv.put_stream("test", write_stream())
        obj = BytesIO()
        async for chunk in kv.get_stream("test"):
            obj.write(chunk)
        value = obj.getvalue().decode()

    assert "0" in value
