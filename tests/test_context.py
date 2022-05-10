from nb_workflows import context as ctx
from nb_workflows import defaults
from nb_workflows import defaults as df
from nb_workflows.executors.execid import ExecID
from nb_workflows.types import ProjectData, WorkflowDataWeb
from tests import factories

from .factories import NBTaskFactory, ProjectDataFactory, RuntimeDataFactory


def test_context_ExecID():
    id = ExecID()

    docker_id = id.firm_with(ExecID.types.docker)
    str_id = str(id)

    second_sign = id.firm_by_type("machine")

    pure = id.pure()
    assert "." not in pure
    assert str_id == docker_id
    assert docker_id.startswith("dck")
    assert second_sign.startswith("mch.dck.")


# def test_context_execid_build():
#    id = ctx.execid_for_build()
#    assert id.startswith("bld.")


def test_context_dummy_wfid():
    id_ = ctx._dummy_wfid()
    assert len(id_) == defaults.WFID_LEN
    assert id_.startswith("tmp")


def test_context_prepare_runtime():
    rd = RuntimeDataFactory()
    run = ctx.prepare_runtime(rd)
    run2 = ctx.prepare_runtime()
    assert run.endswith(rd.version)
    assert run2.startswith("nuxion")


def test_context_create_nb_ctx_dummy():
    pd = ProjectDataFactory()
    task = NBTaskFactory()
    execid = "test_execid"
    ctx_result = ctx.create_notebook_ctx(pd.projectid, task, execid)
    assert ctx_result.execid == "test_execid"
    assert ctx_result.runtime
    assert ctx_result.params["WFID"]
    assert ctx_result.params["EXECID"] == "test_execid"
    assert ctx_result.machine == defaults.MACHINE_TYPE


# def test_context_dummy_wf_from_nbtask():
#     pd = ProjectDataFactory()
#     task = NBTaskFactory()
#     wd = ctx.dummy_wf_from_nbtask(pd, task)
#     assert isinstance(wd, WorkflowDataWeb)
#
#
# def test_context_create_dummy_ctx():
#     exec_task = ctx.create_dummy_ctx("test", "test_project", execid="0.dummyid")
#     exec_task2 = ctx.create_dummy_ctx("test_2", "test_project")
#     assert exec_task.projectid == "test"
#     assert exec_task2.projectid == "test_2"
#     assert "WFID" in exec_task.params.keys()
#     assert "EXECID" in exec_task.params.keys()
#     assert "NOW" in exec_task.params.keys()
#     assert exec_task.execid == "dummyid"
#
#
# def test_context_create_notebook_ondemand():
#     pd = ProjectDataFactory()
#     task = NBTaskFactory()
#     exec_task = ctx.create_notebook_ctx_ondemand(pd, task)
#     assert exec_task.projectid == pd.projectid
#     assert "WFID" in exec_task.params.keys()
#     assert "EXECID" in exec_task.params.keys()
#     assert "NOW" in exec_task.params.keys()
#
#
# def test_context_make_error():
#     pd = ProjectDataFactory()
#     task = NBTaskFactory()
#     exec_task = ctx.create_notebook_ctx_ondemand(pd, task)
#     res = ctx.make_error_result(exec_task, 10)
#     assert res.error
