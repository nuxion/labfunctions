from sanic import Blueprint, Request, Sanic

from labfunctions import defaults
from labfunctions.conf.server_settings import settings
from labfunctions.control import JobManager, SchedulerExec
from labfunctions.io.kvspec import AsyncKVSpec


def get_query_param2(request, key, default_val=None):
    val = request.args.get(key, default_val)
    return val


def parse_page_limit(request, def_pg="1", def_lt="100"):
    strpage = request.args.get("page", [def_pg])
    strlimit = request.args.get("limit", [def_lt])
    page = int(strpage[0])
    limit = int(strlimit[0])

    return page, limit


def get_scheduler2(
    request: Request,
) -> SchedulerExec:
    current_app = Sanic.get_app(request.app.name)
    return current_app.ctx.scheduler


def get_job_manager(request: Request) -> JobManager:
    current_app = Sanic.get_app(request.app.name)
    return current_app.ctx.job_manager


def get_kvstore(request: Request) -> AsyncKVSpec:
    return Sanic.get_app(request.app.name).ctx.kv_store


async def stream_reader(request: Request):
    """
    It's a wrapper to be used to yield response from a stream
    to another stream.

    it's used with project upload data to stream upload zip directly to
    the fileserver instead of load data in memory.
    """
    while True:
        body = await request.stream.read()
        if body is None:
            break
        yield body
