import pytest

from nb_workflows.managers import runtimes_mg
from nb_workflows.types.docker import RuntimeVersionOrm

from .factories import RuntimeVersionFactory, create_runtime_model


@pytest.mark.asyncio
async def test_runtimes_mg_list(async_session):
    rows = await runtimes_mg.get_list(async_session, "test")
    empty = await runtimes_mg.get_list(async_session, "nontest")
    assert isinstance(rows, list)
    assert isinstance(rows[0], RuntimeVersionOrm)
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
