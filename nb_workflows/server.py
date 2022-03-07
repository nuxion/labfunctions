from contextvars import ContextVar

import aioredis
from redis import Redis
from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize

from nb_workflows.auth import authenticate, users
from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.db.nosync import AsyncSQL

app = Sanic(defaults.SANIC_APP_NAME)

Initialize(
    app,
    authentication_class=authenticate.NBAuthentication,
    secret=settings.SECRET_KEY,
    refresh_token_enabled=True,
    # retrieve_refresh_token=users.retrieve_refresh_token,
    # store_refresh_token=users.store_refresh_token,
    # retrieve_user=users.retrieve_user,
)


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

db = AsyncSQL(settings.ASQL)
_base_model_session_ctx = ContextVar("session")


@app.listener("before_server_start")
async def startserver(current_app, loop):
    """Initialization of the redis and sqldb clients"""
    current_app.ctx.web_redis = aioredis.from_url(
        settings.WEB_REDIS, decode_responses=True
    )

    _cfg = settings.rq2dict()
    redis = Redis(**_cfg)
    current_app.ctx.rq_redis = redis

    current_app.ctx.db = db
    await current_app.ctx.db.init()


@app.listener("after_server_stop")
async def shutdown(current_app, loop):
    await current_app.ctx.db.engine.dispose()
    # await current_app.ctx.redis.close()


@app.middleware("request")
async def inject_session(request):
    current_app = Sanic.get_app(defaults.SANIC_APP_NAME)
    request.ctx.session = app.ctx.db.sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
    request.ctx.web_redis = current_app.ctx.web_redis

    request.ctx.dbconn = db.engine


@app.middleware("response")
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()


@app.get("/status")
async def status_handler(request):
    return json(dict(msg="We are ok"))
