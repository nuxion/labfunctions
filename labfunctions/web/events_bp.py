import asyncio
import json as jsondef

import aioredis
import async_timeout
from sanic import Blueprint
from sanic.response import empty, json, stream
from sanic_ext import openapi

from labfunctions.defaults import API_VERSION
from labfunctions.events import EventManager
from labfunctions.security.web import protected
from labfunctions.types.events import EventSSE
from labfunctions.utils import get_query_param, secure_filename

events_bp = Blueprint("events", url_prefix="events", version=API_VERSION)


def get_event_manager(request) -> EventManager:
    return request.ctx.events


@events_bp.get("/<projectid>/<execid>/_listen")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("execid", str, "path")
@openapi.parameter("last", str, "query")
@openapi.response(200, "Found")
@openapi.response(404, dict(msg=str), "Not Found")
@protected()
async def event_listen(request, projectid, execid):
    # redis = get_web_redis(request)
    em = get_event_manager(request)
    last = request.args.get("last", "$")

    response = await request.respond(
        content_type="text/event-stream", headers={"Cache-Control": "no-store"}
    )

    channel = EventManager.generate_channel(projectid, execid)
    keep = True
    while keep:
        rsp = await em.read(channel, last)
        if rsp:
            for r in rsp:
                if r.event == "control" and r.data == "exit":
                    keep = False
                msg = em.format_sse(r)
                await response.send(msg)
            last = r.id
        else:
            keep = False

    await response.eof()


@events_bp.post("/<projectid>/<execid>/_publish")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("execid", str, "path")
@openapi.response(204)
@openapi.response(404, dict(msg=str), "Not Found")
@protected()
async def event_publish(request, projectid, execid):
    evt = EventSSE(**request.json)

    em = get_event_manager(request)
    channel = EventManager.generate_channel(projectid, execid)
    await em.publish(channel, evt)

    return empty()
