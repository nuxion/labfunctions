import os

import pytest
from redislite import Redis
from sqlalchemy.orm import sessionmaker

from nb_workflows.conf import Config
from nb_workflows.db.nosync import AsyncSQL
from nb_workflows.db.sync import SQL
from nb_workflows.workflows.models import HistoryModel, ScheduleModel

SQL_URI = os.getenv("SQLTEST")
ASQL_URI = os.getenv("ASQLTEST")

Session = sessionmaker()


@pytest.fixture(scope="module")
def connection():
    db = SQL(SQL_URI)
    conn = db.engine.connect()

    db.create_all()
    yield conn
    db.drop_all()
    conn.close()


@pytest.fixture(scope="function")
def session(connection):
    transaction = connection.begin()
    _session = Session(bind=connection)
    yield _session

    _session.close()
    transaction.rollback()


@pytest.fixture(scope="module")
async def async_conn():
    adb = AsyncSQL(ASQL_URI)
    await adb.init()
    await adb.create_all()
    yield adb._engine
    await adb.drop_all()


@pytest.fixture(scope="function")
async def async_session(async_conn):
    async with async_conn.begin() as conn:
        yield conn
        await conn.rollback()


@pytest.fixture
async def async_clean_db():
    _db = AsyncSQL(ASQL_URI)
    await _db.init()
    await _db.drop_all()
    await _db.create_all()
    return _db


@pytest.fixture(scope="function")
async def async_db():
    db = AsyncSQL(ASQL_URI)
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
