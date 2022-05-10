from typing import List

from sanic import Blueprint, Request
from sanic.response import empty, json, stream
from sanic_ext import openapi

from labfunctions.defaults import API_VERSION
from labfunctions.managers import runtimes_mg
from labfunctions.security.web import protected
from labfunctions.types.runtimes import RuntimeData, RuntimeReq
from labfunctions.web.utils import get_query_param2

runtimes_bp = Blueprint("runtimes", url_prefix="runtimes", version=API_VERSION)


@runtimes_bp.get("/<projectid>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("lt", int, "query")
@openapi.response(200, List[RuntimeData], "Collection of runtimes")
@protected()
async def runtimes_list(request: Request, projectid: str):
    """get a list of runtimes, by default they are ordered by created_at field"""
    lt = get_query_param2(request, "lt", 10)
    session = request.ctx.session
    async with session.begin():
        rows = await runtimes_mg.get_list(session, projectid, limit=lt)

    return json([r.dict() for r in rows], 200)


@runtimes_bp.post("/<projectid>")
@openapi.body({"application/json": RuntimeReq})
@openapi.parameter("projectid", str, "path")
@openapi.response(200)
@openapi.response(201)
@protected()
async def runtimes_create(request: Request, projectid):
    session = request.ctx.session
    rq = RuntimeReq(**request.json)
    async with session.begin():
        created = await runtimes_mg.create(session, rq)
    code = 201
    if not created:
        code = 200
    return json({"msg": "ok"}, code)


@runtimes_bp.delete("/<projectid>/<rid: str>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("id", str, "path")
@openapi.response(200)
@protected()
async def runtimes_delete(request: Request, projectid: str, rid: str):
    session = request.ctx.session
    async with session.begin():
        await runtimes_mg.delete_by_rid(session, rid)

    return json({"msg": "ok"}, 200)
