from typing import List

from sqlalchemy import delete as sqldelete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from labfunctions.models import MachineModel
from labfunctions.types.machine import MachineOrm, MachineType


def _insert(machine: MachineOrm):
    t = MachineModel.__table__
    stmt = sqlinsert(t).values(**machine.dict())
    return stmt


def _select_machine():
    stmt = select(MachineModel)
    return stmt


async def create(session, machine: MachineOrm) -> bool:
    stmt = _insert(machine)
    inserted = True
    try:
        r = await session.execute(stmt)
    except IntegrityError:
        inserted = False

    return inserted


async def create_or_update(session, machine: MachineOrm) -> MachineModel:
    m = MachineModel(**machine.dict())

    await session.merge(m)
    return m


def create_or_update_sync(session, machine: MachineOrm) -> MachineModel:
    m = MachineModel(**machine.dict())

    session.merge(m)
    return m


async def get_list(session, limit=1) -> List[MachineOrm]:
    stmt = _select_machine().order_by(MachineModel.created_at.desc()).limit(limit)
    rows = await session.execute(stmt)

    return [MachineOrm.from_orm(r[0]) for r in rows]


async def get_one(session, name: str) -> MachineModel:
    stmt = _select_machine().where(MachineModel.name == name).limit(1)
    rsp = await session.execute(stmt)
    return rsp.scalar_one_or_none()
