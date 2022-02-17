import os

import pytest
from dataproc.conf import Config

# from dataproc.content.models import (ContentBucketModel, ContentDocumentModel,
#                                      ContentLabelModel)
from dataproc.crawlers.models import (
    CrawlerBucketModel,
    DataPagesTaskModel,
    DataRootsTaskModel,
    PageModel,
    SiteLabelModel,
    SiteModel,
)
from dataproc.datasets.models import DatasetModel, TableModel, TagModel, datasets_tags
from dataproc.regions.models import Place
from dataproc.social.models import GoogleTrendTask, TweetTrendModel, TweetTrendTask
from dataproc.workflows.models import HistoryModel, ScheduleModel
from db.nosync import AsyncSQL
from db.sync import SQL

SQL_URI = os.getenv("SQLTEST")
ASQL_URI = os.getenv("ASQLTEST")


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
    yield s
    await s.close()


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
