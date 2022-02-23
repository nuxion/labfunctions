import os

import pytest
from dataproc.conf import Config
# from dataproc.content.models import (ContentBucketModel, ContentDocumentModel,
#                                      ContentLabelModel)
from dataproc.crawlers.models import (CrawlerBucketModel, DataPagesTaskModel,
                                      DataRootsTaskModel, PageModel,
                                      SiteLabelModel, SiteModel)
from dataproc.datasets.models import (DatasetModel, TableModel, TagModel,
                                      datasets_tags)
from dataproc.regions.models import Place
from dataproc.social.models import (GoogleTrendTask, TweetTrendModel,
                                    TweetTrendTask)
from dataproc.workflows.models import HistoryModel, ScheduleModel
from db.nosync import AsyncSQL
from db.sync import SQL
from redislite import Redis
from sqlalchemy.orm import sessionmaker

# SQL_URI = os.getenv("SQLTEST")
# ASQL_URI = os.getenv("ASQLTEST")
SQL_URI = "postgresql://dataproc_test:testing@localhost:5432/dataproc_test"
ASQL_URI = "postgresql+asyncpg://dataproc_test:testing@localhost:5432/dataproc_test"
# https://github.com/ProvoK/article_agile_database_integration/blob/master/tests/test_user_repo.py

Session = sessionmaker()


@pytest.fixture
def clean_db():
    _db = SQL(SQL_URI)
    _db.drop_all()
    _db.create_all()
    return _db


@pytest.fixture(scope="function")
def db_session():
    sqldb = SQL(SQL_URI)
    Session = sqldb.sessionmaker()
    s = Session()
    yield s
    s.close()


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


@pytest.fixture
def html_document():
    with open(f"{Config.BASE_PATH}/tests/html_document.html", "r") as f:
        data = f.read()
        yield data


@pytest.fixture
def small_corpus_es():
    with open(f"{Config.BASE_PATH}/tests/small_corpus_es.txt") as f:
        data = f.read()
    texts = data.split(".")
    yield texts


@pytest.fixture(scope="module")
def redis():
    rdb = Redis("/tmp/RQ.rdb")
    yield rdb
    try:
        os.remove("/tmp/RQ.rdb")
    except FileNotFoundError:
        pass
