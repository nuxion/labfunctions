from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Union

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows import errors
from nb_workflows.executors import context as ctx
from nb_workflows.hashes import Hash96
from nb_workflows.managers import projects_mg
from nb_workflows.models import WorkflowModel
from nb_workflows.types import (
    ExecutionNBTask,
    NBTask,
    ProjectData,
    ScheduleData,
    WorkflowData,
    WorkflowsList,
)

WFDATA_RULES = ("-id", "-project", "-project_id", "-created_at", "-updated_at")


def _create_or_update_workflow(jobid: str, projectid: str, task: NBTask):
    task_dict = asdict(task)

    stmt = insert(WorkflowModel.__table__).values(
        jobid=jobid,
        nb_name=task.nb_name,
        alias=task.alias,
        job_detail=task_dict,
        project_id=projectid,
        enabled=task.enabled,
    )
    stmt = stmt.on_conflict_do_update(
        # constraint="crawlers_page_bucket_id_fkey",
        index_elements=["jobid"],
        set_=dict(
            job_detail=task_dict,
            alias=task.alias,
            enabled=task.enabled,
            updated_at=datetime.utcnow(),
        ),
    )

    return stmt


def select_workflow():
    stmt = select(WorkflowModel).options(selectinload(WorkflowModel.project))
    return stmt


def generate_jobid():
    """jobid refers to the workflow id, this is only defined once, when the
    workflow is created, and should to be unique."""
    return Hash96.time_random_string().id_hex


def get_job_from_db(session, jobid) -> Union[WorkflowModel, None]:
    stmt = select(WorkflowModel).where(WorkflowModel.jobid == jobid)
    result = session.execute(stmt)
    row = result.scalar()

    if row:
        return row
    return None


async def get_by_jobid(session, jobid) -> WorkflowData:
    stmt = select_workflow().where(WorkflowModel.jobid == jobid)
    result = await session.execute(stmt)
    row = result.scalar()
    if row:
        return WorkflowData(**row.to_dict(rules=WFDATA_RULES))
    return None


async def get_by_jobid_prj(session, projectid, jobid) -> WorkflowData:
    stmt = (
        select_workflow()
        .where(WorkflowModel.jobid == jobid)
        .where(WorkflowModel.project_id == projectid)
    )
    result = await session.execute(stmt)
    row = result.scalar()
    if row:
        return WorkflowData(**row.to_dict(rules=WFDATA_RULES))
    return None


def get_by_prj_and_jobid_sync(session, projectid, jobid) -> Union[WorkflowModel, None]:
    stmt = (
        select_workflow()
        .where(WorkflowModel.project_id == projectid)
        .where(WorkflowModel.jobid == jobid)
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


async def get_by_alias(session, alias) -> Union[Dict[str, Any], None]:
    if alias:
        stmt = select_workflow().where(WorkflowModel.alias == alias).limit(1)
        result = await session.execute(stmt)
        row = result.scalar()
        return row
    return None


async def register(session, projectid: str, task: NBTask, update=False) -> str:
    """Register workflows"""
    jobid = generate_jobid()
    data_dict = asdict(task)

    pm = await projects_mg.get_by_projectid_model(session, projectid)
    if not pm:
        raise AttributeError("Projectid not found %s", projectid)

    if update:
        wf = await get_by_jobid(session, task.jobid)
        if wf:
            jobid = wf.jobid

        stmt = _create_or_update_workflow(jobid, projectid, task)
        await session.execute(stmt)
    else:
        data_dict["jobid"] = jobid
        obj = WorkflowModel(
            jobid=jobid,
            nb_name=task.nb_name,
            alias=task.alias,
            job_detail=data_dict,
            project_id=projectid,
        )
        session.add(obj)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise KeyError("Integrity error")
    return jobid


async def delete_wf(session, project_id, jobid):
    stmt = (
        delete(WorkflowModel)
        .where(WorkflowModel.project_id == project_id)
        .where(WorkflowModel.jobid == jobid)
    )
    await session.execute(stmt)


def prepare_notebook_job(
    session, projectid: str, jobid: str, execid: str
) -> ExecutionNBTask:
    """It prepares the task execution of the notebook"""
    wm = get_by_prj_and_jobid_sync(session, projectid, jobid)
    if wm and wm.enabled:
        pm = projects_mg.get_by_projectid_model_sync(session, projectid)
        task = NBTask(**wm.job_detail)
        if task.schedule:
            task.schedule = ScheduleData(**wm.job_detail["schedule"])

        pd = ProjectData.from_orm(pm)
        pd.username = pm.user.username

        exec_notebook_ctx = ctx.create_notebook_ctx(pd, task, execid)
        return exec_notebook_ctx
    elif not wm.enabled:
        raise errors.WorkflowDisabled(projectid, jobid)

    raise errors.WorkflowNotFound(projectid, jobid)
