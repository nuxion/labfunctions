from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from labfunctions import context as ctx
from labfunctions import defaults, errors
from labfunctions.errors.generics import WorkflowRegisterError
from labfunctions.hashes import generate_random
from labfunctions.managers import projects_mg, runtimes_mg
from labfunctions.models import WorkflowModel
from labfunctions.types import (
    ExecutionNBTask,
    NBTask,
    ProjectData,
    ScheduleData,
    WorkflowData,
    WorkflowDataWeb,
    WorkflowsList,
)
from labfunctions.utils import get_version

WFDATA_RULES = ("-id", "-project", "-project_id", "-created_at", "-updated_at")


def model2data(wm: WorkflowModel) -> WorkflowDataWeb:
    return WorkflowDataWeb(
        alias=wm.alias,
        nbtask=NBTask(**wm.nbtask),
        enabled=wm.enabled,
        wfid=wm.wfid,
        schedule=ScheduleData(**wm.schedule),
    )


def _update(wfid: str, projectid: str, wfd: WorkflowDataWeb):

    task_dict = wfd.nbtask.dict()
    schedule = None
    if wfd.schedule:
        schedule = wfd.schedule.dict()

    wm_table = WorkflowModel.__table__
    stmt = (
        update(wm_table)
        .where(wm_table.c.wfid == wfid)
        .values(
            nbtask=task_dict,
            schedule=schedule,
            alias=wfd.alias,
            enabled=wfd.enabled,
            updated_at=datetime.utcnow(),
        )
    )
    return stmt


def select_workflow():
    stmt = select(WorkflowModel).options(selectinload(WorkflowModel.project))
    return stmt


def generate_wfid(size=defaults.WFID_LEN) -> str:
    """wfid refers to the workflow id, this is only defined once, when the
    workflow is created, and should to be unique."""
    return generate_random(size)


def get_job_from_db(session, wfid) -> Union[WorkflowModel, None]:
    stmt = select(WorkflowModel).where(WorkflowModel.wfid == wfid)
    result = session.execute(stmt)
    row = result.scalar()

    if row:
        return row
    return None


async def get_by_wfid(session, wfid) -> WorkflowData:
    stmt = select_workflow().where(WorkflowModel.wfid == wfid)
    result = await session.execute(stmt)
    row = result.scalar()
    if row:
        return WorkflowData(**row.to_dict(rules=WFDATA_RULES))
    return None


async def get_by_wfid_prj(session, projectid, wfid) -> WorkflowDataWeb:
    stmt = (
        select_workflow()
        .where(WorkflowModel.wfid == wfid)
        .where(WorkflowModel.project_id == projectid)
    )
    result = await session.execute(stmt)
    row = result.scalar()
    if row:
        return model2data(row)
    return None


def get_by_prj_and_wfid_sync(session, projectid, wfid) -> Union[WorkflowModel, None]:
    stmt = (
        select_workflow()
        .where(WorkflowModel.project_id == projectid)
        .where(WorkflowModel.wfid == wfid)
    )
    result = session.execute(stmt)
    row = result.scalar()
    if row:
        return row
    return None


async def get_all(session, project_id=None) -> List[WorkflowData]:
    stmt = select_workflow()
    if project_id:
        stmt = stmt.where(WorkflowModel.project_id == project_id)

    result = await session.execute(stmt)
    rows = result.scalars()

    wfs = []
    for r in rows:
        dict_ = r.to_dict(rules=WFDATA_RULES)
        wfs.append(WorkflowData(**dict_))

    return wfs


async def get_by_alias(session, alias) -> Union[WorkflowModel, None]:
    stmt = select_workflow().where(WorkflowModel.alias == alias).limit(1)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    return row


async def register(session, projectid: str, wfd: WorkflowDataWeb, update=False) -> str:
    """Register workflows"""
    wfid = generate_wfid()

    if update:
        stmt = _update(wfd.wfid, projectid, wfd)
        await session.execute(stmt)
        return wfd.wfid

    data_dict = wfd.dict()
    data_dict["wfid"] = wfid
    schedule = None
    if wfd.schedule:
        schedule = wfd.schedule.dict()

    obj = WorkflowModel(
        wfid=wfid,
        alias=wfd.alias,
        nbtask=wfd.nbtask.dict(),
        schedule=schedule,
        project_id=projectid,
        enabled=wfd.enabled,
    )
    session.add(obj)
    try:
        await session.flush()
    except IntegrityError as e:
        await session.rollback()
        raise WorkflowRegisterError(projectid, wfd.alias, e)
    return wfid


async def delete_wf(session, project_id, wfid):
    stmt = (
        delete(WorkflowModel)
        .where(WorkflowModel.project_id == project_id)
        .where(WorkflowModel.wfid == wfid)
    )
    await session.execute(stmt)


async def prepare_notebook_job_async(
    session, projectid: str, wfid: str, execid: str
) -> ExecutionNBTask:
    """It prepares the task execution of the notebook"""
    wm = await get_by_wfid_prj(session, projectid, wfid)
    if wm and wm.enabled:
        pm = await projects_mg.get_by_projectid_model(session, projectid)
        task = NBTask(**wm.task)

        pd = ProjectData.from_orm(pm)
        pd.username = pm.user.username

        exec_notebook_ctx = ctx.create_notebook_ctx(pd, task, execid)
        return exec_notebook_ctx
    elif not wm.enabled:
        raise errors.WorkflowDisabled(projectid, wfid)

    raise errors.WorkflowNotFound(projectid, wfid)
