import pytest

from nb_workflows.managers import machine_mg
from nb_workflows.models import MachineModel
from nb_workflows.types.machine import (
    ExecutionMachine,
    MachineInstance,
    MachineOrm,
    SSHKey,
)

from .factories import MachineOrmFactory


@pytest.mark.asyncio
async def test_machine_create(async_session):
    mo = MachineOrmFactory()
    one = await machine_mg.create(async_session, mo)
    repeat = await machine_mg.create(async_session, mo)
    assert one
    assert repeat is False


@pytest.mark.asyncio
async def test_machine_create_or_update(async_session):
    mo = MachineOrmFactory()
    await machine_mg.create(async_session, mo)
    mo.desc = "changed"
    rsp = await machine_mg.create_or_update(async_session, mo)
    assert isinstance(rsp, MachineModel)
    assert rsp.desc == mo.desc


@pytest.mark.asyncio
async def test_machine_get_list(async_session):
    mo = MachineOrmFactory()
    await machine_mg.create(async_session, mo)
    rows = await machine_mg.get_list(async_session)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_machine_get_one(async_session):
    mo = MachineOrmFactory()
    await machine_mg.create(async_session, mo)
    obj = await machine_mg.get_one(async_session, mo.name)
    assert obj.name == mo.name
    assert isinstance(obj, MachineModel)


def test_machine_create_or_update_sync(session):
    mo = MachineOrmFactory()
    mo.desc = "changed"
    rsp = machine_mg.create_or_update_sync(session, mo)
    assert isinstance(rsp, MachineModel)
    assert rsp.desc == mo.desc


def test_machine_insert():
    mo = MachineOrmFactory()
    stmt = machine_mg._insert(mo)
    assert "machine" in str(stmt)
