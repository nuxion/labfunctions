from typing import List

from sqlalchemy import delete as sqldelete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows.models import RuntimeVersionModel
from nb_workflows.types.docker import RuntimeVersionData, RuntimeVersionOrm


def select_runtime():
    stmt = select(RuntimeVersionModel).options(
        selectinload(RuntimeVersionModel.project)
    )
    return stmt


def _insert(rd: RuntimeVersionData):
    t = RuntimeVersionModel.__table__
    stmt = sqlinsert(t).values(
        docker_name=rd.docker_name, project_id=rd.projectid, version=rd.version
    )
    return stmt


async def get_list(session, projectid, limit=1) -> List[RuntimeVersionData]:
    stmt = (
        select_runtime()
        .where(RuntimeVersionModel.project_id == projectid)
        .order_by(RuntimeVersionModel.created_at.desc())
        .limit(limit)
    )
    rows = await session.execute(stmt)

    return [
        RuntimeVersionData(
            id=r[0].id,
            docker_name=r[0].docker_name,
            version=r[0].version,
            projectid=r[0].project.projectid,
        )
        for r in rows
    ]


async def create(session, rd: RuntimeVersionData) -> bool:
    stmt = _insert(rd)
    inserted = True
    try:
        await session.execute(stmt)
    except IntegrityError as e:
        inserted = False
    return inserted


async def delete_by_id(session, id: int):
    stmt = sqldelete(RuntimeVersionModel).where(RuntimeVersionModel.id == id)
    await session.execute(stmt)
