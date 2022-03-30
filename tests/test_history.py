import pytest
from pytest_mock import MockerFixture

from nb_workflows.managers.history_mg import HistoryLastResponse

from .factories import (
    ExecutionResultFactory,
    HistoryResultFactory,
    create_history_request,
)


@pytest.mark.asyncio
async def test_history_bp_create(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    mocker.patch("nb_workflows.web.history_bp.history_mg.create", return_value=5)
    hreq = create_history_request()
    exec_res = ExecutionResultFactory()
    req, res = await sanic_app.asgi_client.post(
        "/history",
        json=exec_res.dict(),
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res.status_code == 201


@pytest.mark.asyncio
async def test_history_bp_last(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    h = HistoryResultFactory()
    rows = HistoryLastResponse(rows=[h])
    mocker.patch("nb_workflows.web.history_bp.history_mg.get_last", return_value=rows)
    req, res = await sanic_app.asgi_client.get(
        "/history/test/test?lt=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # req2, res2 = await sanic_app.asgi_client.get(
    #     "/history/test-nonexistent/test?lt=1",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_history_bp_last_404(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    req, res = await sanic_app.asgi_client.get(
        "/history/not-exist-test/non?lt=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 404
