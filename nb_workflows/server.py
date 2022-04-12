from contextvars import ContextVar
from importlib import import_module
from typing import List

import aioredis
import redis
from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize, inject_user, protected

from nb_workflows import auth, defaults
from nb_workflows.db.nosync import AsyncSQL
from nb_workflows.events import EventManager
from nb_workflows.types import ServerSettings
from nb_workflows.utils import get_version

version = get_version("__version__.py")


def init_blueprints(app, blueprints_allowed):
    """It import and mount each module inside `nb_workflows.web`
    which ends with _bp.

    """
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        module = import_module(f"nb_workflows.web.{mod_name}_bp", mod)
        for el in dir(module):
            if el.endswith("_bp"):
                bp = getattr(module, el)
                blueprints.add(bp)

    for bp in blueprints:
        print("Adding blueprint: ", bp.name)
        app.blueprint(bp)


def create_db_instance(url) -> AsyncSQL:
    return AsyncSQL(url)


def create_web_redis(url):
    return aioredis.from_url(url, decode_responses=True)


def create_rq_redis(url):
    return redis.from_url(url)


def create_app(
    settings: ServerSettings,
    list_bp: List[str],
    app_name=defaults.SANIC_APP_NAME,
    db_func=create_db_instance,
    web_redis_func=create_web_redis,
    rq_func=create_rq_redis,
) -> Sanic:
    """Factory pattern like flask"""

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

    init_blueprints(_app, list_bp)

    @_app.listener("before_server_start")
    async def startserver(current_app, loop):
        """This function runs one time per worker"""
        _db = db_func(settings.ASQL)
        _base_model_session_ctx = ContextVar("session")

        current_app.ctx.web_redis = web_redis_func(settings.WEB_REDIS)
        current_app.ctx.rq_redis = rq_func(settings.RQ_REDIS)
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
