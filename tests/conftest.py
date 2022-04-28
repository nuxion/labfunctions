import asyncio
import os
import tempfile

import aioredis
import pytest
import pytest_asyncio
from redislite import Redis
from sqlalchemy.orm import sessionmaker

# from nb_workflows.auth import (
#     NBAuthStandalone,
#     ProjectClaim,
#     initialize,
#     scope_extender_sync,
# )
from nb_workflows.conf.server_settings import settings
from nb_workflows.db.nosync import AsyncSQL
from nb_workflows.db.sync import SQL
from nb_workflows.models import HistoryModel, UserModel, WorkflowModel
from nb_workflows.security import AuthSpec, auth_from_settings, sanic_init_auth

from .factories import (
    create_history_model,
    create_project_model,
    create_runtime_model,
    create_user_model2,
    create_workflow_model,
)
from .resources import TestTokenStore, create_app

# SQL_URI = os.getenv("SQLTEST")
# ASQL_URI = os.getenv("ASQLTEST")

Session = sessionmaker()

os.environ["NB_WORKFLOW_SERVICE"] = "http://localhost:8000"
pytest_plugins = ("pytest_asyncio",)

secret_auth = "testing"


@pytest.fixture(scope="module")
def connection():
    db = SQL(settings.SQL)
    conn = db.engine.connect()

    db.create_all()
    yield conn
    db.drop_all()
    conn.close()


@pytest.fixture(scope="module", autouse=True)
def setupdb(connection):
    s = Session(bind=connection)
    um = create_user_model2(
        username="admin_test", password="meolvide", salt=settings.SECURITY.AUTH_SALT
    )
    pm = create_project_model(um, projectid="test", name="test")
    wm = create_workflow_model(pm, wfid="wfid-test", alias="alias_test")
    rm = create_runtime_model(pm, project_id="test")
    hm = create_history_model(project_id="test", wfid="wfid-test", execid="exec-test")

    s.add(um)
    s.add(pm)
    s.add(wm)
    s.add(rm)
    s.add(hm)
    s.commit()


@pytest.fixture(scope="function")
def session(connection):
    transaction = connection.begin()
    _session = Session(bind=connection)
    yield _session

    _session.close()
    transaction.rollback()


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_conn():
    adb = AsyncSQL(settings.ASQL)
    await adb.init()
    await adb.create_all()
    yield adb
    await adb.drop_all()


@pytest.fixture(scope="function")
async def async_session(async_conn):
    s = async_conn.sessionmaker()
    # async with s.begin():
    yield s
    await s.rollback()
    # async with async_conn.begin() as conn:
    #    yield conn
    #    await conn.rollback()


@pytest.fixture
async def async_clean_db():
    _db = AsyncSQL(settings.ASQL)
    await _db.init()
    await _db.drop_all()
    await _db.create_all()
    return _db


@pytest.fixture(scope="function")
async def async_db():
    db = AsyncSQL(settings.ASQL)
    await db.init()
    s = db.sessionmaker()
    async with s.begin():
        yield s
    await s.rollback()


@pytest.fixture(scope="module")
def redis():
    rdb = Redis("/tmp/RQ.rdb")
    yield rdb
    try:
        os.remove("/tmp/RQ.rdb")
    except FileNotFoundError:
        pass


@pytest.fixture
def tempdir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
async def sanic_app(async_conn):
    # from nb_workflows.conf.server_settings import settings
    # from nb_workflows.server import app
    # from nb_workflows.utils import init_blueprints

    settings.EVENTS_BLOCK_MS = 5
    settings.EVENTS_STREAM_TTL_SECS = 5

    rweb = aioredis.from_url(settings.WEB_REDIS, decode_responses=True)
    # rweb = Redis("/tmp/RWeb.rdb")

    rqdb = Redis("/tmp/RQWeb.rdb")
    bp = ["workflows", "history", "projects", "events", "runtimes"]
    app = create_app(bp, async_conn, rweb, rqdb)

    yield app
    await app.ctx.web_redis.close()
    await app.asgi_client.aclose()


@pytest.fixture
async def async_redis_web():
    rweb = aioredis.from_url(settings.WEB_REDIS, decode_responses=True)
    await rweb.flushdb()
    yield rweb


@pytest.fixture(scope="session")
def auth_helper():
    store = TestTokenStore()
    auth = auth_from_settings(settings.SECURITY, store=store)
    yield auth


@pytest.fixture
def access_token():
    auth = auth_from_settings(settings.SECURITY)
    encoded = auth.encode({"usr": "admin_test", "scopes": ["user:r:w"]})

    yield encoded
