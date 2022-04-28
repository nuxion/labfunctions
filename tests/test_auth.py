import pytest
from sanic import Sanic, response

from .factories import create_user_model2


@pytest.mark.asyncio
async def test_auth_authenticate(async_session, sanic_app):
    user_pass = {"username": "admin_test", "password": "meolvide"}
    req, res = await sanic_app.asgi_client.post("/v1/auth/login", json=user_pass)

    assert res.status == 200
    assert res.json.get("access_token")
    assert res.json.get("refresh_token")


@pytest.mark.asyncio
async def test_auth_verify(async_session, sanic_app, access_token):

    req, res = await sanic_app.asgi_client.get("/v1/auth/verify")

    req, res_auth = await sanic_app.asgi_client.get(
        "/v1/auth/verify", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert res.status == 401
    assert res_auth.status == 200
