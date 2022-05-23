# pylint: disable=unused-argument
import json as std_json
import pathlib
from dataclasses import asdict

import httpx
from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi

from labfunctions import defaults
from labfunctions.conf.server_settings import settings
from labfunctions.defaults import API_VERSION
from labfunctions.managers import history_mg
from labfunctions.managers.users_mg import inject_user
from labfunctions.security.web import protected
from labfunctions.types import ExecutionResult, HistoryRequest, NBTask
from labfunctions.utils import today_string
from labfunctions.web.utils import get_kvstore, get_query_param2, get_scheduler2

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


@history_bp.get("/<projectid>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "Found")
@openapi.response(404, dict(msg=str), "Not Found")
@openapi.parameter("lt", int, "lt")
@protected()
async def history_get_all(request, projectid):
    """Get the status of the last job executed"""
    # pylint: disable=unused-argument
    lt = get_query_param2(request, "lt", 1)
    session = request.ctx.session
    async with session.begin():
        h = await history_mg.get_last(session, projectid, limit=lt)
        if h.rows:
            return json(h.dict(), 200)

    return json(dict(msg="not found"), 404)


@history_bp.get("/<projectid>/detail/<execid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("execid", str, "path")
@openapi.response(200, "Found")
@openapi.response(404, dict(msg=str), "Not Found")
@protected()
async def history_detail_job(request, projectid: str, execid: str):
    """Get the status of the last job executed"""
    # pylint: disable=unused-argument
    session = request.ctx.session
    async with session.begin():
        h = await history_mg.get_one(session, execid)
        if h:
            return json(h.dict(), 200)

        return json(dict(msg="not found"), 404)


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
    lt = get_query_param2(request, "lt", 1)
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
    kv_store = get_kvstore(request)

    today = today_string(format_="day")
    root = pathlib.Path(projectid)
    output_dir = root / defaults.NB_OUTPUTS / "ok" / today

    file_body = request.files["file"][0].body
    output_name = request.form["output_name"][0]

    fp = str(output_dir / output_name)
    # await fsrv.put(fp, file_body)
    await kv_store.put(fp, file_body)

    return json(dict(msg="OK"), 201)


@history_bp.post("/<projectid>/_output_fail")
@openapi.parameter("projectid", str, "path")
@protected()
async def history_output_fail(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument

    kv_store = get_kvstore(request)

    today = today_string(format_="day")
    root = pathlib.Path(projectid)
    output_dir = root / defaults.NB_OUTPUTS / "errors" / today

    file_body = request.files["file"][0].body
    output_name = request.form["output_name"][0]

    fp = str(output_dir / output_name)
    await kv_store.put(fp, file_body)

    return json(dict(msg="OK"), 201)


@history_bp.get("/<projectid>/_get_output")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("file", str, "query")
@protected()
async def history_get_output(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument
    uri = request.args.get("file")
    key = f"{projectid}/{uri}"
    response = await request.respond(content_type="application/octet-stream")
    kv_store = get_kvstore(request)
    async for chunk in kv_store.get_stream(key):
        await response.send(chunk)
    await response.eof()


@history_bp.get("/<projectid:str>/task/<execid:str>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "project")
@openapi.response(404, "not found")
@protected()
async def history_get_task(request, projectid, execid):
    """Get private key based on the project"""
    # pylint: disable=unused-argument

    scheduler = get_scheduler2(request)
    task = await scheduler.get_task(execid)
    if not task:
        return json({"msg": "not found"}, 404)

    return json(task.dict(), 200)
