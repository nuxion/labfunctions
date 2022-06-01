from contextvars import ContextVar
from importlib import import_module
from typing import List

from libq.job_store import RedisJobStore
from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend

from labfunctions import defaults
from labfunctions.control import JobManager, SchedulerExec
from labfunctions.db.nosync import AsyncSQL
from labfunctions.events import EventManager
from labfunctions.io.kvspec import AsyncKVSpec
from labfunctions.redis_conn import create_pool
from labfunctions.security import auth_from_settings, sanic_init_auth
from labfunctions.security.redis_tokens import RedisTokenStore
from labfunctions.types import ServerSettings
from labfunctions.utils import get_class, get_version

version = get_version("__version__.py")


def init_blueprints(app, blueprints_allowed, package_dir="labfunctions.web"):
    """
    It will import bluprints from modules that ends with "_bp" and belongs
    to the package declared in `changeme.defaults.SANIC_BLUPRINTS_DIR`
    by default it will be `changeme.services`
    """
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        modules = import_module(f"{package_dir}.{mod_name}_bp", mod)
        for el in dir(modules):
            if el.endswith("_bp"):
                bp = getattr(modules, el)
                blueprints.add(bp)

    for bp in blueprints:
        print("Adding blueprint: ", bp.name)
        app.blueprint(bp)


def create_db_instance(url) -> AsyncSQL:
    return AsyncSQL(url)


def create_projects_store(
    store_class, store_bucket, base_root="/tmp/labstore"
) -> AsyncKVSpec:
    Class = get_class(store_class)
    return Class(store_bucket, {"root": base_root})


def create_app(
    settings: ServerSettings,
    list_bp: List[str],
    app_name=defaults.SANIC_APP_NAME,
    db_func=create_db_instance,
    create_redis=create_pool,
    projects_store_func=create_projects_store,
    with_auth=True,
    with_auth_bp=True,
) -> Sanic:
    """Factory pattern like flask"""

    app = Sanic(app_name)

    app.config.CORS_ORIGINS = "*"

    Extend(app)
    app.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    # app.ext.openapi.secured()
    app.ext.openapi.secured("token")

    _base_model_session_ctx = ContextVar("session")

    init_blueprints(app, list_bp)

    web_redis = create_redis(settings.WEB_REDIS)
    if with_auth:
        _store = RedisTokenStore(web_redis)
        auth = auth_from_settings(settings.SECURITY, _store)
        sanic_init_auth(app, auth, settings.SECURITY)
    if with_auth and with_auth_bp:
        init_blueprints(app, ["auth"], "labfunctions.security")

    @app.listener("before_server_start")
    async def startserver(current_app, loop):
        """This function runs one time per worker"""
        _db = db_func(settings.ASQL)
        _base_model_session_ctx = ContextVar("session")
        _queue_pool = create_redis(settings.QUEUE_REDIS)

        current_app.ctx.kv_store = projects_store_func(
            settings.PROJECTS_STORE_CLASS_ASYNC, settings.PROJECTS_STORE_BUCKET
        )
        current_app.ctx.web_redis = web_redis.client()
        current_app.ctx.queue_redis = _queue_pool
        current_app.ctx.scheduler = SchedulerExec(
            _queue_pool, control_queue=settings.CONTROL_QUEUE
        )
        current_app.ctx.job_manager = JobManager(conn=_queue_pool)
        current_app.ctx.db = _db
        await current_app.ctx.db.init()

    @app.middleware("request")
    async def inject_session(request):
        current_app = Sanic.get_app(defaults.SANIC_APP_NAME)

        request.ctx.session = current_app.ctx.db.sessionmaker()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
        request.ctx.web_redis = current_app.ctx.web_redis
        request.ctx.events = EventManager(current_app.ctx.web_redis)

        request.ctx.dbconn = current_app.ctx.db.engine

    @app.middleware("response")
    async def close_session(request, response):
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()

    @app.listener("after_server_stop")
    async def shutdown(current_app, loop):
        await current_app.ctx.db.engine.dispose()
        # await current_app.ctx.redis.close()

    @app.get("/status")
    async def status_handler(request):
        return json(dict(msg="We are ok", version=version))

    return app
