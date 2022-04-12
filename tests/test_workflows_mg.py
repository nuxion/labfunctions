import pytest

from nb_workflows import defaults as df
from nb_workflows.errors.generics import WorkflowRegisterError
from nb_workflows.managers import workflows_mg
from nb_workflows.models import WorkflowModel
from nb_workflows.types import WorkflowData

from .factories import NBTaskFactory, ScheduleDataFactory, WorkflowDataWebFactory

# def test_workflows_mg_create_or_update():
#     wfid = "test"
#     pid = "pid-test"
#     wfd = WorkflowDataWebFactory()
#     stmt = workflows_mg._create_or_update_workflow(wfid, pid, wfd)
#     assert "wfid" in str(stmt)


def test_workflows_mg_generate():
    id_ = workflows_mg.generate_wfid()

    assert isinstance(id_, str)
    assert len(id_) == df.WFID_LEN


def test_workflows_mg_get_job_from_db(session):
    wm = workflows_mg.get_job_from_db(session, "wfid-test")
    assert isinstance(wm, WorkflowModel)
    assert wm.alias == "alias_test"


@pytest.mark.asyncio
async def test_workflows_mg_get_by_wfid(async_session):
    wd = await workflows_mg.get_by_wfid(async_session, "wfid-test")
    assert isinstance(wd, WorkflowData)
    assert wd.alias == "alias_test"


@pytest.mark.asyncio
async def test_workflows_mg_get_by_wfid_prj(async_session):
    wd = await workflows_mg.get_by_wfid_prj(async_session, "test", "wfid-test")
    assert isinstance(wd, WorkflowData)
    assert wd.alias == "alias_test"


@pytest.mark.asyncio
async def test_workflows_mg_get_all(async_session):
    wd_list = await workflows_mg.get_all(async_session, "test")
    assert isinstance(wd_list, list)
    assert wd_list[0].alias == "alias_test"


@pytest.mark.asyncio
async def test_workflows_mg_get_by_alias(async_session):
    wd = await workflows_mg.get_by_alias(async_session, "alias_test")
    assert isinstance(wd, WorkflowModel)
    assert wd.alias == "alias_test"


@pytest.mark.asyncio
async def test_workflows_mg_get_by_alias_none(async_session):
    wd = await workflows_mg.get_by_alias(async_session, "non_exist")
    assert wd is None


@pytest.mark.asyncio
async def test_workflows_mg_register(async_session):
    wfd = WorkflowDataWebFactory()
    wfid = await workflows_mg.register(async_session, "test", wfd)

    wd = await workflows_mg.get_by_wfid(async_session, wfid)

    assert wfid == wd.wfid
    assert wfd.alias == wd.alias


@pytest.mark.asyncio
async def test_workflows_mg_register_update(async_session):
    # wd = await workflows_mg.get_by_wfid_prj(async_session, "test", "wfid-test")

    wfd = WorkflowDataWebFactory(wfid="wfid-test")
    wfd.nbtask.params["daft_punk"] = "alive"

    # wd.nb_name = "test_changed"

    wfd.wfid = "wfid-test"
    # wfd.nbtask.wfid = "wfid-test"

    wfid = await workflows_mg.register(async_session, "test", wfd, update=True)

    wd = await workflows_mg.get_by_wfid(async_session, wfd.wfid)

    assert wfd.alias == wd.alias
    assert wd.nbtask["params"]["daft_punk"] == "alive"


@pytest.mark.asyncio
async def test_workflows_mg_register_conflict(async_session):
    # wd = await workflows_mg.get_by_wfid_prj(async_session, "test", "wfid-test")

    wfd = WorkflowDataWebFactory()
    # this alias already exist
    wfd.alias = "alias_test"

    with pytest.raises(WorkflowRegisterError):
        wfid = await workflows_mg.register(async_session, "test", wfd, update=False)
