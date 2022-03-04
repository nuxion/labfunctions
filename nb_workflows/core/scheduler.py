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
from nb_workflows.core.entities import NBTask, ScheduleData
from nb_workflows.core.executors import docker_exec
from nb_workflows.core.managers import projects, workflows
from nb_workflows.core.models import WorkflowModel
from nb_workflows.core.notebooks import nb_job_executor
from nb_workflows.db.sync import SQL
from nb_workflows.hashes import Hash96
from nb_workflows.utils import run_async

_DEFAULT_SCH_TASK_TO = 60 * 5  # 5 minutes


def scheduler_dispatcher(projectid, jobid):
    """Because rq-scheduler has some limitations
    and could be abandoned in the future, this abstraction was created
    where the idea is to use the scheduler only to enqueue through rq.

    Also, adopting this strategy, allows to react dinamically to changes
    in the workflow task because if params are modified
    """
    db = SQL(settings.SQL)
    _cfg = settings.rq2dict()
    redis = Redis(**_cfg)
    scheduler = SchedulerExecutor(redis=redis, qname="control")

    Session = db.sessionmaker()

    with Session() as session:
        obj_model = workflows.get_by_jobid_model_sync(session, jobid)
        if obj_model and obj_model.enabled:
            task = NBTask(**obj_model.job_detail)
            _job = scheduler.enqueue_notebook_in_docker(
                projectid,
                task,
            )
        else:
            if not obj_model:
                scheduler.cancel_job(jobid)
                print(f"job: {jobid} not found, deleted")
                # raise IndexError(f"job: {jobid} not found")

            print(f"Job: {jobid} disabled")


class SchedulerExecutor:
    def __init__(self, redis: Redis, qname=settings.RQ_CONTROL_QUEUE):
        self.redis = redis
        self.Q = Queue(qname, connection=self.redis)
        self.qname = qname
        # on_success=rq_job_ok, on_failure=rq_job_error)
        self.scheduler = Scheduler(queue=self.Q, connection=self.redis)

    def enqueue_notebook_in_docker(
        self, projectid, task: NBTask, executionid=None
    ) -> Job:
        """Enqueue in redis a notebook workflow
        :param task: NBTask object
        :param executionid: An optional executionid
        """
        _id = executionid or workflows.generate_execid()
        Q = Queue(task.machine, connection=self.redis)
        job = Q.enqueue(
            docker_exec,
            projectid,
            task.jobid,
            job_id=_id,
            job_timeout=task.timeout,
        )
        return job

    async def schedule(self, session, project_id, data_dict, update=False) -> str:
        schedule_data = data_dict["schedule"]
        task = NBTask(**data_dict)
        task.schedule = ScheduleData(**schedule_data)

        jobid = await workflows.register(session, project_id, task, update=update)

        try:
            await session.commit()
        except IntegrityError:
            raise KeyError("An integrity error when saving the workflow into db")

        if task.schedule.cron:
            await run_async(self._cron2redis, project_id, jobid, task)
        else:
            await run_async(self._interval2redis, project_id, jobid, task)

        return jobid

    def _interval2redis(self, projectid: str, jobid: str, task: NBTask):
        interval = task.schedule
        start_in_dt = datetime.utcnow() + timedelta(minutes=interval.start_in_min)

        self.scheduler.schedule(
            id=jobid,
            scheduled_time=start_in_dt,
            func=scheduler_dispatcher,
            args=[projectid, jobid],
            interval=interval.interval,
            repeat=interval.repeat,
            queue_name=self.qname,
            timeout=_DEFAULT_SCH_TASK_TO,
        )

    def _cron2redis(self, projectid: str, jobid: str, task: NBTask):
        cron = task.schedule
        self.scheduler.cron(
            cron.cron,
            id=jobid,
            func=scheduler_dispatcher,
            args=[projectid, jobid],
            repeat=cron.repeat,
            queue_name=self.qname,
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

    async def delete_workflow(self, session, projectid, jobid: str):
        """Delete job from redis and db"""

        await run_async(self.cancel_job, jobid)
        await workflows.delete_wf(session, projectid, jobid)
