from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Union

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from nb_workflows.core.entities import NBTask, WorkflowData, WorkflowsList
from nb_workflows.core.managers import projects
from nb_workflows.core.models import WorkflowModel
from nb_workflows.hashes import Hash96

WFDATA_RULES = ("-id", "-project", "-project_id", "-created_at", "-updated_at")


def _create_or_update_workflow(jobid: str, projectid: str, task: NBTask):
    task_dict = asdict(task)

    stmt = insert(WorkflowModel.__table__).values(
        jobid=jobid,
        nb_name=task.nb_name,
        alias=task.alias,
        job_detail=task_dict,
        project_id=projectid,
        enabled=task.schedule.enabled,
    )
    stmt = stmt.on_conflict_do_update(
        # constraint="crawlers_page_bucket_id_fkey",
        index_elements=["jobid"],
        set_=dict(
            job_detail=task_dict,
            alias=task.alias,
            enabled=task.schedule.enabled,
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


def generate_execid():
    """executionid refers to unique id randomly generated for each execution
    of a workflow. It can be thought of as the id of an instance.
    of the NB Workflow definition.
    """
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


def get_by_jobid_model_sync(session, jobid) -> Union[WorkflowModel, None]:
    stmt = select_workflow().where(WorkflowModel.jobid == jobid)
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

    pm = await projects.get_by_projectid_model(session, projectid)
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
