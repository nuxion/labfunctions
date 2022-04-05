# pylint: disable=unused-argument
import glob
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

import aiofiles
from redis import Redis
from sanic import Blueprint, Sanic, exceptions
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import protected

from nb_workflows.conf.defaults import API_VERSION
from nb_workflows.conf.server_settings import settings
from nb_workflows.core.core import nb_job_executor
from nb_workflows.core.entities import (
    ExecutionResult,
    HistoryRequest,
    NBTask,
    ProjectData,
)
from nb_workflows.core.managers import history, projects
from nb_workflows.core.registers import register_history_db
from nb_workflows.core.scheduler_deprecated import (
    QueueExecutor,
    SchedulerExecutor,
    scheduler_dispatcher,
)
from nb_workflows.utils import (
    get_query_param,
    parse_page_limit,
    run_async,
    secure_filename,
)

rqjobs_bp = Blueprint("rqjobs", url_prefix="rqjobs", version=API_VERSION)


def _get_scheduler(qname="default") -> SchedulerExecutor:

    current_app = Sanic.get_app("nb_workflows")
    r = current_app.ctx.rq_redis
    return SchedulerExecutor(r, qname=qname)


def _get_q_executor(qname="default") -> QueueExecutor:
    current_app = Sanic.get_app("nb_workflows")
    r = current_app.ctx.rq_redis

    return QueueExecutor(r, qname=qname)


def list_workflows():
    notebooks = []
    files = glob(f"{settings.BASE_PATH}/{settings.NB_WORKFLOWS}*")
    for x in files:
        if ".ipynb" or ".py" in x:
            notebooks.append(x.split("/")[-1].split(".")[0])
    return notebooks


@dataclass
class JobResponse:
    wfid: str
    workflow: NBTask


@dataclass
class JobDetail:
    wfid: str
    func_name: str
    # workflow: NBTask
    created_at: str


@rqjobs_bp.get("/")
@openapi.response(200, List[JobDetail], "Task Scheduled")
@protected()
def list_scheduled_redis(request):
    """
    List the jobs scheduled in the scheduler
    """
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()
    jobs = scheduler.list_jobs()

    return json(jobs, 200)


@rqjobs_bp.delete("/_cancel/<wfid>")
@openapi.parameter("wfid", str, "path")
@protected()
async def cancel_job(request, wfid):
    """delete a scheduler job from redis"""
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()
    await run_async(scheduler.cancel_job, wfid)
    return json(dict(msg="done"), 200)


@rqjobs_bp.delete("/_cancel_all")
@protected()
async def schedule_cancel_all(request):
    """Cancel all the jobs in the queue"""
    # pylint: disable=unused-argument

    scheduler = _get_scheduler()

    await run_async(scheduler.cancel_all)

    return json(dict(msg="done"), 200)


@rqjobs_bp.get("/<wfid>")
@openapi.parameter("wfid", str, "path")
@protected()
def get_job_result(request, wfid):
    """Get job result from the queue"""
    Q = _get_q_executor()
    job = Q.fetch_job(wfid)
    result = job.result
    if result:
        result = asdict(result)

    return json(
        dict(
            wfid=job.id,
            status=job.get_status(),
            result=result,
            position=job.get_position(),
        )
    )


@rqjobs_bp.get("/failed")
@protected()
def get_failed_jobs(request):
    """Get jobs failed in RQ"""
    Q = _get_q_executor()

    jobs = Q.get_jobs_ids("failed")

    return json(dict(rows=jobs, total=len(jobs)))


@rqjobs_bp.delete("/failed")
@openapi.parameter("remove", bool, "query")
@protected()
def delete_failed_jobs(request):
    """Remove failed jobs from the queue"""

    to_remove = get_query_param(request, "remove", False)
    Q = _get_q_executor()

    jobs = Q.remove_jobs("failed", to_remove)

    return json(dict(rows=jobs, total=len(jobs)))


@rqjobs_bp.get("/running")
@protected()
def get_running_jobs(request):
    """Get jobs Running"""
    Q = _get_q_executor()

    jobs = Q.get_jobs_ids("started")

    return json(dict(rows=jobs, total=len(jobs)))
