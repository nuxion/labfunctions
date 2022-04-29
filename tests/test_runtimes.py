from pathlib import Path

import pytest

from nb_workflows.defaults import API_VERSION
from nb_workflows.managers import runtimes_mg
from nb_workflows.runtimes import generate_dockerfile
from nb_workflows.types.runtimes import RuntimeData, RuntimeReq

from .factories import (
    RuntimeDataFactory,
    RuntimeReqFactory,
    RuntimeSpecFactory,
    create_runtime_model,
)

version = API_VERSION


@pytest.mark.asyncio
async def test_runtimes_mg_list(async_session):
    rows = await runtimes_mg.get_list(async_session, "test")
    empty = await runtimes_mg.get_list(async_session, "nontest")
    assert isinstance(rows, list)
    assert isinstance(rows[0], RuntimeData)
    assert empty == []


@pytest.mark.asyncio
async def test_runtimes_mg_create(async_session, mocker):
    spec = RuntimeSpecFactory()
    rq = RuntimeReq(
        runtime_name=spec.name,
        docker_name=f"nbworkflows/{spec.name}:{spec.version}",
        spec=spec,
        project_id="test",
        version=spec.version,
    )
    spy = mocker.spy(runtimes_mg, "_insert")
    res = await runtimes_mg.create(async_session, rq)
    repeated = await runtimes_mg.create(async_session, rq)

    rd_calls = spy.call_args_list[0][0][0]
    assert res
    assert rd_calls.runtimeid == f"test/{spec.name}/{spec.version}"
    assert not repeated


@pytest.mark.asyncio
async def test_runtimes_mg_delete(async_session):
    rows = await runtimes_mg.get_list(async_session, "test")
    repeated = await runtimes_mg.delete_by_rid(async_session, rows[0].runtimeid)
    new_rows = await runtimes_mg.get_list(async_session, "test")
    assert len(new_rows) == 0


@pytest.mark.asyncio
async def test_runtimes_bp_create(async_session, sanic_app, access_token, mocker):
    rq = RuntimeReqFactory()
    mocker.patch("nb_workflows.web.runtimes_bp.runtimes_mg.create", return_value=True)
    _, res = await sanic_app.asgi_client.post(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
        json=rq.dict(),
    )
    mocker.patch("nb_workflows.web.runtimes_bp.runtimes_mg.create", return_value=False)
    _, res2 = await sanic_app.asgi_client.post(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
        json=rq.dict(),
    )

    assert res.status_code == 201
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_runtimes_bp_list(async_session, sanic_app, access_token, mocker):
    runtimes = RuntimeDataFactory.create_batch(size=5)
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
        "nb_workflows.web.runtimes_bp.runtimes_mg.delete_by_rid", return_value=None
    )
    _, res = await sanic_app.asgi_client.get(
        f"{version}/runtimes/test",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert res.status_code == 200


def test_runtimes_dockerfile(tempdir):
    spec = RuntimeSpecFactory()
    generate_dockerfile(Path(tempdir), spec)

    assert Path(f"{tempdir}/Dockerfile.{spec.name}").is_file()
