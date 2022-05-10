from typing import List, Optional, Union

from sqlalchemy import delete as sqldelete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from labfunctions.errors.runtimes import RuntimeNotFound
from labfunctions.models import RuntimeModel
from labfunctions.types.runtimes import RuntimeData, RuntimeReq, RuntimeSpec
from labfunctions.utils import get_version


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
        registry=m.registry,
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


async def get_runtime(
    session, projectid: str, runtime_name: str, version=None
) -> Union[RuntimeData, None]:
    stmt = select_runtime().where(RuntimeModel.project_id == projectid)
    if version:
        stmt = (
            stmt.where(RuntimeModel.runtime_name == runtime_name)
            .where(RuntimeModel.version == version)
            .limit(1)
        )
    else:
        stmt = (
            stmt.where(RuntimeModel.runtime_name == runtime_name)
            .order_by(RuntimeModel.created_at.desc())
            .limit(1)
        )

    rsp = await session.execute(stmt)
    model = rsp.scalar_one_or_none()
    if model:
        rd = model2runtime(model)
        return rd
    return None


def get_by_rid_sync(session, runtimeid: str) -> Union[RuntimeData, None]:
    stmt = select_runtime().where(RuntimeModel.runtimeid == runtimeid).limit(1)

    rsp = session.execute(stmt)
    model = rsp.scalar_one_or_none()
    if model:
        rd = model2runtime(model)
        return rd
    return None


async def delete_by_rid(session, runtimeid: int):
    stmt = sqldelete(RuntimeModel).where(RuntimeModel.runtimeid == runtimeid)
    await session.execute(stmt)


# def docker_name_from_runtime(session, runtimeid: Optional[str] = None) -> RuntimeData:
#     """ It returns the final docker name based on a runtime id,
#     if an id is not provided then it will returns the default runtime. """
#     if runtime:
#         _runtime = get_by_rid_sync(session, runtime)
#         if not _runtime:
#             raise RuntimeNotFound(runtime)
#         runtime = f"{_runtime.docker_name}:{_runtime.version}"
#         if _runtime.registry:
#             runtime = f"{_runtime.registry}/{runtime}"
#     else:
#         version = get_version()
#         runtime = f"nuxion/labfunctions:{version}"
#     return runtime
