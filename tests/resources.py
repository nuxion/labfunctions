from contextvars import ContextVar
from dataclasses import asdict

from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize

from nb_workflows.client.types import Credentials
from nb_workflows.conf.server_settings import settings
from nb_workflows.events import EventManager
from nb_workflows.managers import users_mg
from nb_workflows.security import auth_from_settings, sanic_init_auth
from nb_workflows.server import init_blueprints
from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowData


def create_app(bluprints, db, web_redis, rq_redis=None, app_name="test"):

    _app = Sanic(app_name)

    init_blueprints(_app, bluprints)

    auth = auth_from_settings(settings.SECURITY)
    sanic_init_auth(_app, auth, settings.SECURITY)
    init_blueprints(_app, ["auth"], "nb_workflows.security")

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

    _app.ctx.db = db
    _app.ctx.rq_redis = rq_redis
    _app.ctx.web_redis = web_redis

    @_app.middleware("request")
    async def inject_session(request):
        current_app = Sanic.get_app(app_name)

        request.ctx.session = current_app.ctx.db.sessionmaker()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
        request.ctx.web_redis = current_app.ctx.web_redis

        request.ctx.events = EventManager(
            current_app.ctx.web_redis,
            block_ms=settings.EVENTS_BLOCK_MS,
            ttl_secs=settings.EVENTS_STREAM_TTL_SECS,
        )

        request.ctx.dbconn = current_app.ctx.db.engine

    @_app.get("/status")
    async def status_handler(request):
        return json(dict(msg="We are ok"))

    return _app
