from contextvars import ContextVar

import aioredis
from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize

from nb_workflows.auth import users
from nb_workflows.conf import Config
from nb_workflows.db.nosync import AsyncSQL


def my_authenticate(requests, *args, **kwargs):
    pass


app = Sanic("nb_workflows")
Initialize(
    app,
    authenticate=users.authenticate_web,
    secret=Config.SECRET_KEY,
)


# app.blueprint(workflows_bp)

app.config.CORS_ORIGINS = "*"
Extend(app)
app.ext.openapi.add_security_scheme(
    "token",
    "http",
    scheme="bearer",
    bearer_format="JWT",
)
app.ext.openapi.secured()
app.ext.openapi.secured("token")

db = AsyncSQL(Config.ASQL)
_base_model_session_ctx = ContextVar("session")


def _parse_page_limit(request, def_pg="1", def_lt="100"):
    strpage = request.args.get("page", [def_pg])
    strlimit = request.args.get("limit", [def_lt])
    page = int(strpage[0])
    limit = int(strlimit[0])

    return page, limit


@app.listener("before_server_start")
async def startserver(current_app, loop):
    """Initialization of the redis and sqldb clients"""
    if Config.WEB_REDIS:
        current_app.ctx.redis = aioredis.from_url(
            Config.WEB_REDIS, decode_responses=True
        )
    current_app.ctx.db = db
    await current_app.ctx.db.init()


@app.listener("after_server_stop")
async def shutdown(current_app, loop):
    await current_app.ctx.db.engine.dispose()
    await current_app.ctx.redis.close()


@app.middleware("request")
async def inject_session(request):
    current_app = Sanic.get_app("nb_workflows")
    request.ctx.session = app.ctx.db.sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(
        request.ctx.session
    )

    request.ctx.dbconn = db.engine


@app.middleware("response")
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()


@app.get("/status")
async def status_handler(request):
    return json(dict(msg="We are ok"))
