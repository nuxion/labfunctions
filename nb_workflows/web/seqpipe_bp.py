# pylint: disable=unused-argument
import pathlib
from datetime import datetime
from typing import List, Optional

from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import protected

from nb_workflows.executors.context import ExecID
from nb_workflows.managers import seqpipe_mg
from nb_workflows.scheduler import SchedulerExecutor, scheduler_dispatcher
from nb_workflows.types import NBTask, ScheduleData, SeqPipe, WorkflowData
from nb_workflows.utils import (
    get_query_param,
    parse_page_limit,
    run_async,
    secure_filename,
)

from .utils import get_scheduler

seqpipe_bp = Blueprint("seqpipes", url_prefix="seq-pipes")


@seqpipe_bp.post("/<projectid>")
@openapi.body({"application/json": SeqPipe})
@openapi.parameter("projectid", str, "path")
@openapi.response(200, {"msg": str}, "Pipe already exist")
@openapi.response(201, {"pipeid": str}, "SeqPipe registered")
@openapi.response(400, {"msg": str}, description="wrong params")
@openapi.response(404, {"msg": str}, description="project not found")
@protected()
async def seqpipe_create(request, projectid):
    """
    Creates a Sequencial Pipe
    """
    try:
        pipe = SeqPipe(**request.json)
    except TypeError:
        return json(dict(msg="wrong params"), 400)

    session = request.ctx.session
    # scheduler = get_scheduler()

    async with session.begin():
        pipeid = await seqpipe_mg.create(session, projectid, pipe)
        return json(dict(pipeid=pipeid), status=201)


@seqpipe_bp.get("/<projectid>/<pipid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("pipeid", str, "path")
@openapi.response(200, {"msg": str}, "Pipe already exist")
@openapi.response(404, {"msg": str}, "Pipe not found")
@protected()
async def seqpipe_get_one(request, projectid, pipeid):
    """
    Get a Sequencial Pipe by PipeID
    """
    pipe = SeqPipe(**request.json)

    session = request.ctx.session
    # scheduler = get_scheduler()

    async with session.begin():
        pipeid = await seqpipe_mg.get_one(session, projectid, pipe)
        if pipeid:
            return json(dict(pipeid=pipeid), status=200)
        else:
            return json(dict(msg=f"Not found {pipeid}"), status=404)
