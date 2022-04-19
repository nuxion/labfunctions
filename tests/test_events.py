import json

import aioredis
import pytest
from pytest_mock import MockerFixture

from nb_workflows.defaults import API_VERSION
from nb_workflows.events import EventManager
from nb_workflows.types.events import EventSSE

from .factories import EventSSEFactory

version = API_VERSION


def test_events_EventManager(async_redis_web: aioredis.client.Redis):
    em = EventManager(async_redis_web)
    assert isinstance(em.redis, aioredis.client.Redis)


@pytest.mark.asyncio
async def test_events_EventManager_read(async_redis_web: aioredis.client.Redis):
    await async_redis_web.xadd(
        "test.test", fields={"msg": "testing stream", "event": "pytest"}
    )
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


def test_events_EventManager_format_sse():
    evt = EventSSEFactory()
    msg = EventManager.format_sse(evt)
    compare = ""
    for d in msg.split("\n"):
        if d.startswith("data:"):
            compare = d.split(":")[1].strip()
            break

    assert compare == evt.data


def test_events_EventManager_from_sse2event():
    evt = EventSSEFactory()
    evt.id = "test_id"
    evt.event = "event_test"
    msg = EventManager.format_sse(evt)
    compare_evt = EventManager.from_sse2event(msg)

    assert compare_evt.data == evt.data
    assert compare_evt.id == evt.id
    assert compare_evt.event == evt.event


@pytest.mark.asyncio
async def test_events_bp_publish(async_session, sanic_app, access_token):
    evt = EventSSEFactory()

    req, res = await sanic_app.asgi_client.post(
        f"{version}/events/test/test/_publish",
        json=evt.dict(),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 204


@pytest.mark.asyncio
async def test_events_bp_listen(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):
    # await async_redis_web.xadd("test.test", fields={"msg": "testing stream",
    # "event": "pytest"})

    evt = EventSSEFactory()
    evt_exit = EventSSEFactory(event="control", data="exit")
    event_mg = mocker.MagicMock()
    event_mg.generate_channel.return_value = "test.test"

    mocker.patch(
        "nb_workflows.web.events_bp.EventManager.read", side_effect=[[evt], [evt_exit]]
    )

    req, res = await sanic_app.asgi_client.get(
        f"{version}/events/test/test/_listen?last=1123123",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 200
    assert "data" in res.text


@pytest.mark.asyncio
async def test_events_bp_listen_none(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):
    # await async_redis_web.xadd("test.test", fields={"msg": "testing stream",
    # "event": "pytest"})

    evt = EventSSEFactory()
    evt_exit = EventSSEFactory(event="control", data="exit")
    event_mg = mocker.MagicMock()
    event_mg.generate_channel.return_value = "test.test"

    mocker.patch("nb_workflows.web.events_bp.EventManager.read", return_value=None)

    req, res = await sanic_app.asgi_client.get(
        f"{version}/events/test/test/_listen?last=0",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 200
