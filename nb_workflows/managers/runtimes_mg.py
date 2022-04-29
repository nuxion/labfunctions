from typing import List, Union

from sqlalchemy import delete as sqldelete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows.models import RuntimeModel
from nb_workflows.types.runtimes import RuntimeData, RuntimeReq, RuntimeSpec


def select_runtime():
    stmt = select(RuntimeModel).options(selectinload(RuntimeModel.project))
    return stmt


def model2runtime(m: RuntimeModel) -> RuntimeData:
    rd = RuntimeData(
        id=m.id,
        runtimeid=m.runtimeid,
        runtime_name=m.runtime_name,
        docker_name=m.docker_name,
        spec=RuntimeSpec(**m.spec),
        project_id=m.project.projectid,
        created_at=m.created_at.isoformat(),
        version=m.version,
    )
    return rd


def _insert(rd: RuntimeData):
    t = RuntimeModel.__table__
    stmt = sqlinsert(t).values(rd.dict(exclude_none=True))
    return stmt


async def get_list(session, projectid, limit=10) -> List[RuntimeData]:
    stmt = (
        select_runtime()
        .where(RuntimeModel.project_id == projectid)
        .order_by(RuntimeModel.created_at.desc())
        .limit(limit)
    )
    rows = await session.execute(stmt)

    return [model2runtime(r[0]) for r in rows]


async def create(session, rq: RuntimeReq) -> bool:
    rd = RuntimeData(
        runtimeid=f"{rq.project_id}/{rq.runtime_name}/{rq.version}", **rq.dict()
    )
    stmt = _insert(rd)
    inserted = True
    try:
        await session.execute(stmt)
    except IntegrityError as e:
        inserted = False
    return inserted


async def get_by_rid(session, runtimeid: str) -> Union[RuntimeData, None]:
    stmt = select_runtime().where(RuntimeModel.runtimeid == runtimeid).limit(1)

    rsp = await session.execute(stmt)
    model = rsp.scalar_one_or_none()
    if model:
        rd = model2runtime(model)
        return rd
    return None


async def delete_by_rid(session, runtimeid: int):
    stmt = sqldelete(RuntimeModel).where(RuntimeModel.runtimeid == runtimeid)
    await session.execute(stmt)
