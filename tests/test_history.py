import pytest
from pytest_mock import MockerFixture

from .factories import create_history_request


@pytest.mark.asyncio
async def test_history_bp_create(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    mocker.patch("nb_workflows.web.history_bp.history_mg.create", return_value=5)
    hreq = create_history_request()
    req, res = await sanic_app.asgi_client.post(
        "/histories",
        json=hreq.dict(),
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res.status_code == 201
