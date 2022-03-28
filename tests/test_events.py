import json

import aioredis
import pytest

from nb_workflows.events import EventManager
from nb_workflows.types.events import EventSSE

from .factories import EventSSEFactory


def test_events_EventManager(async_redis_web: aioredis.client.Redis):
    em = EventManager(async_redis_web)
    assert isinstance(em.redis, aioredis.client.Redis)


@pytest.mark.asyncio
async def test_events_EventManager_read(async_redis_web: aioredis.client.Redis):
    await async_redis_web.xadd("test.test", fields={"msg": "testing stream"})
    em = EventManager(async_redis_web)
    rsp = await em.read("test.test", "0", block_ms=1)
    rsp_none = await em.read("test.test", "$", block_ms=1)

    assert isinstance(rsp[0], EventSSE)
    assert rsp[0].data == "testing stream"
    assert not rsp_none


@pytest.mark.asyncio
async def test_events_EventManager_publish(async_redis_web: aioredis.client.Redis):
    em = EventManager(async_redis_web)
    evt = EventSSEFactory()
    rsp = await em.publish("test.test", evt, ttl_secs=1)
    assert rsp


def test_events_EventManager_generate_channel():
    key = EventManager.generate_channel("project", "execid")
    assert key == "project.execid"


def test_events_format_sse():
    evt = EventSSEFactory()
    msg = EventManager.format_sse(evt)
    compare = ""
    for d in msg.split("\n"):
        if d.startswith("data:"):
            compare = d.split(":")[1].strip()
            break

    assert compare == evt.data


@pytest.mark.asyncio
async def test_events_bp_publish(async_session, sanic_app):
    evt = EventSSEFactory()
    req, res = await sanic_app.asgi_client.post(
        "/events/test/test/_publish", json=evt.dict()
    )

    assert res.status_code == 204


@pytest.mark.asyncio
async def test_events_bp_listen(async_session, sanic_app, async_redis_web):
    await async_redis_web.xadd("test.test", fields={"msg": "testing stream"})

    evt = EventSSEFactory()
    req, res = await sanic_app.asgi_client.get("/events/test/test/_listen?last=0")

    assert res.status_code == 200
    assert "data" in res.text
