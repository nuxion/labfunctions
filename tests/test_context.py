from nb_workflows import defaults as df
from nb_workflows.executors import context as ctx
from nb_workflows.types import ProjectData, WorkflowDataWeb
from tests import factories

from .factories import NBTaskFactory, ProjectDataFactory


def test_context_ExecID():
    id = ctx.ExecID()
    pure = id.pure()

    from_str = ctx.ExecID.from_str(pure)
    _pure = from_str.pure()

    str_id = str(id)

    assert isinstance(id._id, str)
    assert "." not in pure
    assert "0." in id.signed
    assert _pure == pure
    assert str_id == id._id
    assert isinstance(from_str, ctx.ExecID)


def test_context_generate_execid():
    id_ = ctx.generate_execid()
    assert len(id_) == df.EXECID_LEN
    assert isinstance(id_, str)


def test_context_pure_execid():
    id = ctx.ExecID()
    pure = ctx.pure_execid(id._signed)
    assert "." not in pure
    assert pure == id._id


def test_context_execid_for_build():
    id = ctx.execid_for_build()
    assert str(id).startswith("bld.")


def test_context_docker_name():
    pd = ProjectData(name="test", projectid="testid", owner="tester")
    dn = ctx.generate_docker_name(pd, "1.0")
    assert dn == f"{df.DOCKER_AUTHOR}/test:1.0"


def test_context_dummy_wf_from_nbtask():
    pd = ProjectDataFactory()
    task = NBTaskFactory()
    wd = ctx.dummy_wf_from_nbtask(pd, task)
    assert isinstance(wd, WorkflowDataWeb)


def test_context_create_dummy_ctx():
    exec_task = ctx.create_dummy_ctx("test", "test_project", execid="0.dummyid")
    exec_task2 = ctx.create_dummy_ctx("test_2", "test_project")
    assert exec_task.projectid == "test"
    assert exec_task2.projectid == "test_2"
    assert "WFID" in exec_task.params.keys()
    assert "EXECID" in exec_task.params.keys()
    assert "NOW" in exec_task.params.keys()
    assert exec_task.execid == "dummyid"


def test_context_create_notebook_ondemand():
    pd = ProjectDataFactory()
    task = NBTaskFactory()
    exec_task = ctx.create_notebook_ctx_ondemand(pd, task)
    assert exec_task.projectid == pd.projectid
    assert "WFID" in exec_task.params.keys()
    assert "EXECID" in exec_task.params.keys()
    assert "NOW" in exec_task.params.keys()


def test_context_make_error():
    pd = ProjectDataFactory()
    task = NBTaskFactory()
    exec_task = ctx.create_notebook_ctx_ondemand(pd, task)
    res = ctx.make_error_result(exec_task, 10)
    assert res.error
