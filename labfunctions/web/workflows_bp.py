# pylint: disable=unused-argument
import pathlib
from datetime import datetime
from typing import List, Optional

from pydantic.error_wrappers import ValidationError
from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi

from labfunctions import types
from labfunctions.conf.server_settings import settings
from labfunctions.defaults import API_VERSION
from labfunctions.errors.generics import WorkflowRegisterError
from labfunctions.managers import projects_mg, runtimes_mg, workflows_mg
from labfunctions.security.web import protected
from labfunctions.utils import (
    get_query_param,
    parse_page_limit,
    run_async,
    secure_filename,
)

from .utils import get_job_manager, get_scheduler2

workflows_bp = Blueprint("workflows", url_prefix="workflows", version=API_VERSION)


@workflows_bp.get("/<projectid>/notebooks/_files")
@openapi.parameter("projectid", str, "path")
@protected()
def notebooks_list(request, projectid):
    """
    List file workflows
    TODO: implement a way to register notebooks from each project
    """
    # pylint: disable=unused-argument

    # nb_files = list_workflows()
    nb_files = []

    return json(nb_files)


@workflows_bp.post("/<projectid>/notebooks/_run")
@openapi.parameter("projectid", str, "path")
@openapi.body({"application/json": types.NBTask})
@openapi.response(202, types.ExecutionNBTask, "Notebook execution task")
@protected()
async def notebooks_run(request, projectid):
    """
    Run a notebook
    """
    # pylint: disable=unused-argument

    session = request.ctx.session
    try:
        task = types.NBTask(**request.json)
    except ValidationError:
        return json(dict(msg="wrong params"), 400)

    scheduler = get_scheduler2(request)
    nb_ctx = await scheduler.enqueue_notebook(session, projectid=projectid, task=task)
    return json(nb_ctx.dict(), 202)


@workflows_bp.get("/<projectid>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, types.WorkflowsList, "Notebook Workflow already exist")
@protected()
async def workflows_list(request, projectid):
    """List workflows registered in the database"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    async with session.begin():
        result = await workflows_mg.get_all(session, projectid)
        data = [r.dict() for r in result]

    return json(dict(rows=data), 200)


@workflows_bp.post("/<projectid>")
@openapi.body({"application/json": types.WorkflowDataWeb})
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
        wfd = types.WorkflowDataWeb(**request.json)
    except ValidationError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session

    async with session.begin():
        try:
            wfid = await workflows_mg.register(session, projectid, wfd)
            wfd.wfid = wfid
            if wfd.schedule:
                job_manager = get_job_manager(request)
                await job_manager.register_workflow(
                    session, projectid=projectid, wd=wfd
                )
            # if wfd.schedule and wfd.enabled:
            #    await scheduler.schedule(projectid, wfid, wfd)
        except WorkflowRegisterError as e:
            return json(dict(msg="workflow already exist"), status=200)

        return json(dict(wfid=wfid), status=201)


@workflows_bp.put("/<projectid>")
@openapi.body({"application/json": types.WorkflowDataWeb})
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
        wfd = types.WorkflowDataWeb(**request.json)
        if not wfd.wfid:
            return json(dict(msg="wrong params"), 400)

    except ValidationError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    # scheduler = get_scheduler(request, is_async=is_async)

    async with session.begin():
        try:
            wfid = await workflows_mg.register(session, projectid, wfd, update=True)
            if wfd.schedule:
                job_manager = get_job_manager(request)
                await job_manager.register_workflow(
                    session, projectid=projectid, wd=wfd
                )
            # if wfd.schedule and wfd.enabled:
            #    await scheduler.schedule(projectid, wfid, wfd)
        except WorkflowRegisterError as e:
            return json(dict(msg=str(e)), status=503)

        return json(dict(wfid=wfid), status=201)


@workflows_bp.delete("/<projectid>/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@protected()
async def workflow_delete(request, projectid, wfid):
    """Delete from db and queue a workflow"""
    # pylint: disable=unused-argument
    session = request.ctx.session
    job_manager = get_job_manager(request)
    # scheduler = get_scheduler(request, is_async=is_async)
    async with session.begin():
        # await scheduler.delete_workflow(session, projectid, wfid)
        await job_manager.unregister_workflow(wfid)
        await workflows_mg.delete_wf(session, projectid, wfid)
        await session.commit()

    return json(dict(msg="done"), 200)


@workflows_bp.get("/<projectid>/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(200, types.WorkflowDataWeb)
@openapi.response(404, {"msg": str}, description="Workflow not found")
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


@workflows_bp.post("/<projectid>/_run/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(202, types.ExecutionNBTask)
@openapi.response(404, {"msg": str})
@protected()
async def workflow_enqueue(request, projectid, wfid):
    """Enqueue a worflow"""
    scheduler = get_scheduler2(request)
    session = request.ctx.session
    async with session.begin():
        ctx = await scheduler.enqueue_workflow(session, projectid=projectid, wfid=wfid)
        if ctx:
            return json(ctx.dict(), 202)

    return json(dict(msg=f"{wfid} not found for pid {projectid}"), 404)


# @workflows_bp.post("/<projectid>/_ctx/<wfid>")
# @openapi.parameter("projectid", str, "path")
# @openapi.parameter("wfid", str, "path")
# @openapi.response(200)
# @openapi.response(404, {"msg": str}, description="Job not found")
# @protected()
# async def workflow_generate_ctx(request, projectid, wfid):
#     """Enqueue a workflow on demand"""
#     # pylint: disable=unused-argument
#     execid = ExecID()
#     signed = execid.firm_with(ExecID.types.web)
#
#     session = request.ctx.session
#     async with session.begin():
#         nb_ctx = await workflows_mg.prepare_notebook_job_async(
#             session, projectid, wfid, signed
#         )
#     # job = await run_async(scheduler.dispatcher, projectid, wfid)
#     return json(nb_ctx.dict(), 200)
