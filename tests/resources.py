from contextvars import ContextVar
from dataclasses import asdict

from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_jwt import Initialize

from nb_workflows.auth import authenticate, users
from nb_workflows.conf.server_settings import settings
from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowData

nb_task_simple = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
)

schedule_data = ScheduleData(start_in_min=0, repeat=None, interval="5")

nb_task_schedule = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
    jobid="test_id",
    schedule=schedule_data,
)


wd = WorkflowData(
    jobid="test_id",
    nb_name="test_workflows",
    job_detail=nb_task_schedule.dict(),
    enabled=True,
)

pd = ProjectData(name="test", projectid="asd", username="test")


def app_init(db, web_redis, rq_redis=None, app_name="test"):

    _app = Sanic(app_name)

    Initialize(
        _app,
        authentication_class=authenticate.NBAuthentication,
        secret=settings.SECRET_KEY,
        refresh_token_enabled=True,
        # retrieve_refresh_token=users.retrieve_refresh_token,
        # store_refresh_token=users.store_refresh_token,
        # retrieve_user=users.retrieve_user,
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

    _app.ctx.db = db
    _app.ctx.rq_redis = rq_redis
    _app.ctx.web_redis = web_redis

    @_app.middleware("request")
    async def inject_session(request):
        current_app = Sanic.get_app(app_name)

        request.ctx.session = current_app.ctx.db.sessionmaker()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
        request.ctx.web_redis = current_app.ctx.web_redis

        request.ctx.dbconn = current_app.ctx.db.engine

    @_app.get("/status")
    async def status_handler(request):
        return json(dict(msg="We are ok"))

    return _app
