import pytest

from nb_workflows.conf.defaults import API_VERSION
from nb_workflows.managers import runtimes_mg
from nb_workflows.types.docker import RuntimeVersionData, RuntimeVersionOrm

from .factories import RuntimeVersionFactory, create_runtime_model

version = API_VERSION


@pytest.mark.asyncio
async def test_runtimes_mg_list(async_session):
    rows = await runtimes_mg.get_list(async_session, "test")
    empty = await runtimes_mg.get_list(async_session, "nontest")
    assert isinstance(rows, list)
    assert isinstance(rows[0], RuntimeVersionData)
    assert empty == []


@pytest.mark.asyncio
async def test_runtimes_mg_create(async_session):
    rd = RuntimeVersionFactory(docker_name="only_testing", projectid="test")
    res = await runtimes_mg.create(async_session, rd)
    repeated = await runtimes_mg.create(async_session, rd)
    assert res
    assert not repeated


@pytest.mark.asyncio
async def test_runtimes_mg_delete(async_session):
    rows = await runtimes_mg.get_list(async_session, "test")
    repeated = await runtimes_mg.delete_by_id(async_session, rows[0].id)
    new_rows = await runtimes_mg.get_list(async_session, "test")
    assert len(new_rows) == 0


@pytest.mark.asyncio
async def test_runtimes_bp_create(async_session, sanic_app, access_token, mocker):
    rd = RuntimeVersionFactory()
    mocker.patch("nb_workflows.web.runtimes_bp.runtimes_mg.create", return_value=True)
    _, res = await sanic_app.asgi_client.post(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
        json=rd.dict(),
    )
    mocker.patch("nb_workflows.web.runtimes_bp.runtimes_mg.create", return_value=False)
    _, res2 = await sanic_app.asgi_client.post(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
        json=rd.dict(),
    )

    assert res.status_code == 201
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_runtimes_bp_list(async_session, sanic_app, access_token, mocker):
    runtimes = RuntimeVersionFactory.create_batch(size=5)
    mocker.patch(
        "nb_workflows.web.runtimes_bp.runtimes_mg.get_list", return_value=runtimes
    )
    _, res = await sanic_app.asgi_client.get(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = res.json

    assert len(data) == len(runtimes)


@pytest.mark.asyncio
async def test_runtimes_bp_delete(async_session, sanic_app, access_token, mocker):
    mocker.patch(
        "nb_workflows.web.runtimes_bp.runtimes_mg.delete_by_id", return_value=None
    )
    _, res = await sanic_app.asgi_client.get(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 200
