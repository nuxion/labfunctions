import pytest
from pytest_mock import MockerFixture

from labfunctions.defaults import API_VERSION
from labfunctions.managers import history_mg
from labfunctions.managers.history_mg import HistoryLastResponse
from labfunctions.models import HistoryModel
from labfunctions.types import HistoryLastResponse

from .factories import (
    ExecutionResultFactory,
    HistoryResultFactory,
    create_history_request,
)

version = API_VERSION


@pytest.mark.asyncio
async def test_history_bp_create(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    mocker.patch("labfunctions.web.history_bp.history_mg.create", return_value=5)
    hreq = create_history_request()
    exec_res = ExecutionResultFactory()
    req, res = await sanic_app.asgi_client.post(
        f"{version}/history",
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
    mocker.patch("labfunctions.web.history_bp.history_mg.get_last", return_value=rows)
    req, res = await sanic_app.asgi_client.get(
        f"{version}/history/test/test?lt=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # req2, res2 = await sanic_app.asgi_client.get(
    #     "/history/test-nonexistent/test?lt=1",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_history_bp_get_all(
    async_session, sanic_app, async_redis_web, access_token, mocker: MockerFixture
):

    h = HistoryResultFactory()
    rows = HistoryLastResponse(rows=[h])
    mocker.patch("labfunctions.web.history_bp.history_mg.get_last", return_value=rows)
    req, res = await sanic_app.asgi_client.get(
        f"{version}/history/test?lt=1",
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
        f"{version}/history/not-exist-test/non?lt=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 404


def test_history_mg_select():
    stmt = history_mg.select_history()
    assert "nb_history" in str(stmt)


@pytest.mark.asyncio
async def test_history_mg_last(async_session):
    res_wf = await history_mg.get_last(async_session, "test", "wfid-test", limit=1)
    res = await history_mg.get_last(async_session, "test", limit=1)

    res_none = await history_mg.get_last(async_session, "non existent", limit=1)

    assert isinstance(res_wf, HistoryLastResponse)
    assert len(res_wf.rows) == 1
    assert len(res.rows) == 1
    assert len(res_none.rows) == 0


@pytest.mark.asyncio
async def test_history_mg_create(async_session):
    exec_error = ExecutionResultFactory(error=True)
    exec_ok = ExecutionResultFactory(error=False)

    model_err = await history_mg.create(async_session, exec_error)
    model_ok = await history_mg.create(async_session, exec_ok)

    assert isinstance(model_ok, HistoryModel)
    assert model_err.status == -1
    assert model_ok.status == 0
