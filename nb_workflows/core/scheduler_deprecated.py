import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry, StartedJobRegistry
from rq_scheduler import Scheduler
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

# from nb_workflows.workflows.registers import register_history_db
from nb_workflows.conf import settings
from nb_workflows.core.core import nb_job_executor
from nb_workflows.core.entities import NBTask, ScheduleData
from nb_workflows.core.managers import projects
from nb_workflows.core.models import WorkflowModel
from nb_workflows.db.sync import SQL
from nb_workflows.hashes import Hash96

_DEFAULT_SCH_TASK_TO = 60 * 5  # 5 minutes


def _create_or_update_workflow(jobid: str, projectid: str, task: NBTask, update=False):
    task_dict = asdict(task)

    stmt = insert(WorkflowModel.__table__).values(
        jobid=jobid,
        nb_name=task.nb_name,
        alias=task.alias,
        job_detail=task_dict,
        project_id=projectid,
        enabled=task.schedule.enabled,
    )
    if not update:
        stmt = stmt.on_conflict_do_nothing()
    else:
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


def get_job_from_db(session, jobid) -> Union[WorkflowModel, None]:
    stmt = select(WorkflowModel).where(WorkflowModel.jobid == jobid)
    result = session.execute(stmt)
    row = result.scalar()

    if row:
        return row
    return None


def scheduler_dispatcher(jobid):
    """Because rq-scheduler has some limitations
    and could be abandoned in the future, this abstraction was created
    where the idea is to use the scheduler only to enqueue through rq.

    Also, this way of schedule allows dinamically changes to the workflow
    task because the params are got from the database.
    """
    db = SQL(settings.SQL)
    _cfg = settings.rq2dict()
    redis = Redis(**_cfg)
    scheduler = SchedulerExecutor(redis=redis)
    Q = QueueExecutor(redis=redis)

    Session = db.sessionmaker()

    with Session() as session:
        obj_model = get_job_from_db(session, jobid)
        if obj_model and obj_model.enabled:
            id_ = scheduler.executionid()
            task = NBTask(**obj_model.job_detail)
            task.jobid = jobid
            task.schedule = ScheduleData(**task.schedule)
            _job = Q.enqueue(
                nb_job_executor,
                task,
                job_id=id_,
                job_timeout=task.timeout,
            )
        else:
            if not obj_model:
                scheduler.cancel_job(jobid)
                print(f"job: {jobid} not found, deleted")
                # raise IndexError(f"job: {jobid} not found")

            print(f"Job: {jobid} disabled")


class QueueExecutor:
    """A thin wrapper over the Queue object of rq"""

    def __init__(self, redis: Redis, qname="default", is_async=True):
        self.redis = redis
        self.Q = Queue(qname, is_async=is_async, connection=self.redis)
        self.registries = {
            "failed": FailedJobRegistry(name=qname, connection=self.redis),
            "started": StartedJobRegistry(name=qname, connection=self.redis),
        }
        # self.failed =
        # self.started = StartedJobRegistry(name=qname, connection=self.redis)

    def enqueue(self, f, *args, **kwargs) -> Job:
        """A wrapper over the Queue.enqueue() function of RQ lib"""
        job = self.Q.enqueue(
            f,
            # on_success=rq_job_ok,
            # on_failure=rq_job_error,
            *args,
            **kwargs,
        )
        return job

    def enqueue_notebook(self, task: NBTask, executionid=None) -> Job:
        """Enqueue in redis a notebook workflow
        :param task: NBTask object
        :param executionid: An optional executionid
        """
        _id = executionid or SchedulerExecutor.executionid()
        job = self.Q.enqueue(
            nb_job_executor,
            task,
            job_id=_id,
            job_timeout=task.timeout,
        )
        return job

    def fetch_job(self, jobid) -> Job:
        job = Job.fetch(jobid, connection=self.redis)
        return job

    def get_jobs_count(self, name: str) -> int:
        return self.registries[name].count

    def get_jobs_ids(self, name: str) -> List[str]:
        return self.registries[name].get_job_ids()

    def remove_jobs(self, name: str, delete_job=False) -> List[str]:
        """if delete_job is True, then also it will delete the job specification
        from redis"""
        r = self.registries[name]
        jobs = r.get_job_ids()
        # If you want to remove a job from a registry AND delete the job,
        # use `delete_job=True`
        for job_id in jobs:
            r.remove(job_id, delete_job=delete_job)
        return jobs


class SchedulerExecutor:
    def __init__(self, redis: Redis, qname="default"):
        self.redis = redis
        self.Q = Queue(qname, connection=self.redis)
        # on_success=rq_job_ok, on_failure=rq_job_error)
        self.scheduler = Scheduler(queue=self.Q, connection=self.redis)

    @staticmethod
    def jobid():
        """jobid refers to the workflow id, this is only defined once, when the
        workflow is created, and should to be unique."""
        return Hash96.time_random_string().id_hex

    @staticmethod
    def executionid():
        """executionid refers to unique id randomly generated for each execution
        of a workflow. It can be thought of as the id of an instance.
        of the NB Workflow definition.
        """
        return Hash96.time_random_string().id_hex

    async def get_jobid_db(self, session, jobid):
        stmt = select(WorkflowModel).where(WorkflowModel.jobid == jobid)
        result = await session.execute(stmt)
        row = result.scalar()
        if row:
            return row.to_dict()
        return None

    async def get_by_alias(self, session, alias) -> Union[Dict[str, Any], None]:
        if alias:
            stmt = select(WorkflowModel).where(WorkflowModel.alias == alias).limit(1)
            result = await session.execute(stmt)
            row = result.scalar()
            return row
        return None

    async def get_schedule_db(self, session, projectid):
        stmt = select(WorkflowModel).options(selectinload(WorkflowModel.project))
        stmt = stmt.where(WorkflowModel.project_id == projectid)
        result = await session.execute(stmt)
        rows = result.scalars()
        return [r.to_dict(rules=("-project",)) for r in rows]

    @staticmethod
    async def run_async(func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        rsp = await loop.run_in_executor(None, func, *args, **kwargs)
        return rsp

    async def register(self, session, projectid: str, task: NBTask, update=False):
        jobid = self.jobid()
        data_dict = asdict(task)

        pm = projects.get_by_projectid_model(session, projectid)
        if not pm:
            raise AttributeError("Projectid not found %s", projectid)

        if update:
            j = await self.get_jobid_db(session, task.jobid)
            if j:
                jobid = j["jobid"]

            stmt = _create_or_update_workflow(jobid, projectid, task, update=True)
            await session.execute(stmt)
            await self.run_async(self.cancel_job, jobid)
        else:
            sch = WorkflowModel(
                jobid=jobid,
                nb_name=task.nb_name,
                alias=task.alias,
                job_detail=data_dict,
                enabled=task.schedule.enabled,
                project_id=projectid,
            )
            session.add(sch)
        return jobid

    async def schedule(self, session, project_id, data_dict, update=False) -> str:
        schedule_data = data_dict["schedule"]
        task = NBTask(**data_dict)
        task.schedule = ScheduleData(**schedule_data)

        jobid = await self.register(session, project_id, task, update=update)

        try:
            await session.commit()
        except IntegrityError:
            raise KeyError("An integrity error when saving the workflow into db")

        if task.schedule.cron:
            await self.run_async(self._cron2redis, jobid, task)
        else:
            await self.run_async(self._interval2redis, jobid, task)

        return jobid

    def _interval2redis(self, jobid: str, task: NBTask):
        interval = task.schedule
        start_in_dt = datetime.utcnow() + timedelta(minutes=interval.start_in_min)

        self.scheduler.schedule(
            id=jobid,
            scheduled_time=start_in_dt,
            func=scheduler_dispatcher,
            args=[jobid],
            interval=interval.interval,
            repeat=interval.repeat,
            queue_name=task.qname,
            timeout=_DEFAULT_SCH_TASK_TO,
        )

    def _cron2redis(self, jobid: str, task: NBTask):
        cron = task.schedule
        self.scheduler.cron(
            cron.cron,
            id=jobid,
            func=scheduler_dispatcher,
            args=[jobid],
            repeat=cron.repeat,
            queue_name=task.qname,
        )

    def list_jobs(self):
        """List jobs from Redis"""
        jobs = []
        for x in self.scheduler.get_jobs():
            jobs.append(
                dict(
                    jobid=x.id,
                    func_name=x.func_name,
                    created_at=x.created_at.isoformat(),
                )
            )
        return jobs

    def cancel_all(self):
        """Cancel all from redis"""
        for j in self.scheduler.get_jobs():
            self.scheduler.cancel(j)

    def cancel_job(self, jobid):
        """Cancel job from redis"""
        self.scheduler.cancel(jobid)

    async def delete_workflow(self, session, jobid: str):
        """Delete job from redis and db"""

        await self.run_async(self.cancel_job, jobid)
        table = WorkflowModel.__table__
        stmt = delete(table).where(table.c.jobid == jobid)
        await session.execute(stmt)