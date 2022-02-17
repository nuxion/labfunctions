# pylint: disable=unused-argument
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi

from nb_workflows.conf import Config
from nb_workflows.utils import get_query_param, list_workflows, run_async
from nb_workflows.workflows.core import NBTask, nb_job_executor
from nb_workflows.workflows.scheduler import (
    QueueExecutor,
    ScheduleCron,
    ScheduleInterval,
    SchedulerExecutor,
    scheduler_wrapper,
)

workflows_bp = Blueprint("workflows", url_prefix="workflows")


def _get_scheduler() -> SchedulerExecutor:
    current_app = Sanic.get_app("nb_workflows")
    return current_app.ctx.scheduler


def _get_q_executor() -> QueueExecutor:
    current_app = Sanic.get_app("nb_workflows")
    return current_app.ctx.Q


@dataclass
class JobResponse:
    jobid: str
    workflow: NBTask


@dataclass
class JobDetail:
    jobid: str
    func_name: str
    # workflow: NBTask
    created_at: str


@workflows_bp.listener("before_server_start")
def startserver(current_app, loop):
    _cfg = Config.rq2dict()
    # current_app.ctx.redis = SchedulerExecutor(_cfg)
    current_app.ctx.scheduler = SchedulerExecutor(_cfg)
    current_app.ctx.Q = QueueExecutor(_cfg)
    # current_app.ctx.queue = queue_init(_cfg)


@workflows_bp.post("/notebooks/_run")
@openapi.body({"application/json": NBTask})
@openapi.response(202, JobResponse, "Task executed")
def launch_task(request):
    """
    Prepare and execute a Notebook Workflow Job based on a filename
    """
    current_app = Sanic.get_app("nb_workflows")
    nb_task = NBTask(**request.json)

    jobid = SchedulerExecutor.jobid()

    # job = Job.create(nb_job_executor, args=nb_task, id=jobid)
    # current_app.ctx.Q.enqueue_job(job)
    job = current_app.ctx.Q.enqueue(
        nb_job_executor, nb_task, job_id=jobid, job_timeout=nb_task.timeout
    )
    return json(dict(jobid=job.id), status=202)


@workflows_bp.get("/notebooks/_fetch/<jobid>")
@openapi.parameter("jobid", str, "path")
def get_job_result(request, jobid):
    """Get job result from the queue"""
    Q = _get_q_executor()
    job = Q.fetch_job(jobid)
    result = job.result
    if result:
        result = asdict(result)

    return json(
        dict(
            jobid=job.id,
            status=job.get_status(),
            result=result,
            position=job.get_position(),
        )
    )


@workflows_bp.get("/notebooks/failed")
def get_failed_jobs(request):
    """Get jobs failed"""
    Q = _get_q_executor()

    jobs = Q.get_jobs_ids("failed")

    return json(dict(rows=jobs, total=len(jobs)))


@workflows_bp.delete("/notebooks/failed")
@openapi.parameter("remove", bool, "query")
def delete_failed_jobs(request):
    """Remove failed jobs from the queue"""

    to_remove = get_query_param(request, "remove", False)
    Q = _get_q_executor()

    jobs = Q.remove_jobs("failed", to_remove)

    return json(dict(rows=jobs, total=len(jobs)))


@workflows_bp.get("/notebooks/running")
def get_running_jobs(request):
    """Get jobs failed"""
    Q = _get_q_executor()

    jobs = Q.get_jobs_ids("started")

    return json(dict(rows=jobs, total=len(jobs)))


@workflows_bp.get("/notebooks/_files")
# @openapi.response(201, WorkflowTask, "Task executed")
def list_nb_workflows(request):
    """
    List file workflows
    """
    # pylint: disable=unused-argument

    nb_files = list_workflows()

    return json(nb_files)


@workflows_bp.post("/schedule/interval")
@openapi.body({"application/json": ScheduleInterval})
# @openapi.response(201, WorkflowTask, "Task Scheduled")
async def schedule_interval(request):
    """
    Create and Schedule a workflow using interval syntax
    """
    # pylint: disable=not-a-mapping

    scheduler = _get_scheduler()
    session = request.ctx.session
    alias = request.json.get("alias")
    async with session.begin():
        w = await scheduler.get_by_alias(session, alias)
        if not w:
            jobid = await scheduler.schedule_interval(session, request.json)
            await session.commit()
            return json(dict(jobid=jobid), 201)

        return json(dict(jobid=w.jobid), 200)


@workflows_bp.post("/schedule/cron")
@openapi.body({"application/json": ScheduleCron})
# @openapi.response(201, WorkflowTask, "Task Scheduled")
async def schedule_cron(request):
    """
    Create and Schedule a workflow using CRON syntax
    """
    # pylint: disable=not-a-mapping
    current_app = Sanic.get_app("nb_workflows")
    jobid = SchedulerExecutor.jobid()
    session = request.ctx.session
    async with session.begin():
        await current_app.ctx.scheduler.scheduler_cron(
            jobid, session, request.json
        )
        await session.commit()

    return json(dict(jobid=jobid), 201)
    # return json(asdict(wt), 201)


@workflows_bp.get("/schedule")
# @openapi.response(200, List[JobDetail], "Task Scheduled")
async def list_schedue(request):
    """List jobs registered in the database"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    scheduler = _get_scheduler()

    async with session.begin():
        result = await scheduler.get_schedule_db(session)

    return json(result)


@workflows_bp.get("/schedule/_redis")
@openapi.response(200, List[JobDetail], "Task Scheduled")
def list_scheduled_redis(request):
    """
    List the jobs scheduled in the scheduler
    """
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()
    jobs = scheduler.list_jobs()

    return json(jobs, 200)


@workflows_bp.delete("/schedule/<jobid>")
# @openapi.body({"application/json": ScheduleCron})
@openapi.parameter("jobid", str, "path")
async def schedule_delete(request, jobid):
    """delete a job from scheduler"""
    # pylint: disable=unused-argument
    scheduler = _get_scheduler()
    session = request.ctx.session
    async with session.begin():
        await scheduler.delete_job(session, jobid)
        await session.commit()

    return json(dict(msg="done"), 200)


@workflows_bp.post("/schedule/<jobid>/_run")
@openapi.parameter("jobid", str, "path")
@openapi.response(202, JobResponse, "Relaunch accepted")
def schedule_run(request, jobid):
    """
    Manually execute a registered schedule task
    """
    current_app = Sanic.get_app("nb_workflows")

    job = current_app.ctx.Q.enqueue(scheduler_wrapper, jobid)

    return json(dict(jobid=job.id), status=202)


@workflows_bp.delete("/schedule/_cancel/<jobid>")
@openapi.parameter("jobid", str, "path")
async def schedule_cancel(request, jobid):
    """delete a job from scheduler"""
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()
    await run_async(scheduler.cancel, jobid)
    return json(dict(msg="done"), 200)


@workflows_bp.delete("/schedule/_cancel_all")
# @openapi.body({"application/json": ScheduleCron})
# @openapi.parameter("jobid", str, "path")
async def schedule_cancel_all(request):
    """Cancel all the jobs in the queue"""
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()

    await run_async(scheduler.cancel_all)

    return json(dict(msg="done"), 200)
