from contextvars import ContextVar
from dataclasses import asdict
from typing import Optional, Union

from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend

from nb_workflows.client.types import Credentials
from nb_workflows.conf.server_settings import settings
from nb_workflows.events import EventManager
from nb_workflows.hashes import generate_random
from nb_workflows.managers import users_mg
from nb_workflows.security import TokenStoreSpec, auth_from_settings, sanic_init_auth
from nb_workflows.security.redis_tokens import RedisTokenStore
from nb_workflows.server import create_projects_store, init_blueprints
from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowData


class TestTokenStore(TokenStoreSpec):
    def __init__(self):
        self.data = {}

    async def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self.data[key] = value

    async def get(self, key: str) -> Union[str, None]:
        return self.data[key]

    async def delete(self, key: str):
        del self.data[key]

    # @abstractmethod
    # async def validate(self, token: str, user: str) -> bool:
    #     pass

    @staticmethod
    def generate(sign: Optional[str] = None) -> str:
        return generate_random(size=4)


def create_app(bluprints, db, web_redis, rq_redis=None, app_name="test"):

    _app = Sanic(app_name)

    init_blueprints(_app, bluprints)

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

    _store = TestTokenStore()
    auth = auth_from_settings(settings.SECURITY, _store)
    sanic_init_auth(_app, auth, settings.SECURITY)
    init_blueprints(_app, ["auth"], "nb_workflows.security")

    _app.ctx.kv_store = create_projects_store(
        "nb_workflows.io.kv_local.AsyncKVLocal", "nbworkflows"
    )

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

    @_app.middleware("response")
    async def close_session(request, response):
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()

    @_app.get("/status")
    async def status_handler(request):
        return json(dict(msg="We are ok"))

    return _app
