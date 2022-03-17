import pytest
from sanic import Sanic, response


@pytest.mark.asyncio
async def test_auth_authenticate(async_session, sanic_app):
    user_pass = {"username": "admin_test", "password": "meolvide"}
    req, res = await sanic_app.asgi_client.post("/auth", json=user_pass)

    assert res.status == 200
    assert res.json.get("access_token")
