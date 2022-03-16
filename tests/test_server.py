import pytest
from sanic import Sanic, response

from nb_workflows import server
from nb_workflows.db.nosync import AsyncSQL


def test_server_app():
    assert isinstance(server.app, Sanic)
    # assert isinstance(server.app.ctx.db, AsyncSQL)


@pytest.mark.asyncio
async def test_server_status(sanic_app):
    req, res = await sanic_app.asgi_client.get("/status")

    assert res.status == 200
    assert res.json["msg"] == "We are ok"
