from contextvars import ContextVar

import aioredis
from redis import Redis
from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize, inject_user, protected

from nb_workflows import auth
from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.db.nosync import AsyncSQL
from nb_workflows.events import EventManager
from nb_workflows.utils import get_version

version = get_version("__version__.py")


def create_db_instance(url=settings.ASQL) -> AsyncSQL:
    return AsyncSQL(url)


def create_web_redis(url=settings.WEB_REDIS):
    return aioredis.from_url(settings.WEB_REDIS, decode_responses=True)


def create_rq_redis(cfg=settings.rq2dict()):
    return Redis(**cfg)


def app_init(
    app_name=defaults.SANIC_APP_NAME,
    db_func=create_db_instance,
    web_redis_func=create_web_redis,
    rq_func=create_rq_redis,
):

    _app = Sanic(app_name)

    Initialize(
        _app,
        authentication_class=auth.NBAuthWeb,
        secret=settings.SECRET_KEY,
        refresh_token_enabled=True,
        add_scopes_to_payload=auth.scope_extender,
        custom_claims=[auth.ProjectClaim],
    )

    _app.config.CORS_ORIGINS = "*"
    Extend(_app)
    _app.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    # _app.ext.openapi.secured()
    _app.ext.openapi.secured("token")

    _base_model_session_ctx = ContextVar("session")

    @_app.listener("before_server_start")
    async def startserver(current_app, loop):
        """This function runs one time per worker"""
        _db = db_func()
        _base_model_session_ctx = ContextVar("session")

        current_app.ctx.web_redis = web_redis_func()
        current_app.ctx.rq_redis = rq_func()
        current_app.ctx.db = _db
        await current_app.ctx.db.init()

    @_app.middleware("request")
    async def inject_session(request):
        current_app = Sanic.get_app(defaults.SANIC_APP_NAME)

        request.ctx.session = current_app.ctx.db.sessionmaker()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
        request.ctx.web_redis = current_app.ctx.web_redis
        request.ctx.events = EventManager(current_app.ctx.web_redis)

        request.ctx.dbconn = current_app.ctx.db.engine

    @_app.middleware("response")
    async def close_session(request, response):
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()

    @_app.listener("after_server_stop")
    async def shutdown(current_app, loop):
        await current_app.ctx.db.engine.dispose()
        # await current_app.ctx.redis.close()

    @_app.get("/status")
    async def status_handler(request):
        return json(dict(msg="We are ok", version=version))

    return _app


app = app_init()
