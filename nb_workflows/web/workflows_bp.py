# pylint: disable=unused-argument
import pathlib
from datetime import datetime
from typing import List, Optional

from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import protected

from nb_workflows.executors.context import ExecID
from nb_workflows.managers import workflows_mg
from nb_workflows.scheduler import SchedulerExecutor, scheduler_dispatcher
from nb_workflows.types import (
    NBTask,
    ScheduleData,
    WorkflowData,
    WorkflowDataWeb,
    WorkflowsList,
)
from nb_workflows.utils import (
    get_query_param,
    parse_page_limit,
    run_async,
    secure_filename,
)

from .utils import get_scheduler

workflows_bp = Blueprint("workflows", url_prefix="workflows")


@workflows_bp.get("/<projectid>/notebooks/_files")
@openapi.parameter("projectid", str, "path")
@protected()
def list_nb_workflows(request, projectid):
    """
    List file workflows
    TODO: implement a way to register notebooks from each project
    """
    # pylint: disable=unused-argument

    # nb_files = list_workflows()
    nb_files = []

    return json(nb_files)


@workflows_bp.get("/<projectid>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, WorkflowsList, "Notebook Workflow already exist")
@protected()
async def workflows_list(request, projectid):
    """List workflows registered in the database"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    async with session.begin():
        result = await workflows_mg.get_all(session, projectid)
        data = [r.dict() for r in result]

    return json(dict(rows=data), 200)


@workflows_bp.delete("/<projectid>/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@protected()
async def workflow_delete(request, projectid, wfid):
    """Delete from db and queue a workflow"""
    # pylint: disable=unused-argument
    session = request.ctx.session
    scheduler = get_scheduler()
    async with session.begin():
        await scheduler.delete_workflow(session, projectid, wfid)
        await session.commit()

    return json(dict(msg="done"), 200)


@workflows_bp.post("/<projectid>")
@openapi.body({"application/json": WorkflowDataWeb})
@openapi.parameter("projectid", str, "path")
@openapi.response(200, {"msg": str}, "Notebook Workflow already exist")
@openapi.response(201, {"wfid": str}, "Notebook Workflow registered")
@openapi.response(400, {"msg": str}, description="wrong params")
@openapi.response(404, {"msg": str}, description="project not found")
@protected()
async def workflow_create(request, projectid):
    """
    Register a notebook workflow and schedule it
    """
    try:
        wfd = WorkflowDataWeb(**request.json)
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    scheduler = get_scheduler()

    async with session.begin():
        try:
            wfid = await workflows_mg.register(session, projectid, wfd)
            # if nb_task.schedule and nb_task.enabled:
            #     await scheduler.schedule(projectid, wfid, nb_task)
        except KeyError as e:
            return json(dict(msg="workflow already exist"), status=200)
        except AttributeError as e:
            return json(dict(msg="project not found"), status=404)

        return json(dict(wfid=wfid), status=201)


@workflows_bp.put("/<projectid>")
@openapi.body({"application/json": NBTask})
@openapi.parameter("projectid", str, "path")
@openapi.response(200, {"wfid": str}, "Notebook Workflow accepted")
@openapi.response(400, {"msg": str}, description="wrong params")
@openapi.response(503, {"msg": str}, description="Error persiting the job")
@protected()
async def workflow_update(request, projectid):
    """
    Register a notebook workflow and schedule it
    """
    try:
        nb_task = NBTask(**request.json)
        if nb_task.schedule:
            nb_task.schedule = ScheduleData(**request.json["schedule"])
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    scheduler = get_scheduler()

    async with session.begin():
        try:
            wfid = await workflows_mg.register(session, projectid, nb_task, update=True)
            # await scheduler.cancel_job_async(wfid)
            # if nb_task.enabled and nb_task.schedule:
            #    await scheduler.schedule(projectid, wfid, nb_task)
        except KeyError as e:
            return json(dict(msg="workflow already exist"), status=200)
        except AttributeError:
            return json(dict(msg="project not found"), status=404)

        return json(dict(wfid=wfid), status=201)


@workflows_bp.get("/<projectid>/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(200, WorkflowData)
@openapi.response(404, {"msg": str}, description="Job not found")
@protected()
async def workflow_get(request, projectid, wfid):
    """Get a workflow by projectid"""
    # pylint: disable=unused-argument
    session = request.ctx.session
    async with session.begin():
        wd = await workflows_mg.get_by_wfid_prj(session, projectid, wfid)

    if wd:
        return json(wd.dict(), 200)
    return json(dict(msg="Not found"), 404)


@workflows_bp.post("/<projectid>/queue/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(202, dict(execid=str))
@protected()
async def workflow_enqueue(request, projectid, wfid):
    """Get a workflow by projectid"""
    # pylint: disable=unused-argument
    sche = get_scheduler()
    execid = ExecID()
    signed = execid.firm("web")
    job = await run_async(sche.dispatcher, projectid, wfid, signed)

    return json(dict(execid=job.id), 202)


@workflows_bp.post("/<projectid>/_ctx/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(200)
@openapi.response(404, {"msg": str}, description="Job not found")
@protected()
async def workflow_generate_ctx(request, projectid, wfid):
    """Enqueue a workflow on demand"""
    # pylint: disable=unused-argument
    execid = ExecID()
    signed = execid.firm("web")
    session = request.ctx.session
    async with session.begin():
        nb_ctx = await workflows_mg.prepare_notebook_job_async(
            session, projectid, wfid, signed
        )
    # job = await run_async(scheduler.dispatcher, projectid, wfid)
    return json(nb_ctx.dict(), 200)
