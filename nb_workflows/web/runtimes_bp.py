from typing import List

from sanic import Blueprint, Request
from sanic.response import empty, json, stream
from sanic_ext import openapi
from sanic_jwt import inject_user, protected

from nb_workflows.conf.defaults import API_VERSION
from nb_workflows.managers import runtimes_mg
from nb_workflows.types.docker import RuntimeVersionData, RuntimeVersionOrm
from nb_workflows.web.utils import get_query_param2

runtimes_bp = Blueprint("runtimes", url_prefix="runtimes", version=API_VERSION)


@runtimes_bp.get("/<projectid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("lt", int, "query")
@openapi.response(200, List[RuntimeVersionOrm], "Created")
@protected()
async def runtimes_list(request: Request, projectid: str):
    """get a list of runtimes, by default they are ordered by created_at field"""
    lt = get_query_param2(request, "lt", 1)
    session = request.ctx.session
    async with session.begin():
        rows = await runtimes_mg.get_list(session, projectid, limit=lt)

    return json([r.dict() for r in rows], 200)


@runtimes_bp.post("/<projectid>")
@openapi.body({"application/json": RuntimeVersionData})
@openapi.parameter("projectid", str, "path")
@openapi.response(200)
@openapi.response(201)
@protected()
async def runtimes_create(request: Request, projectid):
    session = request.ctx.session
    rd = RuntimeVersionData(**request.json)
    rd.projectid = projectid
    async with session.begin():
        created = await runtimes_mg.create(session, rd)
    code = 201
    if not created:
        code = 200

    return json({"msg": "ok"}, code)


@runtimes_bp.delete("/<projectid>/<id: int>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("id", str, "path")
@openapi.response(200)
@protected()
async def runtimes_delete(request: Request, projectid: str, id: int):
    session = request.ctx.session
    async with session.begin():
        await runtimes_mg.delete_by_id(session, id)

    return json({"msg": "ok"}, 200)
