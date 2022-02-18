import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from nb_workflows.conf import Config
from nb_workflows.db.sync import SQL
from nb_workflows.hashes import Hash96
from nb_workflows.workflows.core import NBTask, nb_job_executor
from nb_workflows.workflows.models import ScheduleModel
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry, StartedJobRegistry
from rq_scheduler import Scheduler
from sqlalchemy import delete, select


@dataclass
class ScheduleInterval:
    task: NBTask
    interval: int  # seconds
    qname: str = "default"
    alias: Optional[str] = None
    start_in_min: int = 0
    repeat: Optional[int] = None
    enabled: bool = True


@dataclass
class ScheduleCron:
    task: NBTask
    cron: str
    qname: str = "default"
    alias: Optional[str] = None
    start_in_min: int = 0
    repeat: Optional[int] = None
    enabled: bool = True


@dataclass
class ScheduleData:
    """Used as generic structure when querying database"""

    task: NBTask
    qname: str = "default"
    alias: Optional[str] = None
    start_in_min: int = 0
    repeat: Optional[int] = None
    cron: Optional[str] = None
    interval: Optional[str] = None
    enabled: bool = True


def get_job(session, jobid) -> Union[ScheduleModel, None]:
    stmt = select(ScheduleModel).where(ScheduleModel.jobid == jobid)
    result = session.execute(stmt)
    row = result.scalar()

    if row:
        return row
    return None


def _parse_job_detail(data_dict) -> ScheduleData:
    _task = NBTask(**data_dict["job_detail"]["task"])
    s_data = ScheduleData(**data_dict["job_detail"])
    s_data.task = _task
    return s_data


def get_and_parse_job(session, jobid) -> Union[ScheduleData, None]:
    stmt = select(ScheduleModel).where(ScheduleModel.jobid == jobid)
    result = session.execute(stmt)
    row = result.scalar()

    if row:
        s_data = _parse_job_detail(row.to_dict())
        return s_data
    return None


def scheduler_wrapper(jobid):
    """Because rq-scheduler has some limitations
    and could be abandoned in the future, this abstraction was created
    where the idea is to use the scheduler only to enqueue through rq.

    Also, this way of schedule allows dinamically changes to the workflow
    task because the params are got from the database.
    """
    db = SQL(Config.SQL)
    _cfg = Config.rq2dict()
    scheduler = SchedulerExecutor(_cfg)
    Q = QueueExecutor(_cfg)

    Session = db.sessionmaker()

    with Session() as session:
        obj_model = get_job(session, jobid)
        if obj_model and obj_model.enabled:
            id_ = scheduler.executionid()
            schedule_data = _parse_job_detail(obj_model.to_dict())
            # setting jobid for the workflow_history table
            schedule_data.task.jobid = jobid
            _job = Q.enqueue(
                nb_job_executor,
                schedule_data.task,
                job_id=id_,
                job_timeout=schedule_data.task.timeout,
            )
        else:
            if not obj_model:
                raise IndexError(f"job: {jobid} not found")
            else:
                print(f"Job: {jobid} disabled")


class QueueExecutor:
    def __init__(self, redis, qname="default"):
        self.redis = Redis(**redis)
        self.Q = Queue(qname, connection=self.redis)
        self.registries = {
            "failed": FailedJobRegistry(name=qname, connection=self.redis),
            "started": StartedJobRegistry(name=qname, connection=self.redis),
        }
        # self.failed =
        # self.started = StartedJobRegistry(name=qname, connection=self.redis)

    def enqueue(self, f, *args, **kwargs) -> Job:
        job = self.Q.enqueue(
            f,
            # on_success=rq_job_ok,
            # on_failure=rq_job_error,
            *args,
            **kwargs,
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
    def __init__(self, redis, qname="default"):
        self.redis = Redis(**redis)
        self.Q = Queue(qname, connection=self.redis)
        # on_success=rq_job_ok, on_failure=rq_job_error)
        self.scheduler = Scheduler(queue=self.Q, connection=self.redis)

    @staticmethod
    def jobid():
        """ jobid refers to the workflow id, this is only defined once, when the
        workflow is created, and should to be unique. """
        return Hash96.time_random_string().id_hex

    @staticmethod
    def executionid():
        """ executionid refers to unique id randomly generated for each execution
        of a workflow. It can be thought of as the id of an instance.
        of the NB Workflow definition.
        """
        return Hash96.time_random_string().id_hex

    def _cron2redis(self, jobid: str, cron: ScheduleCron):
        self.scheduler.cron(
            cron.cron,
            id=jobid,
            func=nb_job_executor,
            args=[cron.task],
            repeat=cron.repeat,
            queue_name=cron.qname,
            # on_success=rq_job_ok,
            # on_failure=rq_job_error,
        )

    def _interval2redis(self, jobid: str, interval: ScheduleInterval):
        start_in_dt = datetime.utcnow() + timedelta(minutes=interval.start_in_min)

        self.scheduler.schedule(
            id=jobid,
            scheduled_time=start_in_dt,
            func=scheduler_wrapper,
            args=[jobid],
            interval=interval.interval,
            repeat=interval.repeat,
            queue_name=interval.qname,
            timeout=60 * 5,  # 5 minutes
        )

    async def get_jobid_db(self, session, jobid):
        stmt = select(ScheduleModel).where(ScheduleModel.jobid == jobid)
        result = await session.execute(stmt)
        row = result.scalar()
        if row:
            return row.to_dict()
        return None

    async def get_by_alias(self, session, alias) -> Union[Dict[str, Any], None]:
        if alias:
            stmt = (
                select(ScheduleModel).where(
                    ScheduleModel.alias == alias).limit(1)
            )
            result = await session.execute(stmt)
            row = result.scalar()
            return row
        return None

    async def get_schedule_db(self, session):
        stmt = select(ScheduleModel)
        result = await session.execute(stmt)
        rows = result.scalars()
        return [r.to_dict() for r in rows]

    @staticmethod
    async def run_async(func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        rsp = await loop.run_in_executor(None, func, *args, **kwargs)
        return rsp

    @staticmethod
    def _parse_interval_dict(data_dict) -> ScheduleInterval:
        _task = NBTask(**data_dict["task"])
        interval = ScheduleInterval(**data_dict)
        interval.task = _task
        return interval

    @staticmethod
    def _parse_cron_dict(data_dict) -> ScheduleCron:
        _task = NBTask(**data_dict["task"])
        cron = ScheduleCron(**data_dict)
        cron.task = _task
        return cron

    async def schedule(self, session, data_dict, jobid=None) -> str:
        if data_dict.get("interval"):
            j = await self.schedule_interval(session, data_dict, jobid)
        else:
            j = await self.schedule_cron(session, data_dict, jobid)

        return j

    async def schedule_cron(self, session, data_dict, jobid=None) -> str:
        """Entrypoint to register the task in the scheduler and
        register it in the database."""

        jobid = jobid or self.jobid()

        obj = self._parse_cron_dict(data_dict)

        sch = ScheduleModel(
            jobid=jobid,
            nb_name=obj.task.name,
            alias=obj.alias,
            job_detail=data_dict,
            enabled=obj.enabled,
        )
        session.add(sch)
        await self.run_async(self._cron2redis, jobid, obj)
        return jobid

    async def schedule_interval(self, session, data_dict, jobid=None) -> str:
        """Entrypoint to register the task in the scheduler and
        register it in the database."""
        jobid = jobid or self.jobid()
        obj = self._parse_interval_dict(data_dict)

        sch = ScheduleModel(
            jobid=jobid,
            nb_name=obj.task.nb_name,
            job_detail=data_dict,  # schedule_detail
            alias=obj.alias,
            enabled=obj.enabled,
        )
        session.add(sch)
        await self.run_async(self._interval2redis, jobid, obj)
        return jobid

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

    def cancel(self, jobid):
        """Cancel job from redis"""
        self.scheduler.cancel(jobid)

    async def delete_job(self, session, jobid: str):
        """Delete job from redis and db"""

        await self.run_async(self.cancel, jobid)
        table = ScheduleModel.__table__
        stmt = delete(table).where(table.c.jobid == jobid)
        await session.execute(stmt)
