from typing import List, Union

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows.auth.models import GroupModel, UserModel
from nb_workflows.auth.users import get_user_async
from nb_workflows.db.nosync import AsyncSQL


def select_group():
    return select(GroupModel).options(selectinload(GroupModel.users))


def create_group_sync(session, name) -> GroupModel:
    gm = GroupModel(name=name)
    session.add(gm)
    return gm


async def create_group(session, name) -> int:
    stmt = (
        insert(GroupModel.__table__)
        .values(name=name)
        .returning(GroupModel.__table__.c.id)
        .on_conflict_do_nothing()
    )

    r = await session.execute(stmt)
    id_ = r.scalar()
    return id_


async def delete_group(session, id):
    stmt = delete(GroupModel).where(GroupModel.id == 1)
    await session.execute(stmt)


async def get_group_by_name_sync(session, name) -> Union[GroupModel, None]:
    stmt = select_group().where(GroupModel.name == name).limit(1)
    rsp = session.execute(stmt)
    return rsp.scalar_one_or_none()


async def get_group_by_name(session, name) -> Union[GroupModel, None]:
    stmt = select_group().where(GroupModel.name == name).limit(1)
    rsp = await session.execute(stmt)
    return rsp.scalar_one_or_none()


async def get_group_by_id(session, id) -> Union[GroupModel, None]:
    stmt = select_group().where(GroupModel.id == id).limit(1)
    rsp = await session.execute(stmt)
    return rsp.scalar_one_or_none()


async def list_groups(session) -> List[GroupModel]:
    stmt = select_group()
    result = await session.execute(stmt)
    rows = result.fetchall()
    return [r[0] for r in rows]


async def main(db: AsyncSQL):
    await db.init()
    s = db.sessionmaker()
    async with s.begin():
        gm = await create_group(s, "test3")
        rows = await list_groups(s)
        obj = await get_user_async(s, "nuxion")
        await get_group_by_id(s, 1)
        rows[0].users.append(obj)
        # await s.commit()


if __name__ == "__main__":
    import asyncio

    from nb_workflows.conf.server_settings import settings

    asql = AsyncSQL(settings.ASQL)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(asql))
