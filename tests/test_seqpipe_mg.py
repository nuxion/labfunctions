import pytest

from nb_workflows.managers import seqpipe_mg
from nb_workflows.models import SeqPipeModel

from .factories import SeqPipeFactory


@pytest.mark.asyncio
async def test_seqpipe_mg_create(async_session):
    spf = SeqPipeFactory()

    res = await seqpipe_mg.create(async_session, "test", spf)
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_seqpipe_mg_create_none(async_session):
    spf = SeqPipeFactory()

    res = await seqpipe_mg.create(async_session, "inexistent", spf)
    assert res is None


@pytest.mark.asyncio
async def test_seqpipe_mg_get_one(async_session):
    spf = SeqPipeFactory()

    res = await seqpipe_mg.create(async_session, "test", spf)
    one = await seqpipe_mg.get_one(async_session, "test", res)
    assert isinstance(one, SeqPipeModel)


@pytest.mark.asyncio
async def test_seqpipe_mg_delete(async_session):
    spf = SeqPipeFactory()

    res = await seqpipe_mg.create(async_session, "test", spf)
    await seqpipe_mg.delete_pipe(async_session, "test", res)
    one = await seqpipe_mg.get_one(async_session, "test", res)
    assert one is None


def test_seqpipe_mg_generate(async_session):
    p = seqpipe_mg.generate_pipeid(size=10)
    assert len(p) == 10


def test_seqpipe_mg_create_or_update():
    spf = SeqPipeFactory()
    stmt = seqpipe_mg._create_or_update("test_pid", "test_pipeid", spf)
    assert "insert into" in str(stmt).lower()
