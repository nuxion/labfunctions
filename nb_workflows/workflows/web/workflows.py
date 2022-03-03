# pylint: disable=unused-argument
import asyncio
import pathlib
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

from nb_workflows.utils import (get_query_param, list_workflows,
                                parse_page_limit, run_async, secure_filename)
from nb_workflows.workflows.entities import NBTask
from nb_workflows.workflows.scheduler import (QueueExecutor, SchedulerExecutor,
                                              scheduler_dispatcher)
from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import protected

workflows_bp = Blueprint("workflows", url_prefix="workflows")


def _get_scheduler(qname="default") -> SchedulerExecutor:

    current_app = Sanic.get_app("nb_workflows")
    r = current_app.ctx.rq_redis
    return SchedulerExecutor(r, qname=qname)


def _get_q_executor(qname="default") -> QueueExecutor:
    current_app = Sanic.get_app("nb_workflows")
    r = current_app.ctx.rq_redis

    return QueueExecutor(r, qname=qname)


@workflows_bp.post("/<projectid>/notebooks/_run")
@openapi.body({"application/json": NBTask})
@openapi.parameter("projectid", str, "path")
@openapi.response(202, {"executionid": str}, "Task executed")
@openapi.response(400, {"msg": str}, "Wrong params")
@protected()
def launch_task(request, projectid):
    """
    Prepare and execute a Notebook Workflow Job based on a filename
    This endpoint allows to execution any notebook without restriction.
    The file should exist remotetly but it doesn't need to be
    previously scheduled
    """
    try:
        nb_task = NBTask(**request.json)
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    Q = _get_q_executor()

    job = Q.enqueue_notebook(nb_task)

    return json(dict(executionid=job.id), status=202)


@workflows_bp.get("/<projectid>/notebooks/_files")
@openapi.parameter("projectid", str, "path")
@protected()
def list_nb_workflows(request, projectid):
    """
    List file workflows
    """
    # pylint: disable=unused-argument

    nb_files = list_workflows()

    return json(nb_files)


@workflows_bp.post("/<projectid>/notebooks/_upload")
@openapi.parameter("projectid", str, "path")
@protected()
def upload_notebook(request, projectid):
    """
    Upload a notebook file to the server
    """
    # pylint: disable=unused-argument

    nb_files = list_workflows()

    return json(nb_files)


@workflows_bp.get("/<projectid>/schedule")
@openapi.parameter("projectid", str, "path")
@protected()
async def list_schedule(request, projectid):
    """List jobs registered in the database"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    scheduler = _get_scheduler()

    async with session.begin():
        result = await scheduler.get_schedule_db(session, projectid)

    return json(result)


@workflows_bp.delete("/<projectid>/schedule/<jobid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("jobid", str, "path")
@protected()
async def schedule_delete(request, projectid, jobid):
    """Get a ScheduleJob"""
    # pylint: disable=unused-argument
    scheduler = _get_scheduler()
    session = request.ctx.session
    async with session.begin():
        await scheduler.delete_workflow(session, jobid)
        await session.commit()

    return json(dict(msg="done"), 200)


@workflows_bp.post("/<projectid>/schedule")
@openapi.body({"application/json": NBTask})
@openapi.parameter("projectid", str, "path")
@openapi.response(200, {"msg": str}, "Notebook Workflow already exist")
@openapi.response(201, {"jobid": str}, "Notebook Workflow registered")
@openapi.response(400, {"msg": str}, description="wrong params")
@openapi.response(404, {"msg": str}, description="invalid projectid")
@protected()
async def create_notebook_schedule(request, projectid):
    """
    Register a notebook workflow and schedule it
    """
    try:
        nb_task = NBTask(**request.json)
        if not nb_task.schedule:
            return json(dict(msg="schedule information is needed"), 400)
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    scheduler = _get_scheduler()

    async with session.begin():
        try:
            rsp = await scheduler.schedule(session, projectid, request.json)
        except KeyError:
            return json(dict(msg="notebook workflow already exists"),
                        status=200)
        except AttributeError:
            return json(dict(msg=f"Invalid project id {projectid}"),
                        status=404)

    return json(dict(jobid=rsp), status=201)


@workflows_bp.put("/<projectid>/schedule")
@openapi.body({"application/json": NBTask})
@openapi.parameter("projectid", str, "path")
@openapi.response(202, {"jobid": str}, "Notebook Workflow accepted")
@openapi.response(400, {"msg": str}, description="wrong params")
@openapi.response(503, {"msg": str}, description="Error persiting the job")
@protected()
async def update_notebook_schedule(request, projectid):
    """
    Register a notebook workflow and schedule it
    """
    try:
        nb_task = NBTask(**request.json)
        if not nb_task.schedule:
            return json(dict(msg="schedule information is needed"), 400)
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    scheduler = _get_scheduler()

    async with session.begin():
        try:
            rsp = await scheduler.schedule(session, request.json, update=True)
        except KeyError:
            return json(
                dict(msg="An integrity error persisting the job"), status=503
            )

    return json(dict(jobid=rsp), status=202)


@workflows_bp.get("/<projectid>/schedule/<jobid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("jobid", str, "path")
@openapi.response(200)
@openapi.response(404, {"msg": str}, description="Job not found")
@protected()
async def schedule_one_job(request, projectid, jobid):
    """Delete a job from RQ and DB"""
    # pylint: disable=unused-argument
    scheduler = _get_scheduler()
    session = request.ctx.session
    async with session.begin():
        obj_dict = await scheduler.get_jobid_db(session, jobid)

    if obj_dict:
        return json(obj_dict, 200)
    return json(dict(msg="Not found"), 404)


@workflows_bp.post("/<projectid>/schedule/<jobid>/_run")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("jobid", str, "path")
@openapi.response(202, dict(executionid=str), "Execution id of the task")
@protected()
def schedule_run(request, projectid, jobid):
    """
    Manually execute a registered schedule task
    """
    Q = _get_q_executor()

    job = Q.enqueue(scheduler_dispatcher, jobid)

    return json(dict(executionid=job.id), status=202)
