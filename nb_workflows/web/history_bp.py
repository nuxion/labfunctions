# pylint: disable=unused-argument
import json as std_json
import pathlib
from dataclasses import asdict

import httpx
from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import inject_user, protected

from nb_workflows.conf import defaults
from nb_workflows.conf.defaults import API_VERSION
from nb_workflows.conf.server_settings import settings
from nb_workflows.core.registers import register_history_db
from nb_workflows.io import AsyncFileserver
from nb_workflows.managers import history_mg
from nb_workflows.types import ExecutionResult, HistoryRequest, NBTask
from nb_workflows.utils import get_query_param, today_string

history_bp = Blueprint("history", url_prefix="history", version=API_VERSION)

# async def validate_project(request):
#     request.ctx.user = await extract_user_from_request(request)


@history_bp.post("/")
@openapi.body({"application/json": ExecutionResult})
@openapi.response(201, "Created")
@protected()
async def history_create(request):
    """Register a jobexecution"""
    # pylint: disable=unused-argument
    dict_ = request.json
    exec_result = ExecutionResult(**dict_)

    session = request.ctx.session
    async with session.begin():
        hm = await history_mg.create(session, exec_result)

    return json(dict(msg="created"), 201)


@history_bp.get("/<projectid>/<wfid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("wfid", str, "path")
@openapi.response(200, "Found")
@openapi.response(404, dict(msg=str), "Not Found")
@openapi.parameter("lt", int, "lt")
@protected()
async def history_last_job(request, wfid, projectid):
    """Get the status of the last job executed"""
    # pylint: disable=unused-argument
    lt = get_query_param(request, "lt", 1)
    session = request.ctx.session
    async with session.begin():
        h = await history_mg.get_last(session, projectid, wfid, limit=lt)
        if h.rows:
            return json(h.dict(), 200)

        return json(dict(msg="not found"), 404)


@history_bp.post("/<projectid>/_output_ok")
@openapi.parameter("projectid", str, "path")
@protected()
async def history_output_ok(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument
    fsrv = AsyncFileserver(settings.FILESERVER)
    today = today_string(format_="day")
    root = pathlib.Path(projectid)
    output_dir = root / defaults.NB_OUTPUTS / "ok" / today

    file_body = request.files["file"][0].body
    output_name = request.form["output_name"][0]

    fp = str(output_dir / output_name)
    await fsrv.put(fp, file_body)

    return json(dict(msg="OK"), 201)


@history_bp.post("/<projectid>/_output_fail")
@openapi.parameter("projectid", str, "path")
@protected()
async def history_output_fail(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument

    fsrv = AsyncFileserver(settings.FILESERVER)
    today = today_string(format_="day")
    root = pathlib.Path(projectid)
    fp = root / defaults.NB_OUTPUTS / "fail" / today

    file_body = request.files["file"][0].body
    output_name = request.form["output_name"][0]

    fp = str(root / output_name)
    await fsrv.put(fp, file_body)

    return json(dict(msg="OK"), 201)


@history_bp.get("/<projectid>/_get_output")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("file", str, "query")
async def history_get_output(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument
    uri = request.args.get("file")
    response = await request.respond(content_type="application/octet-stream")
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET", f"{settings.FILESERVER}/{projectid}/{uri}"
        ) as r:
            async for chunk in r.aiter_bytes():
                await response.send(chunk)

    await response.eof()
